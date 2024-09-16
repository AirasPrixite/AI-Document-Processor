import pandas as pd
import ast
import numpy as np

# Read the CSV file
df = pd.read_csv('output_payorder.csv')

# Print columns and shape for debugging
print("Columns:", df.columns)
print("Shape:", df.shape)

# Check if the last row has data in the second column
if df.shape[1] > 1:  # Ensure there are at least two columns
    if df.iloc[-1, 1] and not df.iloc[-1, 0]:
        df.iloc[-1, 0] = df.iloc[-1, 1]
        df.iloc[-1, 1] = np.nan
else:
    print("DataFrame does not have enough columns.")

# Replace NaN values with an empty string
df['data'] = df['data'].fillna('[]')

# Convert the 'data' column from string representation of list of dictionaries to actual lists
def safe_literal_eval(x):
    try:
        return ast.literal_eval(x)
    except (ValueError, SyntaxError):
        return []

df['products'] = df['data'].apply(safe_literal_eval)

# Normalize the list of dictionaries into a DataFrame
normalized_df = pd.json_normalize(df['products'].explode())

# If needed, you can now save this DataFrame into a CSV file
normalized_df.to_csv('cleaned_data_payorder.csv', index=False)

print(normalized_df)
