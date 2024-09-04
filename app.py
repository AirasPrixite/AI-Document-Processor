import streamlit as st
import pandas as pd
from PyPDF2 import PdfReader
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

# Function to extract data from the PO PDF
def extract_po_data(po_file):
    pdf = PdfReader(po_file)
    text = ""
    for page in pdf.pages:
        text += page.extract_text()
    # Dummy extraction logic; replace with actual parsing
    po_data = {
        'Order Number': '4400002540',
        'Supplier Name': 'Laboratorios Dr. Collado S.A.'
        # Airas here you can define more fields based on  PO structure
    }
    return po_data

# Updated function to extract data from the Invoice PDF
def extract_invoice_data(invoice_file):
    pdf = PdfReader(invoice_file)
    text = ""
    for page in pdf.pages:
        text += page.extract_text()
    # Dummy extraction logic; replace with actual parsing
    invoice_data = {
        'Invoice Number': '696079456',
        'Qty Shipped': 60,
        'Net Price': 4.80
        # Here you can add more fields based on your Invoice structure
    }
    return invoice_data

# Function to extract data from the Excel file
def extract_excel_data(excel_file, brand):
    xls = pd.ExcelFile(excel_file)
    sheet_names = xls.sheet_names
    sheet = [name for name in sheet_names if brand in name][0]
    df = pd.read_excel(xls, sheet_name=sheet)
    return df

# Generate FACTURA TRADUCCION Y REGISTROS.xlsx
def generate_translation_records(po_data, invoice_data, excel_data):
    df = pd.DataFrame({
        'Product': ['Example Product'],
        'Descripcion': ['Example Description'],
        'Origin': ['Example Origin'],
        'Qty Shipped': [invoice_data['Qty Shipped']],
        'Extension USD': [invoice_data['Qty Shipped'] * invoice_data['Net Price']],
        'Reg San': ['Example Reg San']
    })
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    output.seek(0)
    return output

# Generate FACTURA PARA FINES DE PERMISO Y ADUANAS.pdf
def generate_permits_and_customs_pdf(invoice_file, excel_data):
    output = BytesIO()
    c = canvas.Canvas(output, pagesize=letter)
    c.drawString(100, 750, "Invoice and Customs Document")
    # Example, you should replace this with actual PDF manipulation
    c.drawString(100, 700, "Example Data from Invoice and Excel")
    c.save()
    output.seek(0)
    return output

# Generate EE 1800023968.XLS
def generate_ee_file(po_data, invoice_data):
    df = pd.DataFrame({
        'Doc Compra': [po_data['Order Number']],
        'Entrega Entrante': ['Input from User'],
        'Posición': [po_data['Order Number']],
        'Fecha Entrega Entrante': ['Input from User'],
        'Número Material': [po_data['Order Number']],
        'Descripción Material': ['Example Description'],
        'Cantidad Pedido': [60],  # Example values
        'Cantidad Entrega Entrante': [invoice_data['Qty Shipped']],
        'Diferencia Cantidad': [60 - invoice_data['Qty Shipped']],
        'Precio Pedido': [4.80],
        'Precio Entrega Entrante': [invoice_data['Net Price']],
        'Diferencia Precio': [4.80 - invoice_data['Net Price']]
    })
    output = BytesIO()
    df.to_excel(output, index=False, sheet_name='Sheet1')
    output.seek(0)
    return output

# Streamlit UI
st.title('Document Processing for NYX')

# Upload PO File
po_file = st.file_uploader("Upload Purchase Order PDF", type=["pdf"])
if po_file is not None:
    po_data = extract_po_data(po_file)
    st.write("Purchase Order Data:", po_data)

# Upload Invoice File
invoice_file = st.file_uploader("Upload Invoice PDF", type=["pdf"])
if invoice_file is not None:
    invoice_data = extract_invoice_data(invoice_file)
    st.write("Invoice Data:", invoice_data)

# Upload Excel File
excel_file = st.file_uploader("Upload Excel File", type=["xlsx"])
if excel_file is not None:
    excel_data = extract_excel_data(excel_file, 'NYX')
    st.write("Excel Data:", excel_data)

# Generate Outputs
if po_file and invoice_file and excel_file:
    # Generate and display FACTURA TRADUCCION Y REGISTROS.xlsx
    translation_records = generate_translation_records(po_data, invoice_data, excel_data)
    st.download_button("Download FACTURA TRADUCCION Y REGISTROS.xlsx", translation_records, file_name="FACTURA_TRADUCCION_Y_REGISTROS.xlsx")

    # Generate and display FACTURA PARA FINES DE PERMISO Y ADUANAS.pdf
    permits_and_customs_pdf = generate_permits_and_customs_pdf(invoice_file, excel_data)
    st.download_button("Download FACTURA PARA FINES DE PERMISO Y ADUANAS.pdf", permits_and_customs_pdf, file_name="FACTURA_PARA_FINES_DE_PERMISO_Y_ADUANAS.pdf")

    # Generate and display EE 1800023968.XLS
    ee_file = generate_ee_file(po_data, invoice_data)
    st.download_button("Download EE 1800023968.XLS", ee_file, file_name="EE_1800023968.xls")

    # Placeholder for PO# 4400002540 Final EE 1800023968.pdf
    st.write("PO# 4400002540 Final EE 1800023968.pdf will be generated as part of phase 2.")
