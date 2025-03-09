# this script gets the latest tmobile bill from your gmail, analyses and send you an email with a summary.

from get_bill_from_email import get_bill_from_email
from analyze_bill import analyze_bill
from send_summary_email import send_summary_email

import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def main():
    logging.info("Getting the bill...")
    mail_found = get_bill_from_email()
    if mail_found:
        logging.info("Bill analysis started...")
        analyze_bill()
        logging.info("Sending you the summary..")
        send_summary_email()
        logging.info("Done!")
    else:
        logging.warning("Skipping the other steps.")

if __name__ == "__main__":
    main()