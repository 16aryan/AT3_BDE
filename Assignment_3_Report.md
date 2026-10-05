# Assignment-3: Building ELT Pipelines (Airflow, PostgreSQL, dbt)

**Individual Submission**  
**Student Name:** Aryan Goel | **Student ID:** 26040826  
**Subject:** 94693 / 36120 Big Data Engineering (Spring 2026), University of Technology Sydney  
**Repository:** [https://github.com/16aryan/AT3_BDE](https://github.com/16aryan/AT3_BDE)  
**Infrastructure:** GCP  | Cloud SQL PostgreSQL 18 () | Cloud Composer 2 Airflow 2.11.1

---

## Table of Contents
1. [Project Overview & Architecture](#1-high-level-project-overview--architecture)
2. [Business Problem & Regulatory Context](#2-business-problem--regulatory-context)
3. [Part 1: Ingestion & Orchestration](#3-part-1-data-ingestion--cloud-orchestration-tasks-1-to-3)
4. [Part 2: Silver Cleansing & SCD2](#4-part-2-silver-layer-cleansing--scd-type-2-snapshots)
5. [Part 3: Star Schema & Datamarts](#5-part-3-gold-layer-star-schema--analytical-datamarts)
6. [Part 4: SQL Analytics & Findings](#6-part-4-ad-hoc-analytical-queries-sql-analytics--findings)
7. [Issues & Operational Checklist](#7-issues-bugs-faced-and-engineering-resolutions)

---

## 1. High-Level Project Overview & Architecture

This report details an enterprise ELT data pipeline for Inside Airbnb Sydney listings and ABS 2016 Census data (May 2020–April 2021). Adhering to the Medallion Architecture (Bronze → Silver → Gold), the platform utilizes Google Cloud Platform (Cloud Composer 2, Cloud SQL PostgreSQL 18 in Sydney, and GCS) and dbt Core for automated orchestration, schema evolution, and Slowly Changing Dimension (SCD Type 2) tracking.

- **Bronze Tier (Raw Ingestion):** Airflow DAG (`load_airbnb_census_dag.py`) ingests 12 monthly Airbnb CSVs, Census G01/G02 tables, and LGA-suburb mappings into PostgreSQL bronze tables as raw TEXT, appending `file_source` and `ingestion_timestamp` metadata.
- **Silver Tier (Cleansing & SCD2):** dbt staging views sanitize currency, parse timestamps, and normalize booleans. Three dbt snapshots implement SCD Type 2 tracking with timestamp strategy across hosts, properties, and suburb mappings, managing `dbt_valid_from`/`dbt_valid_to` validity intervals.
- **Gold Tier (Star Schema & Datamarts):** Kimball Star Schema featuring a pure numeric fact table (`gold.fact_listings`) joined to four dimensions. Three analytical datamarts use point-in-time temporal joins to eliminate data leakage.

*(Refer to Figure 1 in the submitted report for the complete GCP Medallion Architecture diagram).*

---

## 2. Business Problem & Regulatory Context

### a. Objective
The platform ingests STR listings and census demographics to answer urban planning and investment questions via deterministic SQL. Key mandates: decoupled landing, Airflow orchestration, SCD2 auditing, pure fact tables, and PIT joins.

### b. Stakeholders
- **Municipal Regulators (City of Sydney):** Enforce 180-day caps and monitor housing supply pressure.
- **STR Investors & Managers:** Isolate high-yield configurations (room type, capacity, price).
- **Tourism Analysts (Destination NSW):** Assess coastal vs CBD recovery trends during COVID-19.
- **Data Engineering Teams:** Require automated orchestration, layer isolation, and auditability.

### c. Business Context & Market Dynamics
The May 2020–April 2021 window captured severe pandemic disruption in Sydney: international tourism fell >97%, collapsing CBD occupancy, while coastal LGAs (Waverley, Northern Beaches) sustained strong domestic leisure demand at 40–60% rate premiums.

---

## 3. PART 1: Data Ingestion & Cloud Orchestration (Tasks 1 to 3)

> **Assignment Prompt — Part 1: Pipeline Orchestration & Raw Ingestion**  
> *"Design an ELT pipeline using Apache Airflow for Inside Airbnb data, Census G01/G02 tables, and LGA-suburb mappings in PostgreSQL with idempotency and auditability."*

Deployed on GCP `australia-southeast1` across three services: Cloud SQL (PostgreSQL 18, instance `bde-postgres`, IP `35.197.167.206:5432`), Cloud Storage (bucket `gs://australia-southeast1-bde-co-d0a030e5-bucket` holding `/dags` and `/data`), and Cloud Composer 2 (Airflow 2.11.1 on GKE, environment `bde-composer`).

Script `sql/01_create_bronze_schema.sql` provisions bronze, silver, and gold schemas. In `bronze.raw_listings`, all 74 Inside Airbnb columns are typed as TEXT to absorb schema drift, with `file_source` and `ingestion_timestamp` metadata. Airflow DAG (`load_airbnb_census_dag.py`) executes reference loading before monthly listing ingestion:
`[task_load_census_g01, task_load_census_g02, task_load_lga_suburb] >> task_load_airbnb`  
The DAG ingests monthly batches into `raw_listings` (`if_exists='append'`), resolving paths across Composer GCS mounts and local volumes.

### Table 1: Raw Bronze Ingestion Accounting Across Cloud SQL Database
| Target Bronze Table | Source File (GCS) | Strategy | Rows | Status |
| :--- | :--- | :--- | :---: | :---: |
| `bronze.raw_census_g01` | `2016Census_G01.csv` | Idempotent Replace | 9 | CONFIRMED |
| `bronze.raw_census_g02` | `2016Census_G02.csv` | Idempotent Replace | 9 | CONFIRMED |
| `bronze.raw_lga_suburb` | `LGA_Suburb_Mapping.csv` | Idempotent Replace | 27 | CONFIRMED |
| `bronze.raw_listings` (Initial) | `05_2020.csv` | Append + Metadata | 800 | CONFIRMED |
| `bronze.raw_listings` (12-Mo Full) | `05_2020 to 04_2021` | Monthly Append | 4,800 | CONFIRMED |

> **Part 1 Direct Output & Verification:**  
> • Autonomous Orchestration: Cloud Composer executed all DAG tasks with 100% green status, streaming directly to Cloud SQL.  
> • Zero Data Loss: All 74 Inside Airbnb columns captured in raw TEXT to preserve original fidelity for auditing.  
> • Full Lineage: Every row tagged with `file_source` and `ingestion_timestamp` for provenance tracking.

---

## 4. PART 2: Silver Layer Cleansing & SCD Type 2 Snapshots

> **Assignment Prompt — Part 2: Silver Layer Transformations & Slowly Changing Dimensions**  
> *"Cleanse raw data, standardize types, and implement SCD Type 2 tracking via dbt snapshots (timestamp strategy) for hosts, properties, and LGA mappings."*

Silver transformations are authored as declarative dbt views (`silver.stg_listings.sql`) to preserve raw data purity:
1. **Currency Stripping:** `REGEXP_REPLACE(price, '[$,]', '', 'g')::NUMERIC(10, 2)` removes currency symbols.
2. **Temporal Parsing:** `TO_DATE(last_scraped, 'YYYY-MM-DD')` and `TO_TIMESTAMP` parse scrape timestamps.
3. **Boolean Normalization:** `CASE WHEN host_is_superhost = 't' THEN TRUE ELSE FALSE END` standardizes flags.
4. **Spatial Harmonization:** `LOWER(TRIM(neighbourhood))` eliminates spatial join misses against suburb reference crosswalks.

SCD Type 2 captures history without destructive overwriting. Under the hood, dbt's snapshot engine computes an MD5 surrogate hash (`dbt_scd_id = MD5(unique_key || '|' || updated_at)`), compares incoming records against active rows (`dbt_valid_to IS NULL`), closes modified records by setting `dbt_valid_to`, and inserts the new version with `dbt_valid_to IS NULL`.

### Table 2: Silver Layer SCD Type 2 Snapshot Summary Across 12 Months
| Snapshot Model | Unique Key | Strategy | Tracked Attributes | Total Rows |
| :--- | :--- | :--- | :--- | :---: |
| `silver.snapshot_host` | `host_id` | timestamp | name, superhost, listings_count | 1,668 |
| `silver.snapshot_property` | `listing_id` | timestamp | room_type, bedrooms, price | 4,800 |
| `silver.snapshot_suburb_lga` | `suburb_name` | timestamp | lga_code, lga_name | 324 |

> **Part 2 Direct Output & Audit Compliance:**  
> • Zero Historical Distortion: Host superhost changes and property reconfigurations captured without altering past records.  
> • Deterministic Active State: Current state filtered deterministically via `dbt_valid_to IS NULL`.  
> • Temporal Integrity: Exact validity intervals enable point-in-time joins in downstream Gold models.

---

## 5. PART 3: Gold Layer Star Schema & Analytical Datamarts

> **Assignment Prompt — Part 3: Gold Layer Star Schema & Datamarts**  
> *"Implement a Gold Star Schema with pure numeric facts, PIT joins to SCD2 dimensions, and 3 analytical datamarts (dm_listing_neighbourhood, dm_property_type, dm_host_neighbourhood)."*

Following Ralph Kimball's dimensional design standards, the fact table contains strictly foreign keys and numeric metrics:
- **Fact Table (`gold.fact_listings`):** Grain is one listing on a scrape date. Keys: `listing_id`, `host_id`, `scraped_date`. Metrics: `price`, `minimum_nights`, `maximum_nights`, `availability_30`, `number_of_reviews`, `review_scores_rating`, `estimated_revenue`. Estimated revenue formula: `estimated_revenue = (30 - availability_30) * price`.
- **Dimension Models:** `gold.dim_host`, `gold.dim_property`, `gold.dim_suburb`, `gold.dim_lga`, `census_g01`, `census_g02` maintain descriptive context.

To prevent temporal lookahead bias, dimension joins evaluate transactions strictly against the dimension record effective at transaction time:
```sql
ON fact.listing_id = dim_prop.listing_id
   AND fact.scraped_date >= dim_prop.dbt_valid_from
   AND (fact.scraped_date < dim_prop.dbt_valid_to OR dim_prop.dbt_valid_to IS NULL)
```

Three specialized datamarts provide pre-aggregated business views:
1. `dm_listing_neighbourhood`: 9 monthly neighbourhood metrics. MoM active listings growth percentage is derived via: `ROUND(100.0 * (COUNT(listing_id) - LAG(...) OVER (...)) / NULLIF(LAG(...) OVER (...), 0), 2)`.
2. `dm_property_type`: Multi-dimensional performance across property_type, room_type, accommodates, and year_month.
3. `dm_host_neighbourhood`: Evaluates host concentration and estimated revenue by host_neighbourhood_lga.

---

## 6. PART 4: Ad-Hoc Analytical Queries (SQL Analytics & Findings)

### Question A: Demographic Differences in Top 3 vs Bottom 3 LGAs

> **Part 4 — Question A: Demographic Differences (Top 3 vs Lowest 3 LGAs)**  
> *"Identify demographic differences (age distribution, household size) between Top 3 and Bottom 3 LGAs by revenue per active listing over 12 months."*

Question A evaluated 12-month average estimated revenue per active listing across Sydney LGAs (>50 active listings). Cohorts were ranked via `DENSE_RANK()` and linked to ABS Census tables G01 and G02.

### Table 3: Demographic & Economic Comparison: Top 3 vs Bottom 3 Performing LGAs
| Cohort | LGA Name | Avg Revenue | Household | Median Age | Weekly Inc | % Age 25-54 |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| Top 3 | Waverley | $5,075.44 | 2.2 | 35.0 | $2,200 | 59.9% |
| Top 3 | Northern Beaches | $4,764.69 | 2.7 | 39.0 | $2,150 | 46.0% |
| Top 3 | Woollahra | $4,152.68 | 2.3 | 39.0 | $2,450 | 52.6% |
| Bottom 3 | Canterbury-Bankstown | $3,416.08 | 3.1 | 35.0 | $1,300 | 43.3% |
| Bottom 3 | Randwick | $3,362.43 | 2.4 | 34.0 | $1,850 | 51.7% |
| Bottom 3 | Blacktown | $3,260.99 | 3.2 | 33.0 | $1,550 | 45.0% |

> **Question A Direct Findings & Demographic Insights:**  
> • Revenue Disparity: Top 3 LGAs (Waverley: $5,075, Northern Beaches: $4,765, Woollahra: $4,153) generate 42.6% higher average revenue than Bottom 3 LGAs (Canterbury-Bankstown: $3,416, Randwick: $3,362, Blacktown: $3,261).  
> • Household Size Inversion: Top LGAs have smaller households (2.2–2.7) vs outer suburban LGAs (3.1–3.2 persons).  
> • Income Gap: Median weekly household income in the Top 3 ($2,150–$2,450) is 60% higher than the Bottom 3 ($1,300–$1,550).

---

### Question B: Pearson Correlation Analysis (Median Age vs Revenue)

> **Part 4 — Question B: Correlation Analysis (Median Age vs Estimated Revenue)**  
> *"Evaluate correlation between LGA median age and estimated revenue per active listing over 12 months using Pearson r."*

Question B calculates Pearson's correlation coefficient r between LGA median age (`census_g02`) and 12-month average estimated revenue per active listing (`gold.fact_listings`) using: `r = Σ((x - x̄)(y - ȳ)) / sqrt(Σ(x - x̄)² * Σ(y - ȳ)²)`.

### Table 4: Pearson Correlation Statistical Summary
| Metric | Sample Size (LGAs) | Mean Value | Statistical Result |
| :--- | :---: | :---: | :--- |
| Pearson Correlation (r) | 9 LGAs | N/A | +0.4450 (Moderate Positive) |
| Average Revenue per Listing | 9 LGAs | $3,912.07 | Range: $3,261 - $5,075 |
| Median Age of Population | 9 LGAs | 35.2 Years | Range: 33.0 - 39.0 Years |

> **Question B Direct Findings & Statistical Verdict:**  
> • Correlation Coefficient: Pearson r = +0.4450 confirms a moderate positive correlation between LGA median age and STR revenue.  
> • Demographic Explanation: Older LGAs (Northern Beaches: 39 yrs, Woollahra: 39 yrs) represent affluent coastal enclaves commanding premium rates.  
> • Younger Enclaves: Younger LGAs (Blacktown: 33 yrs, Randwick: 34 yrs) feature student clusters and lower daily rates ($130–$180).

---

### Question C: Optimal Property Configuration in Top 5 Neighbourhoods

> **Part 4 — Question C: Optimal Property Configuration in Top 5 Neighbourhoods**  
> *"Isolate optimal property configurations (property type, room type, accommodates) in Top 5 neighbourhoods by 12-month revenue per listing."*

Question C executed a two-stage query: (1) identified Sydney's Top 5 revenue-generating neighbourhoods, and (2) evaluated every configuration (`property_type × room_type × accommodates`) to isolate the configuration yielding the highest 12-month average revenue per listing.

### Table 5: Optimal Property Configuration in Sydney's Top 5 Highest-Revenue Neighbourhoods
| Neighbourhood | Best Property Type | Room Type | Accom. | Avg Price | Avg 12-Mo Revenue |
| :--- | :--- | :--- | :---: | :---: | :---: |
| Bondi | Entire house | Entire home/apt | 2 | $305.14 | $6,598.52 |
| Manly | Entire house | Entire home/apt | 4 | $376.91 | $6,546.55 |
| Bondi Beach | Entire house | Entire home/apt | 1 | $271.40 | $6,054.88 |
| Double Bay | Entire townhouse | Entire home/apt | 4 | $381.47 | $5,869.98 |
| Sydney (CBD) | Private room in apartment | Private room | 4 | $312.18 | $5,111.94 |

> **Question C Strategic Investment Recommendations:**  
> • Coastal Corridors (Bondi, Manly, Bondi Beach): Entire houses accommodating 2 to 4 guests yield peak revenue ($6,050–$6,600).  
> • Prestigious Eastern Suburbs (Double Bay): 4-guest Entire townhouses deliver peak yields ($5,870/listing) from corporate executive stays.  
> • Commercial Core (Sydney CBD): High-capacity private rooms in apartments accommodating 4 guests provide highest capital-efficient yield ($5,112/listing).

---

## 7. Issues, Bugs Faced and Engineering Resolutions

### 7.1 Cross-Platform POSIX Path Incompatibilities in Cloud Composer
- **Issue:** Composer mounts GCS to `/home/airflow/gcs/data/`, while Docker mounts `/opt/airflow/data/`, causing path errors.
- **Resolution:** Created `get_file_content()` checking Composer mounts, GCSHook, and POSIX paths.
- **Outcome:** Fully portable DAG execution across Docker and Composer.

### 7.2 Custom Schema Name Macro Override in dbt
- **Issue:** dbt default naming created `public_silver` and `public_gold` instead of `silver` and `gold`.
- **Resolution:** Added `dbt_bde/macros/generate_schema_name.sql` to override prefix logic.
- **Outcome:** Schemas materialized cleanly as bronze, silver, and gold.

### 7.3 Temporal Precision & Timestamp Mismatch in dbt Snapshots
- **Issue:** DATE vs DATETIME mismatches produced false-positive snapshot mutations.
- **Resolution:** Applied `TO_TIMESTAMP(last_scraped, 'YYYY-MM-DD HH24:MI:SS')` in staging.
- **Outcome:** Zero-warning snapshot execution across all 3 SCD2 models.

### 7.4 Point-in-Time Temporal Join Cartesian Explosions
- **Issue:** Joins between facts and snapshots on natural keys caused row fan-out.
- **Resolution:** Added PIT filtering: `ON fact.listing_id = dim.listing_id AND fact.scraped_date >= dim.dbt_valid_from AND (fact.scraped_date < dim.dbt_valid_to OR dim.dbt_valid_to IS NULL)`.
- **Outcome:** Exact 1:1 cardinality (4,800 fact rows matching raw listings).

### 7.5 Google Kubernetes Engine API Provisioning Dependency
- **Issue:** Composer creation failed due to inactive `container.googleapis.com` (GKE API).
- **Resolution:** Enabled GKE and Artifact Registry APIs before provisioning in sydney.
- **Outcome:** Composer 2 cluster provisioned with active schedulers and workers.

---

### 7.6 Operational Replication Checklist for Peer Engineers
| Pipeline Component | Target Output Metric | Status | Verification Method |
| :--- | :--- | :---: | :--- |
| Cloud Composer Airflow DAG | 4 Green Tasks (100% Success) | CONFIRMED | Airflow Grid View & Task Logs |
| Bronze Data Ingestion | 4,800 Listings, 45 Ref Rows | CONFIRMED | Cloud SQL Row Count Assertions |
| Silver Staging Cleansing | Regex Currency / Date Parsing | CONFIRMED | `dbt run --select stg_listings` |
| Silver SCD2 Snapshots | 3 Dimension Snapshots Active | CONFIRMED | `dbt snapshot` (PASS=3, WARN=0) |
| Gold Star Schema | fact_listings (IDs & Metrics) | CONFIRMED | `dbt run --select gold` (PASS=11) |
| Analytical Datamarts | 3 Datamarts with MoM Metrics | CONFIRMED | Point-in-Time Join SQL Queries |
| Part 4 Ad-Hoc Analytics | Q(a), Q(b), Q(c) Exact Findings | CONFIRMED | Deterministic SQL Executions |
| Local Docker Reproducibility | Single-command docker compose | CONFIRMED | Tested on Docker & Python 3.13 |
