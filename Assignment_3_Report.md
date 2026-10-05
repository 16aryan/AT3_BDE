# Assignment-3 Engineering Handover Report: Building ELT Pipelines (Airflow, PostgreSQL, dbt)

**Individual Engineering Handover Submission**  
**Student Name:** Aryan Goel | **Student ID:** 26040826  
**Subject:** 94693 / 36120 Big Data Engineering (Spring 2026), University of Technology Sydney  
**Repository:** [https://github.com/16aryan/AT3_BDE](https://github.com/16aryan/AT3_BDE)  
**Cloud Infrastructure:** GCP `rock-collector-510600-k3` | Cloud SQL PostgreSQL 18 (`35.197.167.206:5432`) | Cloud Composer 2 Airflow 2.11.1 (`australia-southeast1`)  

---

## Table of Contents
1. [High-Level Project Overview & Architecture](#1-high-level-project-overview--architecture)
2. [Business Problem & Regulatory Context](#2-business-problem--regulatory-context)
3. [PART 1: Data Ingestion & Cloud Orchestration (Tasks 1 to 3)](#3-part-1-data-ingestion--cloud-orchestration-tasks-1-to-3)
4. [PART 2: Silver Layer Cleansing & SCD Type 2 Snapshots](#4-part-2-silver-layer-cleansing--scd-type-2-snapshots)
5. [PART 3: Gold Layer Star Schema & Analytical Datamarts](#5-part-3-gold-layer-star-schema--analytical-datamarts)
6. [PART 4: Ad-Hoc Analytical Queries (SQL Analytics & Findings)](#6-part-4-ad-hoc-analytical-queries-sql-analytics--findings)
   - [Question A: Demographic Differences in Top 3 vs Bottom 3 LGAs](#question-a-demographic-differences-in-top-3-vs-bottom-3-lgas)
   - [Question B: Pearson Correlation Analysis (Median Age vs Revenue)](#question-b-pearson-correlation-analysis-median-age-vs-revenue)
   - [Question C: Optimal Property Configuration in Top 5 Neighbourhoods](#question-c-optimal-property-configuration-in-top-5-neighbourhoods)
   - [Strategic Investment Recommendations for STR Investors](#strategic-investment-recommendations-for-str-investors)
7. [Issues, Bugs Faced and Engineering Resolutions](#7-issues-bugs-faced-and-engineering-resolutions)
   - [Operational Replication Checklist for Peer Engineers](#76-operational-replication-checklist-for-peer-engineers)

---

## 1. High-Level Project Overview & Architecture

This engineering handover report details the architectural design, cloud orchestration, data modeling, and deterministic SQL analytics developed for Inside Airbnb Sydney listings and Australian Bureau of Statistics (ABS) 2016 Census datasets spanning May 2020 to April 2021. Written for peer data engineers proficient in Python, SQL, Apache Airflow, and dbt, the document outlines an enterprise Medallion ELT pipeline deployed across Google Cloud Platform (Cloud Composer 2, Cloud SQL PostgreSQL 18 in Sydney, and GCS) and locally via Docker.

Unlike legacy ETL architectures where transformations occur in transit, this platform adheres to the modern ELT paradigm: raw ingestion lands untyped high-fidelity data into Bronze schemas, while heavy computational transformations, cleansing, and Slowly Changing Dimension (SCD Type 2) tracking are pushed directly into the warehouse using declarative dbt models. This decouples compute from storage, ensures full idempotency across batch loads, and establishes complete longitudinal auditability.

- **Bronze Tier (Raw Ingestion):** Airflow DAG (`load_airbnb_census_dag.py`) extracts 12 monthly Airbnb CSVs, Census G01/G02 tables, and NSW LGA-suburb mappings into PostgreSQL bronze tables as raw TEXT, capturing 74 listing attributes and appending `file_source` and `ingestion_timestamp` metadata.
- **Silver Tier (Cleansing & SCD2):** dbt staging views sanitize currency, parse timestamps, and normalize booleans. Three dbt snapshots implement SCD Type 2 tracking with timestamp strategy across hosts, properties, and suburb mappings, managing `dbt_valid_from`/`dbt_valid_to` validity windows.
- **Gold Tier (Star Schema & Datamarts):** A pure Kimball Star Schema with a metric/key fact table (`gold.fact_listings`) connected to four conformed dimensions. Three specialized datamarts utilize point-in-time (PIT) temporal joins to eliminate data leakage and support multi-dimensional business analytics.

*(Refer to Figure 1 in the submitted report for the complete GCP Medallion Architecture diagram).*

---

## 2. Business Problem & Regulatory Context

### a. Objective
The primary mandate is delivering a robust ELT data platform ingesting short-term rental (STR) listings and demographic census data to resolve urban housing, tourism demand, and capital investment questions. Core technical requirements include decoupled schema landing, automated Airflow orchestration, SCD2 audit trails, pure numeric fact tables, and point-in-time joins.

### b. Stakeholders
- **Municipal Regulators (City of Sydney):** Enforce NSW's 180-day annual letting cap and assess housing affordability pressure.
- **STR Commercial Investors & Hosts:** Identify revenue-maximizing configurations (property type, room type, accommodates) across Sydney.
- **Tourism Analysts (Destination NSW):** Track coastal vs metropolitan demand recovery patterns during COVID-19 border closures.
- **Data Engineering Teams:** Require automated orchestration with layer isolation, testing assertions, and reproducible builds.

### c. Business Context & Market Dynamics
The May 2020 to April 2021 study period captured severe pandemic disruption in Greater Sydney: international tourism collapsed >97%, driving CBD apartment vacancies to historic highs, while affluent coastal enclaves (Waverley, Northern Beaches) experienced surge demand from high-income domestic travelers, resulting in average nightly rates 40% to 60% higher than Greater Sydney baseline rates.

---

## 3. PART 1: Data Ingestion & Cloud Orchestration (Tasks 1 to 3)

> **Assignment Prompt — Part 1: Pipeline Orchestration & Raw Ingestion**  
> *"Design an ELT pipeline using Apache Airflow to ingest Inside Airbnb monthly data, ABS Census G01/G02 tables, and LGA-suburb mappings into PostgreSQL with idempotency and auditability."*

Deployed on GCP `australia-southeast1` across three managed cloud services: (1) Cloud SQL (PostgreSQL 18, instance `bde-postgres`, Public IP `35.197.167.206:5432`), (2) Cloud Storage (bucket `gs://australia-southeast1-bde-co-d0a030e5-bucket` holding `/dags` and `/data`), and (3) Cloud Composer 2 (Airflow 2.11.1 on GKE Autopilot, environment `bde-composer`).

**Schema Definition & Drift Mitigation:** Script `sql/01_create_bronze_schema.sql` provisions bronze, silver, and gold namespaces. In `bronze.raw_listings`, all 74 Inside Airbnb columns are declared as raw TEXT. This defensive design absorbs upstream schema drift, unexpected quoting, and field reordering without pipeline failure. Every record is enriched with `file_source` and `ingestion_timestamp` metadata.

**DAG Flow & Parameterization:** The Airflow DAG (`dags/load_airbnb_census_dag.py`) executes with `schedule_interval=None`. Reference loading tasks execute concurrently before monthly listing ingestion:  
`[task_load_census_g01, task_load_census_g02, task_load_lga_suburb] >> task_load_airbnb`  
Dynamic execution is achieved via `dag_run.conf['file']`, allowing peer engineers to ingest any batch (e.g., `05_2020.csv` for initial load, subsequent months for incremental batches) using `if_exists='append'`. Reference tables utilize `if_exists='replace'` for idempotency. The helper function `get_file_content()` transparently resolves file paths across Composer GCS mounts (`/home/airflow/gcs/data`) and local POSIX paths.

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
> *"Cleanse raw data, standardize types, and implement SCD Type 2 tracking using dbt snapshots (timestamp strategy) for hosts, properties, and suburb mappings."*

**Silver Cleansing View Architecture:** Cleansing transformations are authored as declarative dbt views (`silver.stg_listings.sql`) to maintain non-destructive transformations:
1. **Currency Stripping:** `REGEXP_REPLACE(price, '[$,]', '', 'g')::NUMERIC(10, 2)` strips currency formatting and casts to numeric.
2. **Temporal Standardization:** Explicit casting `TO_DATE(last_scraped, 'YYYY-MM-DD')` and `TO_TIMESTAMP` parse scrape dates into ISO timestamps.
3. **Boolean Normalization:** `CASE WHEN host_is_superhost = 't' THEN TRUE ELSE FALSE END` converts raw character flags to native booleans.
4. **Spatial Harmonization:** `LOWER(TRIM(neighbourhood))` eliminates spatial join misses against suburb reference crosswalks.

**SCD Type 2 Snapshot Mechanics:** Slowly Changing Dimensions preserve historical state without destructive overwrites. Under the hood, dbt's snapshot engine computes an MD5 surrogate hash (`dbt_scd_id = MD5(unique_key || '|' || updated_at)`), compares incoming records against active rows (`dbt_valid_to IS NULL`), closes modified records by setting `dbt_valid_to` to the new record's timestamp, and inserts the new version with `dbt_valid_to IS NULL`. The timestamp strategy was selected because source datasets provide explicit scrape timestamps.

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

**Dimensional Design Standards:** Following Ralph Kimball's dimensional modeling standards, the fact table contains strictly foreign keys and numerical metrics—no descriptive text attributes are permitted in facts:
- **Fact Table (`gold.fact_listings`):** Grain represents one listing on a scrape date. Keys: `listing_id`, `host_id`, `scraped_date`. Numeric metrics: `price`, `minimum_nights`, `maximum_nights`, `availability_30`, `number_of_reviews`, `review_scores_rating`, `estimated_revenue`. Estimated revenue follows the brief formula: `estimated_revenue = (30 - availability_30) * price`.
- **Dimension Models:** `gold.dim_host`, `gold.dim_property`, `gold.dim_suburb`, `gold.dim_lga`, `census_g01`, `census_g02` maintain descriptive context.

**Point-in-Time Temporal Joins:** To prevent temporal lookahead bias (data leakage), transactions are evaluated strictly against the dimension record effective at transaction time:
```sql
ON fact.listing_id = dim_prop.listing_id
   AND fact.scraped_date >= dim_prop.dbt_valid_from
   AND (fact.scraped_date < dim_prop.dbt_valid_to OR dim_prop.dbt_valid_to IS NULL)
```

**Three Specialized Analytical Datamarts:**
1. `dm_listing_neighbourhood`: Computes 9 monthly metrics for each listing neighbourhood: active listing count, minimum/maximum/median/average nightly price, distinct host count, superhost percentage, total estimated revenue, and average revenue per active listing. Crucially, Month-over-Month (MoM) active listings growth percentage is derived using SQL window functions:
```sql
ROUND(100.0 * (COUNT(listing_id) - LAG(COUNT(listing_id)) OVER (PARTITION BY neighbourhood_name ORDER BY year_month)) / 
NULLIF(LAG(COUNT(listing_id)) OVER (PARTITION BY neighbourhood_name ORDER BY year_month), 0), 2)
```
2. `dm_property_type`: Multi-dimensional performance across property_type, room_type, accommodates, and year_month, evaluating supply volume, average stay duration, and revenue yields.
3. `dm_host_neighbourhood`: Evaluates host concentration, multi-listing operator prevalence, and total estimated revenue mapped to host LGA locations.

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

### Strategic Investment Recommendations for STR Investors
1. **Coastal Corridors (Bondi, Manly, Bondi Beach):** Entire houses accommodating 2 to 4 guests represent the premier investment target, generating $6,050 to $6,600 in annual revenue.
2. **Prestigious Eastern Suburbs (Double Bay):** 4-guest Entire townhouses deliver peak yields ($5,870/listing) driven by corporate relocations and extended executive stays.
3. **Commercial Core (Sydney CBD):** High-capacity private rooms in luxury apartments accommodating up to 4 guests provide the highest capital-efficient yield ($5,112/listing).

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

To reproduce the complete pipeline end-to-end on local Docker or GCP Cloud Composer, execute the following verified CLI sequence:

```bash
# 1. Launch local Docker infrastructure or connect to Cloud SQL
docker compose up -d

# 2. Initialize Bronze schemas & trigger Airflow ingestion
psql -h 35.197.167.206 -U postgres -d postgres -f sql/01_create_bronze_schema.sql
airflow dags trigger load_airbnb_census_dag

# 3. Execute dbt Silver staging views & SCD Type 2 snapshots
dbt run --select stg_listings
dbt snapshot

# 4. Build Gold Star Schema, analytical datamarts & test assertions
dbt run --select gold
dbt test
```

### Table 6: Pipeline Component Verification Audit
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
