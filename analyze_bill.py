import logging
import yaml
import pandas as pd
from pdf2image import convert_from_path
import pyocr
import pyocr.builders
from PIL import Image

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

def convert_pdf_to_image(pdf_path, page_number):
    """Converts a specific page of a PDF to an image."""
    logging.info(f"Converting page {page_number} of PDF to image")
    try:
        pages = convert_from_path(pdf_path, first_page=page_number, last_page=page_number)
        logging.info("Page converted to image successfully")
        return pages[0] if pages else None
    except Exception as e:
        logging.error(f"Error converting PDF to image: {e}")
        return None

def extract_text_from_image(image):
    """Extracts text from an image using OCR."""
    tool = pyocr.get_available_tools()
    if not tool:
        logging.error("No OCR tool found")
        return None
    
    builder = pyocr.builders.TextBuilder()
    text = tool[0].image_to_string(image, lang="eng", builder=builder)
    
    if text:
        logging.info("Text extracted successfully from image")
    else:
        logging.warning("No text found in image")
    
    return text

def process_text_to_dataframe(text, yaml_data):
    """Processes extracted text into a structured DataFrame."""
    if not text:
        logging.error("No text provided for processing")
        return None
    
    text = "AccountNumber " + text.replace("One-time charges", "One-time-charges")
    rows = text.strip().split('\n')
    data = [row.split() for row in rows]
    
    try:
        df = pd.DataFrame(data[1:], columns=data[0])
        logging.info("Text successfully converted to DataFrame")
    except Exception as e:
        logging.error(f"Error creating DataFrame: {e}")
        return None
    
    def clean_number(num_str):
        if isinstance(num_str, (int, float)):
            return num_str
        elif len(num_str) <= 1:
            return 0
        elif num_str[0] == "-":
            return float(num_str[2:]) * (-1)
        else:
            return float(num_str[1:])
    
    included_plan_total = clean_number(df.loc[1, "Line"])
    included_members = df[df["Plans"] == "Included"].shape[0]
    plan_per_incl_member = round(included_plan_total / included_members, 2)
    
    plan_total = clean_number(df.loc[0, "Line"])
    member_cnt = df.shape[0] - 2
    plan_per_member = round(plan_total / member_cnt, 2)
    
    df["phone_num"] = df["AccountNumber"] + " " + df["Line"]
    df = df[df["phone_num"].str.startswith("(")]
    
    if yaml_data["plan_cost_for_all_members"]:
        df["Plans"] = plan_per_member
    else:
        df["Plans"] = df["Plans"].replace("Included", plan_per_incl_member)
    
    other_cols = ["Plans", "Equipment", "Services", "One-time-charges"]
    for col in other_cols:
        df[col.lower()] = df[col].apply(clean_number)
    
    lower_other_cols = [x.lower() for x in other_cols]
    df["final_amt"] = df[lower_other_cols].sum(axis=1)
    df["member"] = df["phone_num"].map(yaml_data["member_numbers"])
    df = df[["member", "final_amt"]].reset_index(drop=True)
    
    logging.info(f"Total bill sums up to ${df.final_amt.sum():,.2f}")
    return df

def save_dataframe(df, file_path):
    """Saves DataFrame to a CSV file."""
    try:
        df.to_csv(file_path, index=False)
        logging.info(f"DataFrame saved successfully to {file_path}")
    except Exception as e:
        logging.error(f"Error saving DataFrame: {e}")

def analyze_bill():
    yaml_file = 'configs.yml'
    yaml_data = read_yaml_file(yaml_file)
    if not yaml_data:
        return
    
    page_number = 2
    image = convert_pdf_to_image(yaml_data["bill_path"], page_number)
    if not image:
        return
    
    cropped_image = image.crop((0, 240, image.width, 800))
    text = extract_text_from_image(cropped_image)
    
    df = process_text_to_dataframe(text, yaml_data)
    if df is not None:
        save_dataframe(df, file_path=yaml_data["summarized_bill_path"])
        logging.info("Processing completed successfully")

if __name__ == "__main__":
    analyze_bill()
