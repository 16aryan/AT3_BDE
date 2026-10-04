# UTS 36120: Big Data Engineering - Assignment 3
## Building ELT Data Pipelines with Apache Airflow & dbt

**Student Name:** Aryan Goel  
**Student ID:** 26040826  
**Repository:** [https://github.com/16aryan/AT3_BDE](https://github.com/16aryan/AT3_BDE)  
**Report Document:** [`reports/Assignment_3_Report_Aryan_Goel.docx`](reports/Assignment_3_Report_Aryan_Goel.docx) | [`Assignment_3_Report.md`](Assignment_3_Report.md)

---

## 🚀 Quickstart for Instructors & Markers (Running the DAG)

To run the pipeline and inspect the DAG execution outside GCP, you can start the complete environment in **one command** using Docker Compose.

### Step 1: Start Airflow & PostgreSQL
```bash
git clone https://github.com/16aryan/AT3_BDE.git
cd AT3_BDE
docker compose up -d
```
*(This starts PostgreSQL 15, initializes the Bronze schema and tables, and starts the Apache Airflow 2.8 Webserver & Scheduler).*

### Step 2: Open the Airflow Web UI
1. Open your browser to: **[http://localhost:8080](http://localhost:8080)**
2. Log in with:
   - **Username:** `admin`
   - **Password:** `admin`
3. Locate **`load_airbnb_census_dag`** and toggle it **ON / Unpause**.

### Step 3: Trigger the DAG
* **Via Web UI:** Click the **Trigger DAG** (▶ play) button.
* **Via Terminal CLI (Alternative):**
  ```bash
  docker exec -it bde_airflow_scheduler airflow dags trigger load_airbnb_census_dag
  ```
Navigate to **Graph View** or **Grid View** to see all tasks (`load_census_g01`, `load_census_g02`, `load_lga_suburb_mapping`, `load_airbnb_monthly_listings`) complete with **100% green SUCCESS**.

### Step 4: Run the Complete dbt Warehouse & Analytics (1-Command)
To execute dbt snapshots (SCD Type 2), build the Star Schema (Bronze, Silver, Gold), materialize the 3 Datamart views, and print the Part 4 Ad-Hoc Analytics:
```bash
python3 scripts/pipeline_runner.py --part all
```

---

## Architecture Overview

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
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│ PART 4: AD-HOC BUSINESS ANALYTICS                        │
│ - Q(a): Demographics Top 3 vs Bottom 3 LGAs              │
│ - Q(b): Pearson Correlation (Median Age vs Revenue)      │
│ - Q(c): Optimal Listing Configuration for Top 5 Suburbs  │
└──────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
.
├── dags/
│   └── load_airbnb_census_dag.py       # Production Airflow DAG (schedule_interval=None)
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
├── docker-compose.yml                  # Production Docker stack (Airflow 2.8 + Postgres 15)
├── reports/
│   ├── Assignment_3_Report_Aryan_Goel.docx  # Complete formatted Word report
│   ├── README.md                       # Figures catalog
│   └── images/                         # 6 publication-quality diagrams
├── scripts/
│   ├── generate_sample_data.py         # Test dataset generator
│   ├── generate_report_diagrams.py     # 300 DPI diagram renderer
│   └── pipeline_runner.py              # End-to-end execution & validation runner
└── sql/
    ├── 00_init_postgres_users.sql      # Container database & user initialization
    ├── 01_create_bronze_schema.sql     # Schema DDL for DBeaver / PostgreSQL
    └── 02_ad_hoc_analysis.sql          # Part 4 ad-hoc analytical queries
```

---

## Deliverables & Mark Allocation Mapping

| Brief Component | Implementation | Location |
| :--- | :--- | :--- |
| **Part 1: Airflow Ingestion** | Ingests initial month & reference datasets to Bronze | [`dags/load_airbnb_census_dag.py`](dags/load_airbnb_census_dag.py) |
| **Part 1: Bronze Schema** | Raw tables created via DDL | [`sql/01_create_bronze_schema.sql`](sql/01_create_bronze_schema.sql) |
| **Part 2: Medallion Architecture** | Cleaned staging & SCD2 snapshots | [`dbt_bde/models/silver/`](dbt_bde/models/silver/), [`dbt_bde/snapshots/`](dbt_bde/snapshots/) |
| **Part 2: Gold Star Schema** | Fact (IDs & metrics only) + 4 dimensions + 2 Census | [`dbt_bde/models/gold/`](dbt_bde/models/gold/) |
| **Part 2: 3 Datamart Views** | SCD2 point-in-time join logic & all formulas | [`dbt_bde/models/datamart/`](dbt_bde/models/datamart/) |
| **Part 3: Sequential Ingestion** | Chronological 12-month incremental loads with dbt | [`scripts/pipeline_runner.py`](scripts/pipeline_runner.py) |
| **Part 4: Ad-Hoc Analytics** | SQL answering questions (a), (b), (c) | [`sql/02_ad_hoc_analysis.sql`](sql/02_ad_hoc_analysis.sql) |
| **Full Written Report** | Academic report with figures & empirical findings | [`reports/Assignment_3_Report_Aryan_Goel.docx`](reports/Assignment_3_Report_Aryan_Goel.docx) |
