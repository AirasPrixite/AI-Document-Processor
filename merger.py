import streamlit as st
import os
import pandas as pd
import io
import PyPDF2
import re
from anthropic_2 import extract_tables_from_pdf, validate_upc_values, process_reg_san_excel

# API Key (Replace with your actual key)
api_key = ""

# Temporary directory for CSV files
TEMP_DIR = "temp"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

def extract_text_from_pdf(pdf_file):
    """Extract text from a multi-page PDF."""
    all_text = []
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text = page.extract_text()
            if text:
                all_text.append(text)
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
    return "\n".join(all_text)

def extract_table_data(text):
    """Extract table data from the provided text."""
    pattern = re.compile(
        r'(?P<Item>\d+)\s+(?P<Internal>\d+)(?:\s+(?P<CodVend>\d+))?\s+(?P<Description>.+?)\s+(?P<Quantity>\d+\.\d{2})\s+(?P<UM>\w+)\s+(?P<UnitPrice>\d+\.\d{2})\s+(?P<NetAmount>\d+\.\d{2})'
    )
    
    data = []
    
    for line in text.split('\n'):
        line = line.strip()
        if line:
            match = pattern.search(line)
            if match:
                data.append([
                    match.group('Item'),
                    match.group('Internal'),
                    match.group('CodVend') or "",
                    match.group('Description').strip(),
                    match.group('Quantity'),
                    match.group('UM'),
                    match.group('UnitPrice'),
                    match.group('NetAmount')
                ])

    return pd.DataFrame(data, columns=["Item", "Internal", "Cod/Cod Vend", "Description", "Quantity", "UM", "Unit Price", "Net Amount"])

def merging_logic(invoice_df, reg_san_df):
    invoice_df['UPC'] = invoice_df['UPC'].astype(str)
    reg_san_df['UPC'] = reg_san_df['UPC'].astype(str)
    merged_df = invoice_df.merge(reg_san_df, on='UPC', how='left')
    selected_columns = ['PRODUCT', 'DESCRIPTION', 'País de Orígen', 'QTY', 'NET PRICE', 'EXT US($)', 'Reg. San. / Compr. No.']
    new_df = merged_df[selected_columns].copy()
    renamed_df = new_df.rename(columns={'País de Orígen': 'ORIGIN', 'QTY': 'QTY SHIPPED', 'Reg. San. / Compr. No.': 'REG. SAN'})
    return merged_df, renamed_df

def process_invoice_purchase_order(): 
    df_invoice = pd.read_csv(os.path.join(TEMP_DIR, 'invoice.csv'))
    df_purchase_order = pd.read_csv(os.path.join(TEMP_DIR, 'purchase_order.csv'))
    df_merged_po_invoice = df_purchase_order.merge(df_invoice, left_on='Cod/Cod Vend', right_on='UPC', how='left')
    df_merged_po_invoice['Quantity_difference'] = df_merged_po_invoice['QTY ORD'] - df_merged_po_invoice['Quantity']
    df_merged_po_invoice['Price_difference'] = df_merged_po_invoice['PRICE'] - df_merged_po_invoice['Unit Price']
    return df_merged_po_invoice

