import pandas as pd

# Load the Excel file
file_path = "WSHR.NE Details.xlsx"
xls = pd.ExcelFile(file_path, engine="openpyxl")

# Define the sheets we want to analyze
sheets_to_analyze = ["WSHR.NE Holdings", "WSHR.NE Sector", "WSHR.NE Country"]

for sheet_name in sheets_to_analyze:
    print(f"\n🔹 Analyzing Sheet: {sheet_name}")

    # Read the specific sheet
    df = pd.read_excel(xls, sheet_name=sheet_name)

    # Display column names
    print("\n📌 Column Names:")
    print(df.columns.tolist())

    # Show the first 12 rows
    print("\n📊 First 12 Rows:")
    print(df.head(12))  # Show first 12 rows instead of 5

    # Show summary statistics (numerical & categorical)
    print("\n📈 Summary Statistics:")
    print(df.describe(include="all"))

    # Show missing values
    print("\n⚠️ Missing Values:")
    print(df.isnull().sum())

    print("\n" + "-" * 50)  # Separator for clarity
