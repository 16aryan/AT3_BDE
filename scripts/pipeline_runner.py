#!/usr/bin/env python3
"""
UTS 36120: Big Data Engineering - Assignment 3
Pipeline Simulation & Automation Runner
Author: Aryan Goel

Features:
  - Part 1: Ingests 05_2020.csv, Census G01, Census G02, and LGA mapping into Bronze schema.
  - Part 2: Triggers dbt snapshots (SCD2) and dbt run to build Bronze, Silver, Gold, and 3 Datamarts.
  - Part 3: Simulates sequential monthly ingestion (06_2020 to 04_2021), running dbt after each month.
  - Part 4: Executes ad-hoc analysis queries and displays results.
"""

import os
import sys
import glob
import subprocess
import argparse
import pandas as pd
from sqlalchemy import create_engine, text

# Configuration defaults
DB_USER = os.getenv("DBT_USER", "postgres")
DB_PASS = os.getenv("DBT_PASSWORD", "postgres")
DB_HOST = os.getenv("DBT_HOST", "localhost")
DB_PORT = os.getenv("DBT_PORT", "5432")
DB_NAME = os.getenv("DBT_DBNAME", "postgres")
DATA_DIR = os.getenv("DATA_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data")))
DBT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dbt_bde"))

DBT_SSLMODE = os.getenv("DBT_SSLMODE", "prefer")
DATABASE_URI = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode={DBT_SSLMODE}"


def get_engine():
    return create_engine(DATABASE_URI)


def run_dbt(command):
    """Executes a dbt command inside the dbt_bde project directory"""
    dbt_bin = os.getenv("DBT_BIN", "/opt/miniconda3/bin/dbt" if os.path.exists("/opt/miniconda3/bin/dbt") else "dbt")
    full_cmd = f"{dbt_bin} {command} --profiles-dir {DBT_DIR} --project-dir {DBT_DIR}"
    print(f"\n[DBT] Executing: {full_cmd}")
    env = os.environ.copy()
    env.update({
        "DBT_USER": DB_USER,
        "DBT_PASSWORD": DB_PASS,
        "DBT_HOST": DB_HOST,
        "DBT_PORT": DB_PORT,
        "DBT_DBNAME": DB_NAME
    })
    res = subprocess.run(full_cmd, shell=True, env=env)
    if res.returncode != 0:
        print(f"[DBT Warning] Command exited with code {res.returncode}")
    return res.returncode


def init_bronze_schema():
    """Initializes schemas and raw tables using 01_create_bronze_schema.sql"""
    print("\n--- Initializing Bronze, Silver, and Gold Schemas ---")
    sql_path = os.path.join(os.path.dirname(__file__), "..", "sql", "01_create_bronze_schema.sql")
    with open(sql_path, "r") as f:
        sql_content = f.read()

    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text(sql_content))
    print("✓ Bronze schema and tables created.")


def load_csv_to_bronze(file_name, target_table, if_exists="append"):
    """Loads a CSV into a target bronze table"""
    file_path = os.path.join(DATA_DIR, file_name)
    if not os.path.exists(file_path):
        print(f"[Warning] File not found: {file_path}. Skipping.")
        return False

    print(f"Loading {file_name} -> bronze.{target_table} (if_exists='{if_exists}')")
    df = pd.read_csv(file_path, dtype=str, low_memory=False)
    df.columns = [c.strip().lower() for c in df.columns]

    if target_table == "raw_listings":
        df["file_source"] = file_name

    engine = get_engine()
    df.to_sql(target_table, engine, schema="bronze", if_exists=if_exists, index=False)
    print(f"✓ Loaded {len(df)} rows into bronze.{target_table}")
    return True


