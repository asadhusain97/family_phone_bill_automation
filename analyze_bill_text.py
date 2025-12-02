import os
import json
import logging
import yaml
import pandas as pd  # Import pandas first
from pandas.errors import SettingWithCopyWarning
from pypdf import PdfReader  # Pure Python PDF library (iOS a-Shell compatible)
import numpy as np
import re
import warnings

warnings.filterwarnings("ignore", category=SyntaxWarning)
warnings.filterwarnings("ignore", category=SettingWithCopyWarning)


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

MEMBER_NAMES = os.environ.get("MEMBER_NAMES")


def read_yaml_file(file_path):
    """Reads and parses a YAML file."""
    logging.info(f"Reading YAML file from {file_path}")
    try:
        with open(file_path, "r") as file:
            data = yaml.safe_load(file)
            logging.info("YAML file read successfully")
            return data
    except (yaml.YAMLError, FileNotFoundError) as e:
        logging.error(f"Error reading YAML file: {e}")
        return None


def find_nth_occurrence(strings: list, target: str, n: int = 1) -> int:
    """Return index of nth occurrence of target string in strings list.

    Args:
        strings: List of strings to search
        target: String to find
        n: Occurrence number (1-based)

    Returns:
        Index of nth occurrence or -1 if not found

    Example:
        >>> find_nth_occurrence(["a", "b", "a", "c", "a"], "a", 3)
        4
    """
    count = 0
    for i, s in enumerate(strings):
        if s == target:
            count += 1
            if count == n:
                return i
    return -1


def get_num_from_str(s: str) -> float:
    r"""Convert currency strings to floats while handling edge cases.

    Examples:
        get_num_from_str("-$280.83") → -280.83
        get_num_from_str("$1,234.56") → 1234.56
        get_num_from_str("-") → 0.0
    """
    match = re.search(r"[-+]?\$?\d{1,4}(?:,\d{3})*(\.\d+)?", str(s))

    if s == "-":
        return 0.0

    if not match:
        return s

    try:
        # Remove non-numeric chars except . and -
        cleaned = re.sub(r"[^\d.-]", "", match.group(0))
        return float(cleaned)
    except (ValueError, TypeError):
        return s


def get_bill_month(reader, page_number=0):
    """
    Extracts the billing month from the specified page of the PDF document.
    Looks for the text after "Here's your bill for ".

    Args:
        reader: pypdf PdfReader object
        page_number: Page number to extract from (default: 0)

    Returns:
        str: Billing month string if found, else None
    """
    page = reader.pages[page_number]
    text = page.extract_text()
    match = re.search(r"Here's your bill for\s+([^\n]+)", text)
    if match:
        bill_month = match.group(1).strip()[:-1]  # Remove trailing period and spaces
        # save month name to a txt file
        with open("billing_month.txt", "w") as f:
            f.write(bill_month)
        logging.info(f"Billing month extracted: {bill_month}")
    else:
        logging.error("Billing month not found in the document")
        return None


def parse_table_row(row):
    """Parse a single table row from pypdf extracted text.

    Args:
        row: Single line string from the bill summary table

    Returns:
        list: Parsed row with 7 elements [cell_nums, line_type, plans, equipment, services, one_time, total]
        None if parsing fails
    """
    if row.startswith('Account'):
        # Account row: "Account $280.00 - $0.00 - $280.00"
        parts = row.split()
        if len(parts) >= 6:
            return ['Account', '', parts[1], parts[2], parts[3], parts[4], parts[5]]
    else:
        # Member row: "(999) 637-3009 Voice Included - - $0.53 $0.53"
        # Extract phone number and parse rest
        match = re.match(r'\((\d+)\)\s*(\d+)-(\d+)\s+Voice\s+(.+)', row)
        if match:
            phone = f"({match.group(1)}) {match.group(2)}-{match.group(3)}"
            rest = match.group(4).strip()

            # Parse remaining fields: Plans Equipment Services One-time Total
            tokens = rest.split()
            if len(tokens) >= 5:
                return [phone, 'Voice'] + tokens
    return None