def main():
    st.title("Invoice PDF Processor")

    # Initialize session states for data
    if 'final_df' not in st.session_state:
        st.session_state.final_df = None
    if 'reg_san_data' not in st.session_state:
        st.session_state.reg_san_data = None
    if 'purchase_order_data' not in st.session_state:
        st.session_state.purchase_order_data = None

    # File uploader for Invoice PDF
    uploaded_invoice = st.file_uploader("Upload Invoice PDF", type="pdf")

    if uploaded_invoice is not None:
        st.write(f"Uploaded Invoice file: {uploaded_invoice.name}")
        temp_invoice_path = os.path.join(TEMP_DIR, uploaded_invoice.name)
        with open(temp_invoice_path, "wb") as temp_file:
            temp_file.write(uploaded_invoice.getbuffer())

        if st.button("Process Invoice"):
            try:
                final_df = extract_tables_from_pdf(temp_invoice_path, api_key)
                if final_df is not None:
                    final_df = validate_upc_values(final_df)
                    final_df.to_csv(os.path.join(TEMP_DIR, 'invoice.csv'), index=False)
                    st.session_state.final_df = final_df

                    st.success("Invoice processed successfully.")
                    st.dataframe(final_df.head())
                else:
                    st.error("No tables were found in the PDF.")
            except Exception as e:
                st.error(f"Error processing PDF: {str(e)}")

        if os.path.exists(temp_invoice_path):
            os.remove(temp_invoice_path)

    st.write("---")

    # File uploader for Reg San Excel
    uploaded_excel = st.file_uploader("Upload Reg San Excel Sheet", type=["xlsx"])

    if uploaded_excel is not None:
        excel_file = uploaded_excel
        sheet_names = pd.ExcelFile(excel_file).sheet_names
        selected_sheet = st.selectbox("Select a sheet", sheet_names)

        if st.button("Process Reg San Excel"):
            reg_san_csv = process_reg_san_excel(excel_file, selected_sheet)
            st.success(f"Reg San data saved to {reg_san_csv}")

            st.session_state.reg_san_data = pd.read_csv(reg_san_csv)

            st.dataframe(st.session_state.reg_san_data)

    st.write("---")

    # File uploader for Purchase Order PDF
    uploaded_purchase_order = st.file_uploader("Upload Purchase Order PDF", type=["pdf"])

    if uploaded_purchase_order is not None:
        if st.button("Process Purchase Order"):
            pdf_text = extract_text_from_pdf(uploaded_purchase_order)
            df = extract_table_data(pdf_text)
            
            if not df.empty:
                df.to_csv(os.path.join(TEMP_DIR, 'purchase_order.csv'), index=False)
                st.session_state.purchase_order_data = df
                st.success("Purchase Order processed successfully.")
                st.dataframe(df)
            else:
                st.warning("No table data found in the PDF.")

    st.write("---")

    # Merge Invoice and Purchase Order
    if st.button("Merge Invoice and Purchase Order"):
        if st.session_state.final_df is not None and st.session_state.purchase_order_data is not None:
            df_merged_po_invoice = process_invoice_purchase_order()
            st.write("Merged Invoice and Purchase Order Data:")
            st.dataframe(df_merged_po_invoice)
        else:
            st.error("Please upload both the invoice PDF and Purchase Order CSV.")

    # Load Data and Merge by UPC
    if st.button("Load Data and Merge by UPC"):
        if st.session_state.final_df is not None and st.session_state.reg_san_data is not None:
            merged_df, renamed_df = merging_logic(st.session_state.final_df, st.session_state.reg_san_data)
            st.write("Renamed Data:")
            st.dataframe(renamed_df)

            csv_buffer = io.StringIO()
            renamed_df.to_csv(csv_buffer, index=False)
            st.download_button(
                label="Download Merged CSV",
                data=csv_buffer.getvalue(),
                file_name="merged_data.csv",
                mime="text/csv"
            )
        else:
            st.error("Please upload both the invoice PDF and Reg San Excel file.")

    # Clean up CSV files on refresh
    if st.button("Clear Data"):
        if os.path.exists(os.path.join(TEMP_DIR, 'invoice.csv')):
            os.remove(os.path.join(TEMP_DIR, 'invoice.csv'))
        if os.path.exists(os.path.join(TEMP_DIR, 'purchase_order.csv')):
            os.remove(os.path.join(TEMP_DIR, 'purchase_order.csv'))
        st.session_state.final_df = None
        st.session_state.purchase_order_data = None
        st.session_state.reg_san_data = None
        st.success("Data cleared.")

if __name__ == "__main__":
    main()
