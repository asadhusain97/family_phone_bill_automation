# this script gets the latest tmobile bill from your gmail, analyses and send you an email with a summary.

from get_bill_from_email import main as get_bill_from_email
from analyze_bill_text import main as analyze_bill_text
from send_summary_email import main as send_summary_email

import logging
from typing import Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def main() -> None:
    """Main workflow to process phone bill from email to analysis."""
    try:
        # Get bill content
        logging.info("Searching for latest bill email")
        bill_found: Optional[str] = get_bill_from_email()

        if not bill_found:
            logging.warning("No bill email found")
            return

        # Analyze bill
        logging.info("Analyzing bill content")
        analyze_bill_text()

        # Send summary
        logging.info("Sending summary email")
        send_summary_email()

    except Exception as e:
        logging.error(f"Error processing bill: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
