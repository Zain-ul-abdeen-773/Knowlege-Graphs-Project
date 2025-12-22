"""
Script to truncate all CSV files in the data folder to keep only the first 50,000 rows.
"""
import os
import pandas as pd

DATA_DIR = r"d:\Study\AI-311\Project\data"
MAX_ROWS = 50000

def truncate_csv(file_path):
    """Truncate a CSV file to keep only the first MAX_ROWS rows."""
    print(f"Processing: {os.path.basename(file_path)}")
    
    try:
        # Read only the first MAX_ROWS rows
        df = pd.read_csv(file_path, nrows=MAX_ROWS)
        original_rows = len(df)
        
        # Check if we need to read more to count total rows (for reporting)
        # For large files, we'll skip this step
        file_size = os.path.getsize(file_path)
        
        # Save back to the same file
        df.to_csv(file_path, index=False)
        
        print(f"  ✓ Saved {original_rows} rows to {os.path.basename(file_path)}")
        return True
        
    except Exception as e:
        print(f"  ✗ Error processing {os.path.basename(file_path)}: {e}")
        return False

def main():
    print(f"Truncating CSV files in: {DATA_DIR}")
    print(f"Keeping first {MAX_ROWS:,} rows for each file\n")
    
    csv_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.csv')]
    
    if not csv_files:
        print("No CSV files found in the data directory.")
        return
    
    print(f"Found {len(csv_files)} CSV files:\n")
    
    success_count = 0
    for csv_file in csv_files:
        file_path = os.path.join(DATA_DIR, csv_file)
        if truncate_csv(file_path):
            success_count += 1
        print()
    
    print(f"\nComplete! Successfully truncated {success_count}/{len(csv_files)} files.")

if __name__ == "__main__":
    main()
