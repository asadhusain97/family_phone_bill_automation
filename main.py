#!/usr/bin/env python3
"""T-Mobile Bill Parser - Local iOS Execution

This script parses T-Mobile PDF bills and outputs a formatted summary table.
Designed for iOS a-Shell execution with Share Sheet integration.

Usage:
    python main.py /path/to/bill.pdf
"""

from analyze_bill_text import main as analyze_bill_text

import sys
import logging
import pandas as pd
from tabulate import tabulate

# Suppress all logging for clean stdout output
logging.disable(logging.CRITICAL)


def print_bill_summary(summary_csv_path: str, bill_month_file: str = "billing_month.txt") -> None:
    """Print formatted bill summary for stdout capture.

    Args:
        summary_csv_path: Path to the summary CSV file
        bill_month_file: Path to the billing month text file
    """
    # Read bill month
    try:
        with open(bill_month_file, "r") as f:
            bill_month = f.read().strip()
            if not bill_month:
                bill_month = "last month"
    except FileNotFoundError:
        bill_month = "last month"

    # Read and format the summary
    df = pd.read_csv(summary_csv_path)

    # Format currency columns
    currency_cols = ["total", "plan_price", "equipment", "services", "one_time_charges"]
    for col in currency_cols:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: f"${x:,.2f}")

    # Select only Member and Total columns for output
    output_df = df[["member", "total"]].copy()
    output_df.columns = ["Member", "Total"]

    # Create formatted table
    table = tabulate(
        output_df,
        headers="keys",
        tablefmt="simple",
        showindex=False,
    )

    # Calculate grand total
    grand_total = df["total"].replace(r"[\$,]", "", regex=True).astype(float).sum()

    # Print clean output (only this will go to stdout)
    print(f"\nT-Mobile Bill Summary for {bill_month}\n")
    print(table)
    print(f"\nGrand Total: ${grand_total:,.2f}")


def main() -> None:
    """Main entry point for bill processing."""

    # Validate arguments
    if len(sys.argv) < 2:
        print("Error: Please provide a PDF file path")
        print("Usage: python main.py /path/to/bill.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]

    try:
        # Process the PDF bill
        analyze_bill_text(pdf_path=pdf_path)

        # Print formatted output
        print_bill_summary("attachments/summary.csv")

    except FileNotFoundError:
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error processing bill: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
