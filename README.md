# UTS 36120: Big Data Engineering - Assignment 3
## Building ELT Data Pipelines with Apache Airflow & dbt

**Student Name:** Aryan Goel  
**Student ID:** 26040826  
**Repository:** [https://github.com/16aryan/AT3_BDE](https://github.com/16aryan/AT3_BDE)  
**Handover Reports:** [`reports/Assignment_3_Report_Aryan_Goel.docx`](reports/Assignment_3_Report_Aryan_Goel.docx) | [`Assignment_3_Report.md`](Assignment_3_Report.md)  
**Environment:** Validated locally on Docker (PostgreSQL 15, Airflow 2.8.1, dbt Core 1.11); Deployed to Google Cloud Platform (Cloud Composer 2 Airflow 2.11, Cloud SQL PostgreSQL 18)

---

## 🚀 Quickstart for Instructors & Markers

The pipeline is fully portable and can be evaluated either **locally on Docker** or on **Google Cloud Platform (Cloud Composer & Cloud SQL)**.

### Option A: Local Evaluation via Docker (1-Command)

#### 1. Start Airflow & PostgreSQL
```bash
git clone https://github.com/16aryan/AT3_BDE.git
cd AT3_BDE
docker compose up -d
```
*(Starts PostgreSQL 15, initializes the Bronze schema and tables, and boots Apache Airflow 2.8.1 Webserver & Scheduler).*

#### 2. Trigger the Airflow DAG
* **Via Web UI:** Open **[http://localhost:8080](http://localhost:8080)** (login: `admin` / `admin`), unpause `load_airbnb_census_dag`, and click **Trigger DAG** (▶).
* **Via Terminal CLI:**
  ```bash
  docker exec -it bde_airflow_scheduler airflow dags trigger load_airbnb_census_dag
  ```
All tasks (`load_census_g01`, `load_census_g02`, `load_lga_suburb_mapping`, `load_airbnb_monthly_listings`) complete with **100% green SUCCESS**.

#### 3. Run dbt Transformations & Analytical Queries
```bash
python3 scripts/pipeline_runner.py --part all
```
*(Executes dbt snapshots for SCD Type 2, builds the Kimball Star Schema and Datamarts, runs 29 automated tests, and displays the Part 4 SQL analytics).*

---

### Option B: Google Cloud Platform (Cloud Composer 2 & Cloud SQL)

The platform is operational on Google Cloud Platform:
* **Cloud Composer 2 (Airflow 2.11):** Environment `bde-composer` in `australia-southeast1` (Sydney).
* **Cloud SQL (PostgreSQL 18):** Instance `bde-postgres` in `australia-southeast1` (Sydney).
* **Airflow Connection:** `postgres_default` configured via PostgresHook.
* **Storage Abstraction:** The DAG dynamically discovers files across `/home/airflow/gcs/data` (Composer FUSE mount), GCSHook, and `/opt/airflow/data` (local).

To run dbt against Cloud SQL from your CLI:
```bash
cd dbt_bde
export DBT_HOST=<CLOUD_SQL_IP>
export DBT_PASSWORD=<YOUR_PASSWORD>
dbt run --select stg_listings
dbt snapshot
dbt run --select gold
dbt test
```

---

## Architecture Overview

```
Raw CSV Datasets (12 Monthly Airbnb CSVs + Census G01/G02 + Suburb Mapping)
       │
       ▼  (Airflow DAG: load_airbnb_census_dag)
┌──────────────────────────────────────────────────────────┐
│ BRONZE SCHEMA (PostgreSQL)                               │
│ - raw_listings (22 attributes + lineage metadata)        │
│ - raw_census_g01 (2016 Census Person characteristics)   │
│ - raw_census_g02 (2016 Census Medians and Averages)     │
│ - raw_lga_suburb (LGA to Suburb crosswalk)               │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼  (dbt Staging & Snapshots)
┌──────────────────────────────────────────────────────────┐
│ SILVER SCHEMA (PostgreSQL)                               │
│ - stg_listings (View: sanitized types, currency regex)   │
│ - snapshot_host (SCD2 snapshot: state-start strategy)    │
│ - snapshot_property (SCD2 snapshot: state-start)         │
│ - snapshot_suburb_lga (SCD2 snapshot: crosswalk)         │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼  (dbt Gold Models & Datamarts)
┌──────────────────────────────────────────────────────────┐
│ GOLD SCHEMA (PostgreSQL)                                 │
│ 1. Star Schema Dimensions:                               │
│    - dim_host, dim_property, dim_suburb, dim_lga         │
│ 2. Demographic Dimensions:                               │
│    - census_g01, census_g02                              │
│ 3. Kimball Fact Table:                                   │
│    - fact_listings (surrogate IDs and metrics ONLY)      │
│ 4. Datamart Views (Point-in-Time SCD2 Joins):            │
│    - dm_listing_neighbourhood (MoM growth, rev, active)  │
│    - dm_property_type (MoM pricing & capacity metrics)   │
│    - dm_host_neighbourhood (Host concentration metrics)  │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│ PART 4: AD-HOC SQL ANALYTICS                             │
│ - Q(a): Demographics in Top 3 vs Bottom 3 Revenue LGAs   │
│ - Q(b): Pearson Correlation Analysis (Median Age vs Rev) │
│ - Q(c): Optimal Property Configuration in Top 5 Suburbs  │
│ - Q(d): Host Portfolio Concentration Across LGAs         │
│ - Q(e): Single-Listing Hosts vs Annual Median Mortgages  │
└──────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
.
├── dags/
│   └── load_airbnb_census_dag.py       # Production Airflow DAG (portable: Docker + Composer)
├── data/                               # 12 monthly Airbnb CSVs & Census reference files
├── dbt_bde/
│   ├── dbt_project.yml                 # dbt project configuration
│   ├── profiles.yml                    # Postgres connection profiles (supports env vars)
│   ├── macros/
│   │   └── generate_schema_name.sql    # Custom schema naming (bronze/silver/gold)
│   ├── models/
│   │   ├── bronze/sources.yml          # dbt source declarations
│   │   ├── silver/stg_listings.sql     # Silver cleansed staging view
│   │   ├── gold/                       # Star schema dims, facts, and census
│   │   └── datamart/                   # 3 analytical business datamart views
│   ├── snapshots/                      # SCD Type 2 dimension snapshots
│   └── tests/                          # 5 custom business & data integrity tests (29 tests total)
├── dbt_submission_files.zip            # Clean submission archive (31 files: models, snapshots, tests, macros)
├── docker-compose.yml                  # Production Docker stack (Airflow 2.8.1 + Postgres 15)
├── reports/
│   ├── Assignment_3_Report_Aryan_Goel.docx  # Final Handover Report (academic styling, <2,500 words)
│   ├── README.md                       # Figures catalog
│   └── images/                         # Publication-quality charts, captures & ERDs
├── scripts/
│   ├── build_hd_report_docx.py         # Word report generator with verified empirical figures
│   ├── generate_report_diagrams.py     # High-resolution diagram and chart renderer
│   └── pipeline_runner.py              # CLI validation runner for all 4 parts
└── sql/
    ├── 00_init_postgres_users.sql      # Container database & user initialization
    ├── part_1.sql                      # Bronze schema DDL (also 01_create_bronze_schema.sql)
    ├── 01_create_bronze_schema.sql     # DDL script creating bronze, silver, gold schemas
    ├── part_4.sql                      # Part 4 ad-hoc analytical queries (Questions A to E)
    └── 02_ad_hoc_analysis.sql          # Ad-hoc analytical queries (Questions A to E mirror)
```

---

## Deliverables & Mark Allocation Mapping

| Brief Component | Implementation Summary | File Location |
| :--- | :--- | :--- |
| **Part 1: Airflow Ingestion** | Ingests initial month & reference datasets to Bronze with automated schema creation and lineage watermarks. | [`dags/load_airbnb_census_dag.py`](dags/load_airbnb_census_dag.py) |
| **Part 1: Bronze Schema** | Raw tables created via DDL absorbing schema drift as raw `TEXT`. | [`sql/part_1.sql`](sql/part_1.sql) |
| **Part 2: Medallion Architecture** | Cleaned staging view and 3 SCD Type 2 snapshots tracking history. | [`dbt_bde/models/silver/`](dbt_bde/models/silver/), [`dbt_bde/snapshots/`](dbt_bde/snapshots/) |
| **Part 2: Gold Star Schema** | Fact table strictly keys and metrics + 4 conformed dimensions + 2 Census tables. | [`dbt_bde/models/gold/`](dbt_bde/models/gold/) |
| **Part 2: 3 Datamart Views** | SCD2 point-in-time join logic calculating MoM rates, revenues, and occupancy. | [`dbt_bde/models/datamart/`](dbt_bde/models/datamart/) |
| **Part 3: Sequential Ingestion** | Chronological 12-month incremental ingestion with dbt snapshots and fact builds. | [`scripts/pipeline_runner.py`](scripts/pipeline_runner.py) |
| **Part 4: Ad-Hoc Analytics** | SQL answering questions (A) through (E) with statistical derivations. | [`sql/part_4.sql`](sql/part_4.sql) |
| **Full Written Report** | Handover report with 13 figures, 26 tables, and strictly <2,500 words. | [`reports/Assignment_3_Report_Aryan_Goel.docx`](reports/Assignment_3_Report_Aryan_Goel.docx) |
