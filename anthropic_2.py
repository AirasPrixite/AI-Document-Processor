import os
import anthropic
import PyPDF2
import io
import pandas as pd
from anthropic import Anthropic
from tqdm import tqdm

def extract_text_from_pdf_page(pdf_reader, page_num):
    """Extract text from a specific page of the PDF."""
    try:
        page = pdf_reader.pages[page_num]
        return page.extract_text()
    except Exception as e:
        print(f"Error extracting text from page {page_num + 1}: {str(e)}")
        return ""

def process_page_with_claude(client, page_text, page_num):
    """Process a single page with Claude API."""
    prompt = f"""
    Extract the table information from the following text (Page {page_num + 1}).
    The table should have these headers:
    PRODUCT, LEGACY PRODUCT, DESCRIPTION, UPC, QTY ORD, QTY, PRICE, UNIT ALLOW, NET PRICE, EXT US($)

    Critical instructions for UPC extraction:
    1. UPC values are EXACTLY twelve (12) digits long
    2. UPC values may be split across multiple lines in the text
    3. Ensure all UPC digits are captured and combined into a single 12-digit number
    4. Do NOT include any digits from adjacent columns (like QTY ORD or QTY) in the UPC
    5. Always verify that each UPC value contains exactly 12 digits

    Example of correct UPC extraction:
    If you see:
    123456789012    2    3
    The UPC should be: 123456789012 (not including the 2 or 3)
you see:
    123456789
    012
    This should be combined into: 123456789012

    Please format the output as a CSV with the exact headers specified above.
    If no table is found on this page, respond with 'NO_TABLE_FOUND'.

    Here's the text:
    {page_text}
   """
    try:
        message = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=4000,
            temperature=0,
            messages=[                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        response = message.content[0].text
        if 'NO_TABLE_FOUND' in response:
            return None
        df = pd.read_csv(io.StringIO(response))
        # Ensure UPC is treated as string and padded to 12 digits
        if 'UPC' in df.columns:
            df['UPC'] = df['UPC'].astype(str).apply(lambda x: ''.join(filter(str.isdigit, x))).str.zfill(12)
        return df
    except Exception as e:
        print(f"Error processing page {page_num + 1} with Claude: {str(e)}")
        return None

def process_reg_san_excel(excel_file, sheet_name, output_csv="reg_san.csv"):
    df = pd.read_excel(excel_file, sheet_name=sheet_name, skiprows=6)  # Skip first 4 rows
    df.to_csv(output_csv, index=False)
    return output_csv


def find_header_row(df):
    for i, row in df.iterrows():
        if "UPC" in row.values:
            return i
    return None

def validate_upc_values(df):
    """Validate and report on UPC values."""
    if 'UPC' not in df.columns:
        print("No UPC column found in the extracted data.")
        return df
    # Convert UPC to string and remove any non-digit characters
    df['UPC'] = df['UPC'].astype(str).apply(lambda x: ''.join(filter(str.isdigit, x)))
    # Pad UPCs with leading zeros if necessary
    df['UPC'] = df['UPC'].str.zfill(12)
    # Report on UPC lengths
    upc_lengths = df['UPC'].str.len().value_counts().sort_index()
    print("\nUPC Length Distribution:")
    for length, count in upc_lengths.items():
        print(f"UPC length {length}: {count} entries")
    # Flag incorrect length UPCs
    incorrect_upcs = df[df['UPC'].str.len() != 12]['UPC'].tolist()
    if incorrect_upcs:
        print("\nWarning: Found UPC values that are not 12 digits:")
        for upc in incorrect_upcs[:5]:  # Show first 5 examples
            print(f"- {upc}")
        if len(incorrect_upcs) > 5:
            print(f"... and {len(incorrect_upcs) - 5} more")
    return df

def extract_tables_from_pdf(pdf_path, api_key):
    client = Anthropic(api_key=api_key)
    all_tables = []
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            print(f"Processing {num_pages} pages...")
            for page_num in tqdm(range(num_pages), desc="Extracting tables"):
                page_text = extract_text_from_pdf_page(pdf_reader, page_num)
                if not page_text.strip():
                    continue
                df = process_page_with_claude(client, page_text, page_num)
                if df is not None and not df.empty:
                    df['Page_Number'] = page_num + 1
                    all_tables.append(df)
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
    if not all_tables:
        return None
    final_df = pd.concat(all_tables, ignore_index=True)
    return final_df

def save_to_csv(df, output_path):
    try:
        df.to_csv(output_path, index=False)
        return True
    except Exception as e:
        print(f"Error saving CSV file: {str(e)}")
        return False