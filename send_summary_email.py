import smtplib
import logging
import yaml
import pandas as pd
from email.message import EmailMessage
import os
import json
from datetime import datetime
from tabulate import tabulate

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

USER = os.environ.get("USER")
PASSWORD = os.environ.get("GAPP_PASSWORD")
RECIPIENT_EMAIL = os.environ.get("SUMMARY_EMAIL_RECIPIENT")


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


def read_summary_file(file_path):
    """Formats billing summary CSV into a visually appealing email-ready string.

    Args:
        file_path: Path to CSV from analyze_bill_text.process_text_to_dataframe()

    Returns:
        str: Formatted table with borders and aligned columns
    """
    try:
        # Read and preprocess data
        df = pd.read_csv(file_path)
        if df.empty:
            return "Error: Empty billing summary file"

        # Format currency columns
        currency_cols = [
            "total",
            "plan_price",
            "equipment",
            "services",
            "one_time_charges",
        ]
        for col in currency_cols:
            df[col] = df[col].apply(lambda x: f"${x:,.2f}")

        # Rename columns for better display
        df = df.rename(
            columns={
                "member": "Member",
                "total": "Total",
                "plan_price": "Plan Cost",
                "equipment": "Equipment",
                "services": "Services",
                "one_time_charges": "One-Time Charges",
            }
        )

        # Create formatted table
        table = tabulate(
            df,
            headers="keys",
            tablefmt="plain",
            stralign="left",
            numalign="right",
            showindex=True,
            maxcolwidths=[25, 15, 15, 15, 15, 15],
        )

        # Add total summary
        grand_total = df["Total"].replace("[\$,]", "", regex=True).astype(float).sum()
        total_row = f"\n{'Grand Total':<15} ${grand_total:,.2f}"

        return f"```\n{table}\n{total_row}\n```"

    except Exception as e:
        # logging.error(f"Error formatting billing summary: {e}", exc_info=True)
        return "Error generating billing summary"


def send_email(sender_email, sender_password, recipient_emails, subject, body):
    """Sends an email with the CSV content in the body."""

    logging.info("Setting up the email message")

    msg = EmailMessage()
    msg["From"] = sender_email
    msg["Subject"] = subject
    msg.set_content(body)

    # Split the recipient_emails string by comma and add each email to the 'To' field
    recipient_list = [email.strip() for email in recipient_emails.split(",")]
    msg["To"] = ", ".join(recipient_list)

    try:
        logging.info("Connecting to email server")
        with smtplib.SMTP_SSL(
            "smtp.gmail.com", 465
        ) as server:  # Use your email provider's SMTP settings
            server.login(sender_email, sender_password)
            logging.info("Logged into email server")
            server.send_message(msg)
            logging.info("Email sent successfully")
    except Exception as e:
        logging.error(f"Error sending email: {e}")


def delete_all_files_in_folder(folder_path):
    # Check if the folder exists
    if not os.path.exists(folder_path):
        logging.ERROR(f"The folder {folder_path} does not exist.")
        return

    # Loop through all files in the folder
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        # Check if it's a file (not a folder) and delete it
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
                logging.info(f"Deleted: {file_path}")
            except Exception as e:
                logging.ERROR(f"Error deleting {file_path}: {e}")
        else:
            logging.info(f"Skipped (not a file): {file_path}")


def send_summary_email(user=USER, password=PASSWORD, recipient_email=RECIPIENT_EMAIL):
    """Sends a formatted summary mail to the recipient."""
    yaml_file = "configs.yml"
    yaml_data = read_yaml_file(yaml_file)
    if not yaml_data:
        return

    csv_content = read_summary_file(yaml_data["summarized_bill_path"])

    summary_body = f"""
        Here is how much each member of the family owes for last months' 
        T-Mobile bill:
        \n\n{csv_content}\n\n
        Have a good day beautiful!
        """

    send_email(
        user, password, recipient_email, yaml_data["summary_subject"], summary_body
    )
    if yaml_data["delete_attachments"]:
        delete_all_files_in_folder("attachments/")


if __name__ == "__main__":
    send_summary_email()
