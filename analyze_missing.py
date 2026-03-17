import pandas as pd

# Load spreadsheet
df = pd.read_excel("my_config_agent/data/House Orders.xlsx", sheet_name="Everybody Else", header=1)

print(f"Total rows: {len(df)}")
print(f"Non-null Serial #: {df['Serial #'].notna().sum()}")
print(f"Non-null Model: {df['Model'].notna().sum()}")
print()

# Find rows with serial but no model
has_serial_no_model = df[(df['Serial #'].notna()) & (df['Model'].isna())]
print(f"Rows with Serial but NO Model: {len(has_serial_no_model)}")
print("\nSample rows with serial but no model:")
for idx, row in has_serial_no_model.head(10).iterrows():
    print(f"  Row {idx+2}: Serial={row['Serial #']}, MSRP={row.get('MSRP', 'N/A')}")

print("\n" + "="*80)

# Find rows with both
has_both = df[(df['Serial #'].notna()) & (df['Model'].notna())]
print(f"\nRows with BOTH Serial AND Model: {len(has_both)}")
print("\nBreakdown by Model value:")
model_counts = has_both['Model'].value_counts()
print(model_counts.head(10))