def part1_initial_load():
    """Part 1: Ingest initial month 05_2020 + Census + LGA mapping"""
    print("\n=======================================================")
    print("PART 1: Initial Data Ingestion (Airflow Simulation)")
    print("=======================================================")
    init_bronze_schema()

    # Load Reference Datasets
    load_csv_to_bronze("2016Census_G01_NSW_LGA.csv", "raw_census_g01", if_exists="replace")
    load_csv_to_bronze("2016Census_G02_NSW_LGA.csv", "raw_census_g02", if_exists="replace")
    load_csv_to_bronze("NSW_LGA_Suburb_Mapping.csv", "raw_lga_suburb", if_exists="replace")

    # Load First Month of Airbnb Listings
    load_csv_to_bronze("05_2020.csv", "raw_listings", if_exists="append")


def part2_build_dwh():
    """Part 2: Run dbt to build Bronze, Silver (SCD2 snapshots), Gold, and Datamarts"""
    print("\n=======================================================")
    print("PART 2: Design Data Warehouse with dbt")
    print("=======================================================")
    run_dbt("run --select stg_listings")
    run_dbt("snapshot")
    run_dbt("run")


def part3_incremental_monthly():
    """Part 3: Ingest remaining months sequentially (06_2020 to 04_2021) and run dbt after each"""
    print("\n=======================================================")
    print("PART 3: Sequential Monthly Ingestion & dbt Runs")
    print("=======================================================")
    monthly_files = [
        "06_2020.csv", "07_2020.csv", "08_2020.csv", "09_2020.csv",
        "10_2020.csv", "11_2020.csv", "12_2020.csv", "01_2021.csv",
        "02_2021.csv", "03_2021.csv", "04_2021.csv"
    ]

    for month_file in monthly_files:
        print(f"\n--- Ingesting {month_file} ---")
        loaded = load_csv_to_bronze(month_file, "raw_listings", if_exists="append")
        if loaded:
            print(f"Triggering dbt snapshot and run for {month_file}...")
            run_dbt("snapshot")
            run_dbt("run")


def part4_ad_hoc_analysis():
    """Part 4: Execute analytical queries against Gold / Datamart layers"""
    print("\n=======================================================")
    print("PART 4: Ad-Hoc Analytical Queries")
    print("=======================================================")
    sql_path = os.path.join(os.path.dirname(__file__), "..", "sql", "part_4.sql")
    with open(sql_path, "r") as f:
        sql_content = f.read()

    engine = get_engine()
    queries = [q.strip() for q in sql_content.split(";") if q.strip()]

    labels = [
        "Question A: Top 3 vs Bottom 3 LGAs Demographics Comparison",
        "Question B: Pearson Correlation (Median Age vs Avg Revenue)",
        "Question C: Best Listing Configuration for Top 5 Neighbourhoods",
        "Question D: Host Concentration Across LGAs",
        "Question E: Single-Listing Hosts vs Median Mortgage Repayments"
    ]

    for i, q in enumerate(queries[:5]):
        label = labels[i] if i < len(labels) else f"Query {i+1}"
        print(f"\n=======================================================")
        print(f">>> {label} <<<")
        print(f"=======================================================")
        try:
            with engine.connect() as conn:
                df = pd.read_sql_query(text(q.replace("%", "%%")), conn)
            print(df.to_string(index=False))
        except Exception as e:
            try:
                raw_conn = engine.raw_connection()
                df = pd.read_sql_query(q, raw_conn)
                print(df.to_string(index=False))
                raw_conn.close()
            except Exception as e2:
                print(f"Query error: {e2}")


def main():
    parser = argparse.ArgumentParser(description="UTS 36120 BDE Assignment 3 Pipeline Runner")
    parser.add_argument("--part", choices=["all", "1", "2", "3", "4"], default="all",
                        help="Run specific assignment part")
    args = parser.parse_args()

    if args.part in ["all", "1"]:
        part1_initial_load()
    if args.part in ["all", "2"]:
        part2_build_dwh()
    if args.part in ["all", "3"]:
        part3_incremental_monthly()
    if args.part in ["all", "4"]:
        part4_ad_hoc_analysis()


if __name__ == "__main__":
    main()
