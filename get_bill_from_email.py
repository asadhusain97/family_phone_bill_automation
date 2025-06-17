import os
import imaplib
import email
from email import policy
from email.header import decode_header
import logging
import yaml
import pandas as pd

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Create a folder to save attachments
ATTACHMENT_DIR = "attachments"
if not os.path.exists(ATTACHMENT_DIR):
    os.makedirs(ATTACHMENT_DIR)

USER = os.environ.get("USER")
PASSWORD = os.environ.get("GAPP_PASSWORD")
TRIGGER_MAIL_SENDER = os.environ.get("TRIGGER_MAIL_SENDER")


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


def connect_to_mailbox(yaml_data, user=USER, password=PASSWORD):
    logging.info("Connecting to Gmail's IMAP server...")
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(USER, PASSWORD)
    mail.select("inbox")
    logging.info("Logged in!")
    return mail


def search_emails(mail, subject, lookback_days):
    today = pd.Timestamp("today")
    since_date = (today - pd.Timedelta(days=lookback_days)).strftime("%d-%b-%Y")
    logging.info(f"Searching for emails since {since_date}...")
    status, messages = mail.search(None, f'SINCE {since_date}')
    if status != "OK":
        logging.warning("No emails found matching the criteria.")
        return []
    email_ids = messages[0].split()
    matched_ids = []
    for eid in email_ids:
        status, msg_data = mail.fetch(eid, "(BODY.PEEK[HEADER.FIELDS (SUBJECT)])")
        if status == "OK":
            msg = email.message_from_bytes(msg_data[0][1])
            subj = msg.get("Subject", "")
            if subject.lower() in subj.lower():
                matched_ids.append(eid)
    return matched_ids


def save_attachment(part, directory):
    filename = part.get_filename()
    if filename:
        filepath = os.path.join(directory, filename)
        with open(filepath, "wb") as f:
            f.write(part.get_payload(decode=True))
        logging.info(f"Attachment saved: {filepath}")


def fetch_and_process_email(mail, email_id):
    status, msg_data = mail.fetch(email_id, "(RFC822)")
    for response_part in msg_data:
        if isinstance(response_part, tuple):
            msg = email.message_from_bytes(response_part[1], policy=policy.default)
            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding if encoding else "utf-8")

            for part in msg.walk():
                if part.get_content_disposition() == "attachment":
                    filename = part.get_filename()
                    if filename:
                        new_filename = "tmobile_bill.pdf"
                        filepath = os.path.join(ATTACHMENT_DIR, new_filename)
                        with open(filepath, "wb") as f:
                            f.write(part.get_payload(decode=True))
                        logging.info(f"Attachment saved: {filepath}")


def main():
    yaml_file = "configs.yml"
    yaml_data = read_yaml_file(yaml_file)
    if not yaml_data:
        return

    try:
        mail = connect_to_mailbox(yaml_data)

        email_ids = search_emails(
            mail, yaml_data["subject"], yaml_data["lookback_days"]
        )
        if email_ids:
            logging.info(
                f"Found {len(email_ids)} matching email(s). Fetching the latest one..."
            )
            fetch_and_process_email(mail, email_ids[-1])
            logging.info("Logging out and closing the connection.")
            mail.logout()
            return True
        else:
            logging.info("No emails matched the search criteria.")
            logging.info("Logging out and closing the connection.")
            mail.logout()
            return False

    except Exception as e:
        logging.error(f"Error: {e}")


if __name__ == "__main__":
    main()
