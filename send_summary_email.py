import smtplib
import logging
import yaml
import pandas as pd
from email.message import EmailMessage
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

USER = os.environ.get("USER")
PASSWORD = os.environ.get("GAPP_PASSWORD")
RECIPIENT_EMAIL = os.environ.get("SUMMARY_EMAIL_RECIPIENT")

def read_yaml_file(file_path):
    """Reads and parses a YAML file."""
    logging.info(f"Reading YAML file from {file_path}")
    try:
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)
            logging.info("YAML file read successfully")
            return data
    except (yaml.YAMLError, FileNotFoundError) as e:
        logging.error(f"Error reading YAML file: {e}")
        return None

def read_summary_file(file_path):
    """Reads a CSV file and returns its content as a formatted string."""
    try:
        df = pd.read_csv(file_path)
        total_bill = df["final_amt"].sum()
        df["final_amt"] = df["final_amt"].apply(lambda x: f"${x:,.2f}")
        df.rename(columns={"final_amt": "Amount", "member": "Member"}, inplace=True)
        max_key_length = max(df[df.columns[0]].astype(str).apply(len))
        max_value_length = 6
        middle_dots = 10
        total_width = max_key_length + max_value_length + middle_dots + 7  # Adjust spacing for dots
        
        # Formatting table with dotted lines, ensuring right alignment for second column
        formatted_table = "\n".join(
            [f"{row[0].ljust(max_key_length, '.')}{'.' * middle_dots}{row[1]}" for row in df.values]
        )
        header = f"{'-' * total_width}\n{df.columns[0].ljust(max_key_length, '.')}{'.' * middle_dots}{df.columns[1]}\n{'-' * total_width}"
        footer = f"{'Total bill'.ljust(max_key_length, '.')}{'.' * middle_dots}{f'${total_bill:,.2f}'}\n{'-' * total_width}"
        return f"{header}\n{formatted_table}\n{'-' * total_width}\n{footer}"
    except Exception as e:
        logging.error(f"Error reading CSV file: {e}")
        return "Error reading CSV file."

def send_email(sender_email, sender_password, recipient_email, subject, body):
    """Sends an email with the CSV content in the body."""
    logging.info("Setting up the email message")
    
    msg = EmailMessage()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.set_content(body)
    
    try:
        logging.info("Connecting to email server")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:  # Use your email provider's SMTP settings
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


def send_summary_email(user = USER, password = PASSWORD, recipient_email = RECIPIENT_EMAIL):
    """Sends a formatted summary mail to the recipient."""
    yaml_file = 'configs.yml'
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

    send_email(user, password, recipient_email, yaml_data["summary_subject"], summary_body)
    if yaml_data["delete_attachments"]: 
        delete_all_files_in_folder("attachments/")

if __name__ == "__main__":
    send_summary_email()
