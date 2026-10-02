"""
UTS 36120: Big Data Engineering - Assignment 3
Airflow DAG: load_airbnb_census_dag.py
Description: Ingests Airbnb Sydney monthly CSVs, Census G01/G02, and LGA/Suburb mapping
             into the PostgreSQL 'bronze' schema.
Requirements:
  - schedule_interval=None (manually triggered as specified)
  - Loads initial month (05_2020.csv) or parameterized month via dag_run.conf
  - Handles GCP Cloud Composer (GCS bucket) or local Airflow data folder
"""

import os
import io
import csv
import logging
from datetime import datetime, timedelta
import pandas as pd

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

# Default arguments for DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2020, 5, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

# Environment configurations
POSTGRES_CONN_ID = os.environ.get('POSTGRES_CONN_ID', 'postgres_default')
GCS_BUCKET_NAME = os.environ.get('GCS_BUCKET_NAME', '')
LOCAL_DATA_DIR = os.environ.get('AIRFLOW_DATA_DIR', '/opt/airflow/data')


def get_file_content(file_path_or_blob_name):
    """
    Reads file from GCS bucket if configured, otherwise falls back to local data directory.
    """
    if GCS_BUCKET_NAME:
        from airflow.providers.google.cloud.hooks.gcs import GCSHook
        gcs_hook = GCSHook()
        logging.info(f"Fetching gs://{GCS_BUCKET_NAME}/{file_path_or_blob_name}")
        file_bytes = gcs_hook.download(bucket_name=GCS_BUCKET_NAME, object_name=file_path_or_blob_name)
        return io.BytesIO(file_bytes)
    else:
        # Local file system fallback
        local_path = os.path.join(LOCAL_DATA_DIR, os.path.basename(file_path_or_blob_name))
        if not os.path.exists(local_path):
            # Check relative to repo
            candidate = os.path.join('/Users/aryan/AT3_BDE/data', os.path.basename(file_path_or_blob_name))
            if os.path.exists(candidate):
                local_path = candidate
        logging.info(f"Reading local file: {local_path}")
        return open(local_path, 'rb')


def load_census_g01(**kwargs):
    """Loads Census G01 table into bronze.raw_census_g01"""
    file_name = '2016Census_G01_NSW_LGA.csv'
    logging.info(f"Loading {file_name} into bronze.raw_census_g01")
    
    try:
        content = get_file_content(file_name)
        df = pd.read_csv(content, dtype=str)
        # Standardize column names (lowercase)
        df.columns = [c.strip().lower() for c in df.columns]
        
        # Map LGA code column if needed
        lga_col = [c for c in df.columns if 'lga' in c]
        if lga_col and lga_col[0] != 'lga_code':
            df.rename(columns={lga_col[0]: 'lga_code'}, inplace=True)
            
        pg_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
        engine = pg_hook.get_sqlalchemy_engine()
        df.to_sql('raw_census_g01', engine, schema='bronze', if_exists='replace', index=False)
        logging.info("Successfully loaded bronze.raw_census_g01")
    except Exception as e:
        logging.warning(f"Could not load {file_name}: {e}. Ensure file is present in bucket/data dir.")


def load_census_g02(**kwargs):
    """Loads Census G02 table into bronze.raw_census_g02"""
    file_name = '2016Census_G02_NSW_LGA.csv'
    logging.info(f"Loading {file_name} into bronze.raw_census_g02")
    
    try:
        content = get_file_content(file_name)
        df = pd.read_csv(content, dtype=str)
        df.columns = [c.strip().lower() for c in df.columns]
        
        lga_col = [c for c in df.columns if 'lga' in c]
        if lga_col and lga_col[0] != 'lga_code':
            df.rename(columns={lga_col[0]: 'lga_code'}, inplace=True)
            
        pg_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
        engine = pg_hook.get_sqlalchemy_engine()
        df.to_sql('raw_census_g02', engine, schema='bronze', if_exists='replace', index=False)
        logging.info("Successfully loaded bronze.raw_census_g02")
    except Exception as e:
        logging.warning(f"Could not load {file_name}: {e}. Ensure file is present in bucket/data dir.")


def load_lga_suburb(**kwargs):
    """Loads LGA to Suburb mapping into bronze.raw_lga_suburb"""
    file_name = 'NSW_LGA_Suburb_Mapping.csv'
    logging.info(f"Loading {file_name} into bronze.raw_lga_suburb")
    
    try:
        content = get_file_content(file_name)
        df = pd.read_csv(content, dtype=str)
        df.columns = [c.strip().lower() for c in df.columns]
        
        pg_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
        engine = pg_hook.get_sqlalchemy_engine()
        df.to_sql('raw_lga_suburb', engine, schema='bronze', if_exists='replace', index=False)
        logging.info("Successfully loaded bronze.raw_lga_suburb")
    except Exception as e:
        logging.warning(f"Could not load {file_name}: {e}. Ensure file is present in bucket/data dir.")


def load_airbnb_listings(**kwargs):
    """
    Loads Airbnb listings into bronze.raw_listings.
    Can be run for a specific month via dag_run.conf (e.g. {"file": "05_2020.csv"})
    or defaults to '05_2020.csv' for the initial load.
    Appends data with file_source metadata.
    """
    dag_run = kwargs.get('dag_run')
    file_name = '05_2020.csv'
    if dag_run and dag_run.conf and 'file' in dag_run.conf:
        file_name = dag_run.conf['file']
    
    logging.info(f"Loading Airbnb dataset: {file_name} into bronze.raw_listings")
    
    content = get_file_content(file_name)
    df = pd.read_csv(content, dtype=str, low_memory=False)
    df['file_source'] = file_name
    df['ingestion_timestamp'] = datetime.utcnow().isoformat()
    
    pg_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    engine = pg_hook.get_sqlalchemy_engine()
    
    # Append to raw_listings so consecutive monthly loads build chronological history
    df.to_sql('raw_listings', engine, schema='bronze', if_exists='append', index=False)
    logging.info(f"Successfully loaded {len(df)} rows from {file_name} into bronze.raw_listings")


with DAG(
    dag_id='load_airbnb_census_dag',
    default_args=default_args,
    description='EL pipeline: Ingests Sydney Airbnb and ABS Census data into Bronze schema',
    schedule_interval=None,  # As required: no set schedule interval
    catchup=False,
    max_active_runs=1,
    tags=['bde', 'assignment_3', 'elt', 'airbnb', 'census']
) as dag:

    task_load_census_g01 = PythonOperator(
        task_id='load_census_g01',
        python_callable=load_census_g01,
        provide_context=True,
    )

    task_load_census_g02 = PythonOperator(
        task_id='load_census_g02',
        python_callable=load_census_g02,
        provide_context=True,
    )

    task_load_lga_suburb = PythonOperator(
        task_id='load_lga_suburb_mapping',
        python_callable=load_lga_suburb,
        provide_context=True,
    )

    task_load_airbnb = PythonOperator(
        task_id='load_airbnb_monthly_listings',
        python_callable=load_airbnb_listings,
        provide_context=True,
    )

    # Reference data can be loaded in parallel, Airbnb listings alongside
    [task_load_census_g01, task_load_census_g02, task_load_lga_suburb] >> task_load_airbnb