def get_summary_table_from_pdf(path, page_number, family_cnt) -> pd.DataFrame:
    """Extracts and structures the billing summary table from a specific PDF page.

    Processes T-Mobile PDF bills to locate and parse the account summary table containing
    plan charges, equipment fees, and total amounts.

    Args:
        path: Path to PDF file containing phone bill
        page_number: Zero-based page index containing summary table (typically page 1)
        family_cnt: Number of family members in the plan, used to validate table

    Returns:
        pd.DataFrame: Structured table with columns:
            - cell_nums: Phone numbers/device identifiers
            - line_type: Voice
            - plans: Monthly plan charges
            - equipment: Device payment plans
            - services: Add-on services
            - one_time_charges: Non-recurring fees
            - total: Line item total
        Returns None if extraction fails

    Note:
        - Requires exact page structure matching T-Mobile's billing format
        - Logs extraction errors with full traceback for debugging
        - Uses pypdf for pure Python PDF parsing (iOS a-Shell compatible)
    """
    try:
        reader = PdfReader(path)
        logging.info(f"Getting summary table from page {page_number} of PDF")

        # Extract billing month from first page
        get_bill_month(reader, 0)

        # Select the page for table extraction
        page = reader.pages[page_number]

        # Extract text
        text = page.extract_text()

        # Split text into lines and process
        lines = text.split("\n")
        data = [line.strip() for line in lines if line.strip() != ""]

        # Find the table boundaries
        # Table starts after "THIS BILL SUMMARY" header line
        # Table ends at "DETAILED CHARGES"
        try:
            summary_idx = data.index("THIS BILL SUMMARY")
            detailed_idx = data.index("DETAILED CHARGES")
        except ValueError as e:
            logging.error(f"Could not find table boundaries: {e}")
            return None

        # Extract table rows (skip header row with column names)
        table_lines = data[summary_idx + 2 : detailed_idx]  # +2 to skip header row

        # Parse each row
        parsed_rows = []
        for line in table_lines:
            if line.startswith('T otals'):  # Skip totals row
                continue
            parsed = parse_table_row(line)
            if parsed:
                parsed_rows.append(parsed)

        # Validate we got the expected number of rows
        expected_rows = family_cnt + 1  # family members + Account row
        if len(parsed_rows) != expected_rows:
            logging.warning(
                f"Expected {expected_rows} rows but got {len(parsed_rows)}. "
                f"Check family_count config setting."
            )

        # Create DataFrame
        raw_df = pd.DataFrame(
            parsed_rows,
            columns=[
                "cell_nums",
                "line_type",
                "plans",
                "equipment",
                "services",
                "one_time_charges",
                "total",
            ],
        )

        logging.info(f"Summary table successfully extracted from PDF ({len(parsed_rows)} rows)")
        return raw_df

    except Exception as e:
        logging.error(f"Error extracting summary table from PDF: {e}", exc_info=True)
        return None


