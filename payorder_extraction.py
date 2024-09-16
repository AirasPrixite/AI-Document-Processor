import base64
import json
import os
import shutil
import pandas as pd
from openai import OpenAI
from pdf2image import convert_from_path

# Initialize the OpenAI client
client = OpenAI(api_key="****")

# Function to encode images in base64
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

# Function to extract insights from a single image frame
def extract_insights_from_frame(image_path):
    base64_image = encode_image(image_path)
    prompt = """
    Please extract the following values in valid JSON format. Also, please keep in mind that Internal Cod/Cod Vend are two different columns
    they are mistakenly given as oint name they have separate values. Provide the data as a JSON list. Can you extract these values?
    'Item', 'Internal Cod', 'Cod Vend', 'Description', 'Quantity', 'UM', 'Unit Price', 'Net Amount'. Keep in mind that if any page has no value
    dont consider that page for extraction.
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "system",
            "content": "You are a helpful assistant that extracts values from images."
        }, {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
            ]
        }],
        response_format={"type": "json_object"},
        temperature=0.0,
    )

    # Debugging: print the raw response content
    response_content = response.choices[0].message.content
    print("Raw response content:")
    print(response_content)

    try:
        # Attempt to parse the response content as JSON
        json_data = json.loads(response_content)

        # Check if json_data is a dictionary and convert it to a list if needed
        if isinstance(json_data, dict):
            json_data = [json_data]

        # Convert JSON to Pandas DataFrame
        df = pd.DataFrame(json_data)
        print("\nExtracted Data (Table Format):\n")
        print(df.to_string(index=False))

        return json_data
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON: {e}")
        print("Raw response that caused the error:")
        print(response_content)
        return None

# Function to convert PDF to images and save them in a folder
def pdf_to_images(pdf_path, image_folder):
    if not os.path.exists(image_folder):
        os.makedirs(image_folder)

    images = convert_from_path(pdf_path)
    image_paths = []
    for i, image in enumerate(images):
        image_path = os.path.join(image_folder, f"page_{i + 1}.png")
        image.save(image_path, "PNG")
        image_paths.append(image_path)

    return image_paths

# Function to process PDF, extract data, and save to DataFrame
def process_pdf_and_extract_data(pdf_path, output_csv="output_payorder.csv"):
    # Create a folder to store images
    image_folder = "temp_images"
    image_paths = pdf_to_images(pdf_path, image_folder)

    all_data = []
    for image_path in image_paths:
        data = extract_insights_from_frame(image_path)
        if data:
            all_data.extend(data)  # Flatten the list of dictionaries

    if all_data:
        # Normalize the list of dictionaries into a DataFrame
        df = pd.json_normalize(all_data)

        # Save to CSV
        df.to_csv(output_csv, index=False)
        print(f"\nData saved to {output_csv}\n")
        print(df.to_string(index=False))  # Print final table

    # Delete the folder with images
    shutil.rmtree(image_folder)
    print(f"Temporary folder '{image_folder}' deleted.")

# Example usage
pdf_path = "*****.pdf"
process_pdf_and_extract_data(pdf_path)
