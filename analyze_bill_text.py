import os
import json
import logging
import yaml
import pandas as pd  # Import pandas first
from pandas.errors import SettingWithCopyWarning
import fitz  # PyMuPDF
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
    """Convert currency strings to floats while handling edge cases.

    Examples:
        get_num_from_str("-$280.83") → -280.83
        get_num_from_str("\$1,234.56") → 1234.56
        get_num_from_str("-") → "-"
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


def get_bill_month(doc, page_number=0):
    """
    Extracts the billing month from the specified page of the PDF document.
    Looks for the text after "Here's your bill for ".

    Args:
        doc: PyMuPDF document object
        page_number: Page number to extract from (default: 0)

    Returns:
        str: Billing month string if found, else None
    """
    page = doc.load_page(page_number)
    text = page.get_text("text")
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


def get_summary_table_from_pdf(path, page_number, family_cnt) -> pd.DataFrame:
    """Extracts and structures the billing summary table from a specific PDF page.

    Processes T-Mobile PDF bills to locate and parse the account summary table containing
    plan charges, equipment fees, and total amounts.

    Args:
        path: Path to PDF file containing phone bill
        page_number: Zero-based page index containing summary table (typically page 1)
        family_cnt: Number of family members in the plan, used to crop the table

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

    Example:
        >>> df = get_summary_table_from_pdf("verizon_bill.pdf", 1)
        >>> df[['cell_nums', 'total']].head()
           cell_nums   total
        0  123-456-7890  $80.00
        1  234-567-8901  $40.00

    Note:
        - Requires exact page structure matching T-Mobile's billing format
        - Logs extraction errors with full traceback for debugging
    """
    try:
        doc = fitz.open(path)
        logging.info(f"Getting summary table from page {page_number} of PDF")

        # Select the page
        get_bill_month(doc, 0)
        page = doc.load_page(page_number)

        # Extract text
        text = page.get_text("text")

        # Split text into lines and process
        lines = text.split("\n")
        data = [line for line in lines if line.strip() != ""]

        # find the start and end of the table
        tbl_start_idx = find_nth_occurrence(data, "Account", 2)
        tbl_end_idx = find_nth_occurrence(data, "DETAILED CHARGES", 1)

        # add a placeholder to make the table and subset
        data.insert(tbl_start_idx + 1, "placeholder")
        tbl_list = data[tbl_start_idx : tbl_end_idx + 1]

        # convert to numpy and reshape
        # check if the table selection is valid
        if len(tbl_list) % (family_cnt+1) != 0:
            logging.error(
                f"Table length {len(tbl_list)} is not divisible by family count {family_cnt}"
            )
            raise ValueError("Invalid table format - inconsistent row count")
        else:
            # Make sure table is ready to be reshaped to have 7 columns
            new_tbl_list = tbl_list.copy()
            num_cols = int(len(tbl_list) / (family_cnt + 1))
            while num_cols < 7:
                new_tbl_list = add_elements_in_list(new_tbl_list, num_cols, ["-"]*(family_cnt + 1))
                num_cols = int(len(new_tbl_list) / (family_cnt + 1))

        tbl_arr = np.array(new_tbl_list).reshape(11, 7)

        # get the raw table
        raw_df = pd.DataFrame(
            tbl_arr,
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
        logging.info("Summary table successfully extracted from PDF")
        return raw_df
    except Exception as e:
        logging.error(f"Error extracting summary table from PDF: {e}")
        return None


def add_elements_in_list(data, group_size, new_elements):
    n = len(data) // group_size
    result = []
    for i in range(n):
        group = data[i * group_size : (i + 1) * group_size]
        insert_index = len(group) - 1  # second-last index
        group.insert(insert_index, new_elements[i])
        result.append(group)
    return list(np.array(result).flatten())


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
    doc = fitz.open(path)

    # Select the page
    page = doc.load_page(page_number)

    # Extract text
    text = page.get_text("text")

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