def process_text_to_dataframe(df, plan_cost_for_all_members):
    """Processes raw billing table into member-specific charges with cost allocation.

    Performs currency conversion, plan cost distribution, and member mapping based on
    configuration settings. Handles two billing strategies:
    1. Split plan costs equally among all members
    2. Charge included members shared cost and others individual plans

    Args:
        df: Raw DataFrame from get_summary_table_from_pdf()
        plan_cost_for_all_members: Boolean config flag from YAML

    Returns:
        pd.DataFrame: Finalized bill with columns ['member', 'total']
            - member: Phone number or mapped name
            - total: Calculated amount owed
            - plan_price: Plan cost per member
            - equipment: Equipment cost
            - services: Services cost
            - one_time_charges: One-time charges

    Raises:
        ValueError: If input table structure is invalid
    """
    if df is None:
        logging.error("No table provided for processing")
        return None

    try:
        # fix all numbers
        currency_cols = ["plans", "equipment", "services", "one_time_charges", "total"]
        for col in currency_cols:
            df[col] = df[col].apply(get_num_from_str)
        df["cell_nums"] = df["cell_nums"].apply(lambda x: x.replace("\xa0", " "))

        if "Account" not in df["cell_nums"].values:
            logging.error("Missing 'Account' row in input table")
            raise ValueError("Invalid table format - no account summary row")

        # fix plans
        included_members = df[df["plans"] == "Included"].shape[0]
        plan_price_for_members = df.loc[df["cell_nums"] == "Account", "plans"].iloc[0]
        df = df[df["cell_nums"] != "Account"]
        plan_price_for_others = df.loc[df["plans"] != "Included", "plans"].sum()
        other_members = df.loc[df["plans"] != "Included", "plans"].shape[0]
        if plan_cost_for_all_members:
            # get the total plan cost
            total_plan_price = plan_price_for_members + plan_price_for_others
            total_members = included_members + other_members
            total_plan_price = total_plan_price / total_members

            # set this plan price for all members
            df["plan_price"] = total_plan_price
        else:  # included members pay different than other members
            df["plan_price"] = np.where(
                df["plans"] == "Included",
                plan_price_for_members / included_members,
                df["plans"],
            )

        df = df[
            ["cell_nums", "plan_price", "equipment", "services", "one_time_charges"]
        ]
        df["total"] = df[
            ["plan_price", "equipment", "services", "one_time_charges"]
        ].sum(axis=1)

        # map names to numbers for better visibility
        if MEMBER_NAMES is not None:
            df["member"] = df["cell_nums"].replace(json.loads(MEMBER_NAMES))
        else:
            df["member"] = df["cell_nums"]
        df = df[
            [
                "member",
                "total",
                "plan_price",
                "equipment",
                "services",
                "one_time_charges",
            ]
        ].reset_index(drop=True)

        logging.info(f"Total bill sums up to ${df.total.sum():,.2f}")
        return df
    except KeyError as e:
        logging.error(f"Missing required column: {e}")
        raise ValueError(f"Invalid table structure - {e} not found") from e
    except IndexError as e:
        logging.error("Account row not found in plans column")
        raise ValueError("Invalid table format - account plan price missing") from e


def get_total_from_bill(path, page_number=0):
    """Extract the total due amount from the PDF bill.

    Args:
        path: Path to PDF file
        page_number: Page number to extract from (default: 0)

    Returns:
        float: Total bill amount
    """
    reader = PdfReader(path)

    # Select the page
    page = reader.pages[page_number]

    # Extract text
    text = page.extract_text()

    # Split text into lines and process
    lines = text.split("\n")
    data = [line for line in lines if line.strip() != ""]
    total_idx = find_nth_occurrence(data, "TOTAL DUE", 1)
    return get_num_from_str(data[total_idx + 1])


def save_dataframe(df, file_path):
    """Saves DataFrame to a CSV file."""
    try:
        df.to_csv(file_path, index=False)
        logging.info(f"DataFrame saved successfully to {file_path}")
    except Exception as e:
        logging.error(f"Error saving DataFrame: {e}")


def main(pdf_path=None):
    """Main function to analyze bill text.

    Args:
        pdf_path: Optional path to PDF file. If provided, uses this instead of config path.
                  This enables local mode execution (e.g., iOS a-Shell).
    """
    yaml_file = "configs.yml"
    yaml_data = read_yaml_file(yaml_file)
    if not yaml_data:
        return

    # Use provided PDF path (local mode) or config path (cloud mode)
    bill_path = pdf_path if pdf_path else yaml_data["bill_path"]
    logging.info(f"Processing bill from: {bill_path}")

    # read the table from the pdf
    raw_df = get_summary_table_from_pdf(
        bill_path, yaml_data["page_number"], yaml_data["family_count"]
    )

    # process the table
    df = process_text_to_dataframe(raw_df, yaml_data["plan_cost_for_all_members"])

    # check if the processing was fine
    total_bill_raw = get_total_from_bill(bill_path)
    total_bill_processed = float(df.total.sum())
    assert (
        abs(total_bill_processed - total_bill_raw) < 10**-6
    ), f"Total bill does not match: {total_bill_processed} != {total_bill_raw}"

    save_dataframe(df, file_path=yaml_data["summarized_bill_path"])
    logging.info("Processing completed successfully")


if __name__ == "__main__":
    main()
