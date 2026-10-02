# Big Data Engineering - Assignment 3
## Building ELT Data Pipelines with Airflow, dbt, and PostgreSQL

### Overview
This repository implements an end-to-end ELT data pipeline following the **Medallion Architecture (Bronze, Silver, Gold)** using Apache Airflow, PostgreSQL (Cloud SQL), and dbt (dbt Cloud / dbt Core). The pipeline processes 12 months of Sydney Airbnb listing data alongside ABS 2016 Census datasets (G01 & G02) and LGA-to-suburb mappings to produce analytical business datamarts and ad-hoc insights.

---

### Architecture & Layers

```
Raw CSV Datasets
       │
       ▼  (Airflow DAG: load_airbnb_census_dag)
┌──────────────────────────────────────────────────────────┐
│ BRONZE SCHEMA (PostgreSQL)                               │
│ - raw_listings (74 columns + audit metadata)             │
│ - raw_census_g01 (2016 Census Person characteristics)   │
│ - raw_census_g02 (2016 Census Medians and Averages)     │
│ - raw_lga_suburb (LGA to Suburb lookup)                  │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼  (dbt Staging & Snapshots)
┌──────────────────────────────────────────────────────────┐
│ SILVER SCHEMA (PostgreSQL)                               │
│ - stg_listings (View: typed, currency cleaned, dates)    │
│ - snapshot_host (SCD2 snapshot with timestamp strategy)  │
│ - snapshot_property (SCD2 snapshot with timestamp)       │
│ - snapshot_suburb_lga (SCD2 snapshot with timestamp)     │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼  (dbt Gold Models & Datamarts)
┌──────────────────────────────────────────────────────────┐
│ GOLD SCHEMA (PostgreSQL)                                 │
│ 1. Star Schema Dimensions:                               │
│    - dim_host, dim_property, dim_suburb, dim_lga         │
│ 2. Reference Tables:                                     │
│    - census_g01, census_g02                              │
│ 3. Fact Table:                                           │
│    - fact_listings (IDs, dates, and metrics ONLY)        │
│ 4. Datamart Views (Point-in-Time SCD2 Joins):            │
│    - dm_listing_neighbourhood                            │
│    - dm_property_type                                    │
│    - dm_host_neighbourhood                               │
└──────────────────────────────────────────────────────────┘
```

---

### Project Structure
```
.
├── dags/
│   └── load_airbnb_census_dag.py       # Airflow DAG (schedule_interval=None)
├── data/                               # 12 monthly CSVs & Census reference files
├── dbt_bde/
│   ├── dbt_project.yml                 # dbt project configurations
│   ├── profiles.yml                    # Postgres connection profiles
│   ├── macros/
│   │   └── generate_schema_name.sql    # Custom schema naming (bronze/silver/gold)
│   ├── models/
│   │   ├── bronze/sources.yml          # dbt source declarations
│   │   ├── silver/stg_listings.sql     # Silver staging view
│   │   ├── gold/                       # Star schema dims, facts, and census
│   │   └── datamart/                   # 3 required business datamart views
│   └── snapshots/                      # SCD Type 2 dimension snapshots
├── docker-compose.yml                  # Local Airflow & Postgres development stack
├── scripts/
│   ├── generate_sample_data.py         # Test dataset generator
│   └── pipeline_runner.py              # End-to-end execution & validation runner
└── sql/
    ├── 01_create_bronze_schema.sql     # Schema DDL for DBeaver / PostgreSQL
    └── 02_ad_hoc_analysis.sql          # Part 4 ad-hoc analytical queries
```

---

### Quickstart & Execution

#### 1. Run the Entire Pipeline End-to-End
```bash
python3 scripts/pipeline_runner.py --part all
```

#### 2. Run Specific Parts
* **Part 1 (Initial Load)**: `python3 scripts/pipeline_runner.py --part 1`
* **Part 2 (Build Warehouse)**: `python3 scripts/pipeline_runner.py --part 2`
* **Part 3 (Sequential Monthly Incremental)**: `python3 scripts/pipeline_runner.py --part 3`
* **Part 4 (Ad-Hoc Analysis)**: `python3 scripts/pipeline_runner.py --part 4`

#### 3. Run Ad-Hoc SQL Analysis via psql
```bash
psql -U postgres -h localhost -d postgres -f sql/02_ad_hoc_analysis.sql
```
