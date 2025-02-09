import boto3
import pandas as pd
from datetime import datetime as dt
from tqdm import tqdm
import warnings
import os

warnings.filterwarnings('ignore')
pd.set_option('display.max_columns', None)

# AWS S3 Configuration
BUCKET_NAME = 'redfin-final-csv'
OUTPUT_FILE_NAME = 'real_estate_data.csv'
OUTPUT_FILE_KEY = 'real_estate_data.csv'

# Redfin dataset URL
URL_BY_CITY = 'https://redfin-public-data.s3.us-west-2.amazonaws.com/redfin_market_tracker/city_market_tracker.tsv000.gz'

def extract_data(url):
    """Extracts the Redfin dataset from the given URL."""
    print("Extracting data from Redfin dataset...")
    df = pd.read_csv(url, compression='gzip', sep='\t')
    print(f"Data extracted: {len(df)} rows, {len(df.columns)} columns")
    return df

def transform_data(df):
    """Performs data cleaning and transformation."""
    print("Transforming data...")

    # Remove commas from the 'city' column
    df['city'] = df['city'].str.replace(',', '')

    # Select relevant columns
    cols = ['period_begin', 'period_end', 'period_duration', 'region_type', 'region_type_id', 'table_id',
            'is_seasonally_adjusted', 'city', 'state', 'state_code', 'property_type', 'property_type_id',
            'median_sale_price', 'median_list_price', 'median_ppsf', 'median_list_ppsf', 'homes_sold',
            'inventory', 'months_of_supply', 'median_dom', 'avg_sale_to_list', 'sold_above_list',
            'parent_metro_region_metro_code', 'last_updated']

    df = df[cols].dropna()

    # Convert period_begin and period_end to datetime
    df['period_begin'] = pd.to_datetime(df['period_begin'])
    df['period_end'] = pd.to_datetime(df['period_end'])

    # Extract year and month
    df["period_begin_in_years"] = df['period_begin'].dt.year
    df["period_end_in_years"] = df['period_end'].dt.year
    df["period_begin_in_months"] = df['period_begin'].dt.month
    df["period_end_in_months"] = df['period_end'].dt.month

    # Month mapping
    month_dict = {
        "period_begin_in_months": {
            1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
            7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
        },
        "period_end_in_months": {
            1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
            7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
        }
    }
    df = df.replace(month_dict)

    print(f"Transformation complete. Final dataset: {len(df)} rows, {len(df.columns)} columns")
    return df

def save_to_csv(df, filename):
    """Saves the transformed data to a CSV file."""
    df.to_csv(filename, index=False)
    print(f"Data saved to {filename}")

def upload_to_s3(bucket, local_file, s3_key):
    """Uploads the file to AWS S3 with a progress bar."""
    s3 = boto3.client('s3')
    file_size = os.path.getsize(local_file)

    with tqdm(total=file_size, unit='B', unit_scale=True, desc="Uploading to S3") as pbar:
        with open(local_file, 'rb') as f:
            s3.upload_fileobj(f, bucket, s3_key, Callback=pbar.update)

    print(f"File uploaded to s3://{bucket}/{s3_key}")

if __name__ == "__main__":
    # Step 1: Extract data
    df = extract_data(URL_BY_CITY)

    # Step 2: Transform data
    df = transform_data(df)

    # Step 3: Save to CSV
    save_to_csv(df, OUTPUT_FILE_NAME)

    # Step 4: Upload to AWS S3
    upload_to_s3(BUCKET_NAME, OUTPUT_FILE_NAME, OUTPUT_FILE_KEY)
