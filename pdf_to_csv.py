import pdfplumber
import pandas as pd
import sys
from datetime import datetime
import csv
import re

def format_date(date):
    try:
        parsed_date = datetime.strptime(date + '/2023', '%d/%m/%Y')
        return parsed_date.strftime('%Y.%m.%d')
    except ValueError:
        return date

def format_value_date(date):
    try:
        parsed_date = datetime.strptime(date, '%d%m%y')
        return parsed_date.strftime('%Y.%m.%d')
    except ValueError:
        return date

def format_number(number):
    if number is None:
        return ''
    return number.replace('.', '')

def clean_description(description):
    if description is None:
        return ''
    return description.replace('\n', ' ').strip()

# Function to standardize and ensure unique columns of a DataFrame
def standardize_columns(df, columns):
    for col in columns:
        if col not in df.columns:
            df[col] = None
    return df[columns]

# Function to make columns unique
def make_unique_columns(columns):
    seen = {}
    result = []
    for col in columns:
        if isinstance(col, str):
            res = col.split("\n")
            if len(res) > 1:
                col = res[1]
            else:
                col = res[0]
        if col in seen:
            seen[col] += 1
            result.append(f"{col}_{seen[col]}")
        else:
            seen[col] = 0
            result.append(col)
    return result

# Check if input file is provided
if len(sys.argv) != 2:
    print("Usage: python pdf_to_csv.py <input_pdf>")
    input_pdf = "/Users/ikoroteev/projects/budget/hellenic_pdf_to_csv/input/input.pdf"  # Replace with your PDF path
else:
    input_pdf = sys.argv[1]

# Path to the output CSV file
output_csv = "output.csv"

# Open the PDF file
with pdfplumber.open(input_pdf) as pdf:
    # Initialize a list to hold the DataFrames
    df_list = []
    all_columns = []

    # First pass to collect all unique columns
    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            columns = table[0]
            all_columns.extend(columns)
    
    # Ensure all columns are unique
    all_columns = make_unique_columns(all_columns)

    # Second pass to create DataFrames with standardized columns
    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            columns = make_unique_columns(table[0])
            df = pd.DataFrame(table[1:], columns=columns)  # Assuming the first row is the header
            df = standardize_columns(df, all_columns)
            df_list.append(df)

# Concatenate all DataFrames
all_data = pd.concat(df_list, ignore_index=True)

with open(output_csv, mode='w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)

    # Write CSV header
    writer.writerow(["DATE", "DESCRIPTION", "DEBIT", "CREDIT", "BALANCE"])

    date_regex = re.compile(r'\d{2}/\d{2}')
    value_date_regex = re.compile(r'\d{6}')
    number_regex = re.compile(r'\d+,\d+')

    for row in all_data.values:
        if len(row) < 7:
            continue
        
        date = format_date(str(row[5]))
        description = clean_description(str(row[2]))
        debit = format_number(row[3])
        credit = format_number(row[4])
        balance = format_number(row[6])

        if date and (debit or credit) and description != 'None':
            writer.writerow([date, description, debit, credit, balance])

print(f"CSV file created successfully: {output_csv}")
