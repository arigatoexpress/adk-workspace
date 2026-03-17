import pandas as pd
import os

# Load and inspect the spreadsheet structure
xlsx_path = "my_config_agent/data/House Orders.xlsx"

print("=== Investigating spreadsheet structure ===\n")

# Check all sheets
xlsx = pd.ExcelFile(xlsx_path)
print(f"Available sheets: {xlsx.sheet_names}\n")

# Try different header configurations
for header_row in [0, 1, 2]:
    try:
        df = pd.read_excel(xlsx_path, sheet_name="Everybody Else", header=header_row)
        print(f"Header row {header_row}:")
        print(f"  Columns: {df.columns.tolist()[:8]}")
        if "Serial #" in df.columns:
            non_null = df["Serial #"].notna().sum()
            print(f"  Non-null Serial #: {non_null}/{len(df)}")
        print()
    except Exception as e:
        print(f"Header row {header_row}: Error - {e}\n")

# Inspect first 30 rows with header=1
df = pd.read_excel(xlsx_path, sheet_name="Everybody Else", header=1)
print("\n=== First 30 rows (header=1) ===")
for idx in range(min(30, len(df))):
    row = df.iloc[idx]
    serial = str(row.get("Serial #", ""))[:15]
    model = str(row.get("Model", ""))[:25]
    msrp = str(row.get("MSRP", ""))[:12]
    print(f"Row {idx+2:3d}: {serial:<15} | {model:<25} | {msrp}")
