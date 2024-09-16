import pandas as pd
import ast

# Read the CSV file
df = pd.read_csv('output.csv')

# Assuming each cell in the column contains a list of dictionaries as strings
df['products'] = df['data'].apply(ast.literal_eval)

# Normalize the list of dictionaries into a DataFrame
normalized_df = pd.json_normalize(df['products'].explode())

# If needed, you can now save this DataFrame into a CSV file
normalized_df.to_csv('cleaned_data_payorder.csv', index=False)

print(normalized_df)
