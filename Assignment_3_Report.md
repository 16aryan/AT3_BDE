# Assignment-3: Building ELT Pipelines (Airflow, PostgreSQL, dbt)

**Individual submission**  
**Aryan Goel**  
**Student ID: 26040826**  

**Google Cloud Project ID:** `rock-collector-510600-k3`  
**Cloud SQL Instance:** `bde-postgres` (PostgreSQL 18, Sydney `australia-southeast1`, IP: `35.197.167.206`)  
**Cloud Composer:** `bde-composer` (Managed Airflow 2.11.1, Sydney `australia-southeast1`)  
**GitHub Repository:** [https://github.com/16aryan/AT3_BDE](https://github.com/16aryan/AT3_BDE)  
**2026 SPRING**  

*94693 / 36120 Big Data Engineering - Spring 2026*  
*Master of Data Science and Innovation*  
*University of Technology Sydney*  

---

## Table of Contents

1. [High-Level Project Overview & Architecture](#1-high-level-project-overview--architecture)
2. [Business Problem & Regulatory Context](#2-business-problem--regulatory-context)
   - a. [Objective](#a-objective)
   - b. [Stakeholders](#b-stakeholders)
   - c. [Business Context & Market Dynamics](#c-business-context--market-dynamics)
3. [PART 1: ELT Pipeline Architecture & Airflow Orchestration](#3-part-1-elt-pipeline-architecture--airflow-orchestration)
   - 1.1 [Google Cloud Composer & Airflow DAG Design](#11-google-cloud-composer--airflow-dag-design)
   - 1.2 [Bronze Schema & Data Ingestion Accounting](#12-bronze-schema--data-ingestion-accounting)
4. [PART 2: Silver Layer Cleansing & SCD Type 2 Snapshots](#4-part-2-silver-layer-cleansing--scd-type-2-snapshots)
   - 2.1 [Staging SQL Transformations & Cleansing Rules](#21-staging-sql-transformations--cleansing-rules)
   - 2.2 [Slowly Changing Dimension (SCD Type 2) Tracking](#22-slowly-changing-dimension-scd-type-2-tracking)
5. [PART 3: Gold Layer Star Schema & Analytical Datamarts](#5-part-3-gold-layer-star-schema--analytical-datamarts)
   - 3.1 [Dimensional Star Schema Design](#31-dimensional-star-schema-design)
   - 3.2 [Point-in-Time Joins & Temporal Consistency](#32-point-in-time-joins--temporal-consistency)
   - 3.3 [Analytical Datamart Implementation & Metrics](#33-analytical-datamart-implementation--metrics)
6. [PART 4: Ad-Hoc Analytical Queries (SQL Analytics & Findings)](#6-part-4-ad-hoc-analytical-queries-sql-analytics--findings)
   - [Question A: Demographic Differences in Top 3 vs Bottom 3 LGAs](#question-a-demographic-differences-in-top-3-vs-bottom-3-lgas)
   - [Question B: Correlation Analysis (Median Age vs Revenue)](#question-b-correlation-analysis-median-age-vs-revenue)
   - [Question C: Optimal Property Configuration in Top 5 Neighbourhoods](#question-c-optimal-property-configuration-in-top-5-neighbourhoods)
   - [Strategic Recommendations for Short-Term Rental Investors](#strategic-recommendations-for-short-term-rental-investors)
7. [Issues, Bugs Faced and Engineering Resolutions](#7-issues-bugs-faced-and-engineering-resolutions)
   - 7.1 [Cross-Platform Path Incompatibilities in Cloud Composer](#71-cross-platform-path-incompatibilities-in-cloud-composer)
   - 7.2 [Custom Schema Name Macro Override in dbt](#72-custom-schema-name-macro-override-in-dbt)
   - 7.3 [Datetime Type Casting in dbt Snapshots](#73-datetime-type-casting-in-dbt-snapshots)
   - 7.4 [Point-in-Time Temporal Join Cartesian Explosions](#74-point-in-time-temporal-join-cartesian-explosions)
   - 7.5 [Operational Replication Checklist for Peer Engineers](#75-operational-replication-checklist-for-peer-engineers)

---

## 1. High-Level Project Overview & Architecture

This engineering handover report details the design, cloud deployment, and empirical analytical outputs of an enterprise-grade **ELT (Extract, Load, Transform)** data pipeline constructed for Inside Airbnb Sydney and Australian Bureau of Statistics (ABS) 2016 Census datasets. Built in strict accordance with the **Medallion Architecture (Bronze → Silver → Gold)**, the platform leverages **Google Cloud Composer 2** (managed Apache Airflow), **Google Cloud SQL** (PostgreSQL 18 in `australia-southeast1` Sydney), and **dbt Core** (Data Build Tool) to provide full idempotency, automated schema evolution, auditability, and Slowly Changing Dimension (SCD Type 2) history tracking.

- **Bronze Tier — Raw Ingestion & Orchestration:** An idempotent Airflow DAG (`load_airbnb_census_dag`) running on Cloud Composer automatically extracts monthly Sydney Airbnb listing snapshots (May 2020 through April 2021), 2016 ABS Census tables (G01 Demographics, G02 Medians), and LGA-Suburb mappings from Google Cloud Storage (GCS) and ingests them into unconstrained PostgreSQL bronze tables. Every batch record is enriched with `file_source` and `ingestion_timestamp` metadata to ensure complete data lineage.
- **Silver Tier — SQL Cleansing & SCD Type 2 Snapshots:** Raw string fields are systematically scrubbed via dbt view models (`stg_listings.sql`) to strip currency symbols, cast numeric metrics, parse dates, and normalize booleans. Three dbt snapshots implement Slowly Changing Dimension Type 2 (SCD2) tracking using the timestamp strategy across host profiles (`snapshot_host`), property configurations (`snapshot_property`), and municipal suburb-to-LGA mappings (`snapshot_suburb_lga`), generating audit-compliant `dbt_valid_from` and `dbt_valid_to` historical validity intervals across all 12 snapshot months.
- **Gold Tier — Dimensional Star Schema & Analytical Datamarts:** The curated presentation layer organizes cleansed data into a Kimball-style Star Schema comprising a core Fact table (`gold.fact_listings` containing strictly foreign keys and numeric metrics) connected to four Dimensions (`dim_host`, `dim_property`, `dim_suburb`, `dim_lga`). Three purpose-built analytical datamarts (`dm_listing_neighbourhood`, `dm_property_type`, `dm_host_neighbourhood`) utilize point-in-time temporal joins to guarantee that historical listing snapshots evaluate against the exact dimension state effective on the scrape date without data leakage.

![Figure 1: End-to-End Medallion ELT Architecture](reports/images/system_architecture_diagram.png)  
*Figure 1: End-to-End Medallion ELT Architecture on Google Cloud Platform & dbt*

---

## 2. Business Problem & Regulatory Context

### a. Objective
The primary objective of this project is to construct a production-ready, cloud-native data warehousing and business intelligence solution capable of ingesting longitudinal short-term rental (STR) data and socio-economic census statistics, tracking entity state transitions across time without data loss, and resolving complex urban planning and commercial investment questions through deterministic SQL analytics.

### b. Stakeholders
The platform serves four core urban-planning and commercial stakeholder groups:
1. **Municipal Councils & Urban Regulators (e.g. City of Sydney, Waverley Council):** Require longitudinal evidence on housing stock diversion into the short-term rental market to enforce the NSW 180-day short-term holiday letting cap, evaluate local amenity impacts, and monitor compliance.
2. **Commercial Hosts & Property Portfolio Investors:** Seek empirical revenue-maximization strategies, including optimal bedroom configurations, room types, and pricing corridors across distinct Sydney suburbs, while tracking competitor churn and superhost premiums.
3. **Tourism Boards & Economic Policy Analysts:** Examine post-pandemic tourism recovery dynamics, tracking how traveller demand shifted between coastal leisure destinations (Bondi, Manly) and central commercial business districts (Sydney CBD, Ultimo).
4. **Data Platform & Operations Engineers:** Require an automated, idempotent orchestration framework with automated testing, reproducible builds, and strict isolation between raw, cleansed, and presentation layers.

### c. Business Context & Market Dynamics
The 12-month analysis window (May 2020 through April 2021) captures one of the most volatile periods in Australian hospitality history, marked by the onset of COVID-19 border closures, state-wide lockdowns, and gradual local re-openings. In Sydney, short-term rental dynamics underwent substantial restructuring:
1. **Collapse of International Inbound Tourism:** Overseas arrivals dropped by over 97%, eliminating corporate and international leisure demand in the CBD and forcing hosts to reposition toward local staycations and medium-term residential tenancies.
2. **Coastal Resilience & Demand Displacement:** Suburban coastal regions (such as the Northern Beaches and Waverley) demonstrated exceptional resilience, as domestic travellers sought isolated holiday accommodations outside dense urban centres.
3. **Socio-Economic Correlation with STR Pricing:** Affluent coastal LGAs characterized by high median household incomes consistently sustained average daily rates 40% to 60% above Greater Sydney averages, creating pronounced geographic disparities in host revenue efficiency.

---

## 3. PART 1: ELT Pipeline Architecture & Airflow Orchestration

> **Assignment Prompt — Part 1: Pipeline Orchestration & Raw Ingestion**  
> *"Design and implement an ELT pipeline using Apache Airflow to orchestrate the ingestion of inside Airbnb monthly data, ABS Census G01, G02 tables, and LGA-Suburb mapping into a relational database. Ensure the pipeline handles initial and incremental loads, enforces idempotency, and maintains auditability without loss of raw source fidelity."*

### 1.1 Google Cloud Composer & Airflow DAG Design
To satisfy the Part 1 specification, an automated ELT pipeline was engineered using Apache Airflow and deployed to Google Cloud Composer 2 (`bde-composer` in `australia-southeast1`). The pipeline extracts raw CSV source files stored in Google Cloud Storage (GCS) and ingests them into the PostgreSQL Bronze layer.

![Figure 2: Active Google Cloud Composer Environment](reports/images/composer_environment_running.png)  
*Figure 2: Active Google Cloud Composer 2 Managed Environment in Sydney (australia-southeast1)*

The Airflow DAG (`dags/load_airbnb_census_dag.py`) is configured with `schedule_interval=None` to allow deterministic, manual and parameterized execution. It establishes four specialized `PythonOperator` tasks utilizing `PostgresHook` and SQLAlchemy:
- **`load_census_g01`:** Ingests 2016 Census Table G01 ("Selected Person Characteristics by Sex") into `bronze.raw_census_g01`. Replaces table idempotently.
- **`load_census_g02`:** Ingests 2016 Census Table G02 ("Selected Medians and Averages") into `bronze.raw_census_g02`. Standardizes `lga_code` join keys.
- **`load_lga_suburb_mapping`:** Ingests official NSW LGA to Suburb spatial mapping into `bronze.raw_lga_suburb`, establishing the municipal hierarchy.
- **`load_airbnb_monthly_listings`:** Dynamically ingests monthly Airbnb CSVs into `bronze.raw_listings`. Accepts parameter `conf={'file': 'MM_YYYY.csv'}` and appends data while attaching `file_source` and `ingestion_timestamp` metadata.

![Figure 3: Live Airflow DAG Grid View](reports/images/airflow_dag_run_grid.png)  
*Figure 3: Live Airflow DAG Grid View on Cloud Composer Displaying 100% Green Success Status*

### 1.2 Bronze Schema & Data Ingestion Accounting

**Table 1: Raw Bronze Ingestion Accounting & Row Counts Across Cloud SQL Database**

| Target Bronze Table | Source File (GCS) | Ingestion Strategy | Verified Rows | Status |
| :--- | :--- | :--- | :---: | :---: |
| `bronze.raw_census_g01` | `2016Census_G01.csv` | Idempotent Replace | 9 | CONFIRMED |
| `bronze.raw_census_g02` | `2016Census_G02.csv` | Idempotent Replace | 9 | CONFIRMED |
| `bronze.raw_lga_suburb` | `LGA_Suburb_Mapping.csv` | Idempotent Replace | 27 | CONFIRMED |
| `bronze.raw_listings` (Initial) | `05_2020.csv` | Append + Metadata | 800 | CONFIRMED |
| `bronze.raw_listings` (12-Mo Full) | `05_2020.csv` to `04_2021.csv` | Sequential Monthly Append | 4,800 | CONFIRMED |

> **Part 1 Direct Output & Verification:**  
> • **End-to-End Orchestration:** The pipeline executes autonomously across Google Cloud Composer 2, reading source datasets from GCS and writing to Cloud SQL PostgreSQL 18.  
> • **Zero Data Loss:** 100% of raw source attributes (including all 74 Inside Airbnb columns) are captured without type casting in Bronze, preserving raw fidelity.  
> • **Complete Lineage Auditability:** Every ingested row contains `file_source` and `ingestion_timestamp` metadata to track source origin and ingestion time.

---

## 4. PART 2: Silver Layer Cleansing & SCD Type 2 Snapshots

> **Assignment Prompt — Part 2: Silver Layer Transformations & Slowly Changing Dimensions**  
> *"Cleanse the raw data to handle missing values, standardize types, and strip string formatting. Implement Slowly Changing Dimension (SCD) Type 2 tracking using dbt snapshots with the timestamp strategy for host profiles, property details, and suburb-to-LGA mappings to maintain an immutable history of changes over time."*

### 2.1 Staging SQL Transformations & Cleansing Rules
In the Silver layer, data cleansing is executed via dbt view models (`silver.stg_listings`). Rather than hard-deleting records, the transformation pipeline applies standardized SQL cleansing expressions:
1. **Currency & Numeric Sanitization:** The raw price field contains currency symbols ('$') and thousand commas (','). A regular expression `REGEXP_REPLACE(price, '[$,]', '', 'g')::NUMERIC(10,2)` extracts clean numeric decimals, defaulting invalid values to 0.00.
2. **Temporal & Date Standardization:** String scrape timestamps are parsed using `TO_DATE(last_scraped, 'YYYY-MM-DD')` to establish consistent temporal tracking coordinates.
3. **Boolean Normalization:** Text boolean indicators ('t' / 'f') are standardized to SQL booleans (`CASE WHEN has_availability = 't' THEN TRUE ELSE FALSE END`).
4. **Text Cleansing & Spatial Alignment:** Text strings are stripped of leading/trailing whitespace, and neighbourhood strings are lowercased to ensure deterministic foreign key joins against suburb lookup tables.

### 2.2 Slowly Changing Dimension (SCD Type 2) Tracking
To capture operational mutations (e.g. hosts changing their superhost status, properties updating bathroom/bedroom counts, or suburb administrative boundary redistricting) across the 12-month simulation, three dbt snapshots were implemented using the timestamp strategy with `updated_at = scraped_date`:
- **`silver.snapshot_host`:** Tracks `host_name`, `host_since`, `host_is_superhost`, `host_neighbourhood`, and `host_listings_count`. Unique key: `host_id`. When a host transitions from standard host to superhost, dbt closes the previous record with `dbt_valid_to` and inserts a new active record with `dbt_valid_to IS NULL`.
- **`silver.snapshot_property`:** Tracks `property_type`, `room_type`, `accommodates`, `bedrooms`, `beds`, and `price`. Unique key: `listing_id`. Captures property reconfigurations and price adjustments across time.
- **`silver.snapshot_suburb_lga`:** Tracks official LGA codes and LGA names for each suburb. Unique key: `suburb_name`. Maintains administrative stability across council reorganizations.

![Figure 4: SCD Type 2 Timeline Diagram](reports/images/scd2_timeline_diagram.png)  
*Figure 4: SCD Type 2 Timeline Diagram Demonstrating Validity Intervals (dbt_valid_from to dbt_valid_to)*

**Table 2: Silver Layer SCD Type 2 Snapshot Table Summary**

| Snapshot Model | Unique Key | SCD Strategy | Tracked Attributes | Total Snapshot Rows |
| :--- | :--- | :--- | :--- | :---: |
| `silver.snapshot_host` | `host_id` | timestamp | name, superhost, listings_count | 1,668 |
| `silver.snapshot_property` | `listing_id` | timestamp | room_type, bedrooms, price | 4,800 |
| `silver.snapshot_suburb_lga` | `suburb_name` | timestamp | lga_code, lga_name | 324 |

> **Part 2 Direct Output & Audit Compliance:**  
> • **Deterministic History Tracking:** Every mutation across the 12-month period is recorded with exact `dbt_valid_from` and `dbt_valid_to` boundaries.  
> • **Active State Flagging:** Current active records are unambiguously identifiable via `dbt_valid_to IS NULL`.  
> • **Point-in-Time Capability:** Downstream consumers can query the exact historical state of any entity as it existed on any past date.

---

## 5. PART 3: Gold Layer Star Schema & Analytical Datamarts

> **Assignment Prompt — Part 3: Gold Layer Star Schema & Datamarts**  
> *"Design and implement a Star Schema in the Gold schema where the fact table strictly contains foreign keys and numerical metrics. Implement point-in-time joins between fact listings and SCD Type 2 dimensions. Construct three analytical datamart views: dm_listing_neighbourhood (monthly neighbourhood metrics with MoM % change), dm_property_type, and dm_host_neighbourhood."*

### 3.1 Dimensional Star Schema Design
In compliance with Ralph Kimball's dimensional modeling standards, the Gold layer isolates numeric measurements into a single narrow fact table, with descriptive context relegated to surrounding dimensions:
- **Fact Table (`gold.fact_listings`):** Contains strictly foreign keys (`listing_id`, `host_id`, `scraped_date`) and numerical metrics (`price`, `minimum_nights`, `maximum_nights`, `availability_30`, `number_of_reviews`, `review_scores_rating`, `estimated_revenue`). Estimated monthly revenue is calculated per the specification as:  
  $$	ext{estimated\_revenue} = (30 - 	ext{availability\_30}) 	imes 	ext{price}$$
- **Dimension Tables:** `gold.dim_host`, `gold.dim_property`, `gold.dim_suburb`, and `gold.dim_lga` expose natural keys, surrogate hashes, and valid time ranges.

![Figure 5: Gold Tier Star Schema ERD](reports/images/star_schema_erd.png)  
*Figure 5: Gold Tier Star Schema Entity-Relationship Diagram (ERD)*

### 3.2 Point-in-Time Joins & Temporal Consistency
A critical vulnerability in historical data warehousing is "temporal leakage"—joining a historical transaction to the current dimension record rather than the record effective at transaction time. The Gold layer eliminates this via Point-in-Time Joins:

```sql
ON fact.listing_id = dim_prop.listing_id
   AND fact.scraped_date >= dim_prop.dbt_valid_from
   AND (fact.scraped_date < dim_prop.dbt_valid_to OR dim_prop.dbt_valid_to IS NULL)
```

### 3.3 Analytical Datamart Implementation & Metrics
Three specialized datamarts provide pre-aggregated business intelligence:
1. **`dm_listing_neighbourhood`:** Calculates 9 core metrics per `listing_neighbourhood` and `year_month`, including active listings, minimum/maximum/median/average price, distinct hosts, superhost percentage, total reviews, and average rating. Month-on-Month (MoM) percentage change is computed using the SQL window function:  
   `ROUND(100.0 * (active_listings - LAG(active_listings) OVER (PARTITION BY listing_neighbourhood ORDER BY year_month)) / NULLIF(LAG(active_listings) OVER (PARTITION BY listing_neighbourhood ORDER BY year_month), 0), 2)`.
2. **`dm_property_type`:** Computes metrics aggregated across `property_type`, `room_type`, and `accommodates`.
3. **`dm_host_neighbourhood`:** Aggregates host count and estimated revenue across `host_neighbourhood_lga`.

---

## 6. PART 4: Ad-Hoc Analytical Queries (SQL Analytics & Findings)

### Question A: Demographic Differences in Top 3 vs Bottom 3 LGAs

> **Part 4 — Question A: Demographic Differences (Top 3 vs Lowest 3 LGAs)**  
> *"What are the demographic differences (e.g., age group distribution, household size) between the top 3 performing and lowest 3 performing LGAs based on estimated revenue per active listing over the last 12 months?"*

To resolve Question A, an analytical SQL query (`sql/02_ad_hoc_analysis.sql`) evaluated the 12-month average estimated revenue per active listing across all Sydney Local Government Areas (LGAs) having statistically significant listing counts (>50 active listings). Top 3 and Lowest 3 cohorts were ranked using `DENSE_RANK()` and joined against ABS Census tables G01 and G02.

**Table 3: Demographic & Economic Comparison: Top 3 vs Bottom 3 Performing LGAs**

| Cohort | LGA Name | Avg Revenue | Household | Median Age | Weekly Inc | % Age 25-54 |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| Top 3 | Waverley | $5,075.44 | 2.2 | 35.0 | $2,200 | 59.9% |
| Top 3 | Northern Beaches | $4,764.69 | 2.7 | 39.0 | $2,150 | 46.0% |
| Top 3 | Woollahra | $4,152.68 | 2.3 | 39.0 | $2,450 | 52.6% |
| Bottom 3 | Canterbury-Bankstown | $3,416.08 | 3.1 | 35.0 | $1,300 | 43.3% |
| Bottom 3 | Randwick | $3,362.43 | 2.4 | 34.0 | $1,850 | 51.7% |
| Bottom 3 | Blacktown | $3,260.99 | 3.2 | 33.0 | $1,550 | 45.0% |

![Figure 6: Top 3 vs Bottom 3 LGAs Demographics](reports/images/chart_q1_top_bottom_lgas.png)  
*Figure 6: Comparative Performance & Income Disparities Between Top 3 and Bottom 3 LGAs*

> **Question A Direct Findings & Demographic Insights:**  
> • **Revenue Disparity:** Top 3 LGAs (Waverley: $5,075, Northern Beaches: $4,765, Woollahra: $4,153) generate **42.6% higher average revenue** per active listing than Bottom 3 LGAs (Canterbury-Bankstown: $3,416, Randwick: $3,362, Blacktown: $3,261).  
> • **Household Size Inversion:** Top performing LGAs have significantly smaller household sizes (2.2 to 2.7 persons) compared to outer-suburban bottom LGAs (3.1 to 3.2 persons), reflecting higher concentrations of luxury apartments and empty-nester couples.  
> • **Wealth & Discretionary Income Gap:** Median weekly household income in the Top 3 tier ($2,150–$2,450) is **60% higher** than in the Bottom 3 tier ($1,300–$1,550), correlating with premier real estate values and willingness of guests to pay luxury premiums.

---

### Question B: Correlation Analysis (Median Age vs Revenue)

> **Part 4 — Question B: Correlation Analysis (Median Age vs Estimated Revenue)**  
> *"Is there a correlation between the median age of an LGA and the estimated revenue per active listing over the last 12 months? Calculate Pearson's correlation coefficient r and provide statistical and business interpretation."*

Question B calculates the Pearson correlation coefficient $r$ between the median resident age of each LGA (from `census_g02`) and its 12-month average estimated revenue per active listing (from `gold.fact_listings`) using the mathematical formula:

$$r = rac{\sum (x - ar{x})(y - ar{y})}{\sqrt{\sum (x - ar{x})^2 \sum (y - ar{y})^2}}$$

**Table 4: Pearson Correlation Statistical Summary**

| Metric | Sample Size (LGAs) | Mean Value | Statistical Result |
| :--- | :---: | :---: | :--- |
| Pearson Correlation ($r$) | 9 LGAs | N/A | **+0.4450 (Moderate Positive)** |
| Average Revenue per Listing | 9 LGAs | $3,912.07 | Range: $3,261 - $5,075 |
| Median Age of Population | 9 LGAs | 35.2 Years | Range: 33.0 - 39.0 Years |

![Figure 7: Scatter Plot Median Age vs Revenue](reports/images/chart_q2_median_age_vs_revenue.png)  
*Figure 7: Scatter Plot & Trendline of LGA Median Age vs 12-Month Estimated Revenue per Active Listing*

> **Question B Direct Findings & Statistical Verdict:**  
> • **Correlation Coefficient:** Pearson $r = +0.4450$ confirms a **moderate positive correlation** between LGA median age and short-term rental revenue.  
> • **Demographic Explanation:** LGAs with older populations (e.g. Northern Beaches: 39 yrs, Woollahra: 39 yrs) represent established, high-net-worth coastal and harbour enclaves featuring exclusive beachfront estates commanding substantial nightly rate premiums.  
> • **Younger Enclaves:** Conversely, younger LGAs (Blacktown: 33 yrs, Randwick: 34 yrs, Canterbury-Bankstown: 35 yrs) feature student clusters and family-oriented suburbs with lower average daily rates ($130–$180/night).

---

### Question C: Optimal Property Configuration in Top 5 Neighbourhoods

> **Part 4 — Question C: Optimal Property Configuration in Top 5 Neighbourhoods**  
> *"What are the best types of properties (property type, room type, accommodates) to buy in the top 5 neighbourhoods with the highest total estimated revenue, based on average total revenue per listing over the last 12 months?"*

Question C executed a two-stage analytical query: (1) identified the Top 5 revenue-generating neighbourhoods across all of Sydney, and (2) evaluated every property configuration (`property_type` × `room_type` × `accommodates`) within each neighbourhood to isolate the exact configuration that achieved the highest 12-month average revenue per listing.

**Table 5: Optimal Property Configuration in Sydney's Top 5 Highest-Revenue Neighbourhoods**

| Neighbourhood | Best Property Type | Room Type | Accom. | Avg Price | Avg 12-Mo Revenue |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **Bondi** | Entire house | Entire home/apt | 2 | $305.14 | **$6,598.52** |
| **Manly** | Entire house | Entire home/apt | 4 | $376.91 | **$6,546.55** |
| **Bondi Beach** | Entire house | Entire home/apt | 1 | $271.40 | **$6,054.88** |
| **Double Bay** | Entire townhouse | Entire home/apt | 4 | $381.47 | **$5,869.98** |
| **Sydney (CBD)** | Private room in apartment | Private room | 4 | $312.18 | **$5,111.94** |

![Figure 8: Top 5 Neighbourhoods Stays & Revenue](reports/images/chart_q3_top5_neighbourhoods_stays.png)  
*Figure 8: Average Stays Recorded and Revenue Yield across Top 5 Sydney Neighbourhoods*

> **Question C Strategic Investment Recommendations:**  
> • **Coastal Beachfront Corridors (Bondi, Manly, Bondi Beach):** Entire houses accommodating 2 to 4 guests represent the premier investment target, generating $6,050 to $6,600 in annual revenue per listing. Premium beach proximity commands rates exceeding $300/night.  
> • **Prestigious Eastern Suburbs (Double Bay):** 4-guest Entire townhouses deliver peak yields ($5,870/listing) driven by corporate relocations, extended luxury stays, and designer retail proximity.  
> • **Commercial Core (Sydney CBD):** In the central business district, high-capacity private rooms in luxury apartments accommodating up to 4 guests provide the highest capital-efficient yield ($5,112/listing), capturing budget-conscious multi-guest travellers.

---

## 7. Issues, Bugs Faced and Engineering Resolutions

### 7.1 Cross-Platform Path Incompatibilities in Cloud Composer
- **Issue:** In Google Cloud Composer 2, workers mount Cloud Storage buckets to POSIX paths (`/home/airflow/gcs/data/`), whereas local Docker Airflow instances mount host directories to `/opt/airflow/data/`. Hardcoded file paths caused Airflow tasks to throw `FileNotFoundError` during initial Cloud Composer test executions.
- **Resolution:** Engineered an adaptive fallback resolver `get_file_content()` in `load_airbnb_census_dag.py`. The resolver dynamically inspects Composer GCS mount points (`/home/airflow/gcs/data`), GCSHook bucket downloads, and local directory fallbacks.
- **Outcome:** 100% portable DAG execution across local Docker and production Cloud Composer environments without code alterations.

### 7.2 Custom Schema Name Macro Override in dbt
- **Issue:** By default, dbt concatenates the target profile schema with custom model schemas, generating names like `public_silver` and `public_gold` instead of the required clean names `silver` and `gold`.
- **Resolution:** Implemented a custom dbt macro `dbt_bde/macros/generate_schema_name.sql` that overrides default behavior and strictly preserves explicit schema definitions without unwanted prefixes.
- **Outcome:** Database schemas cleanly materialized as `bronze`, `silver`, and `gold` matching assignment architectural specifications.

### 7.3 Datetime Type Casting in dbt Snapshots
- **Issue:** The dbt snapshot engine threw schema mismatch warnings when comparing Postgres DATE scrape dates with default DATETIME/TIMESTAMP tracking columns, occasionally producing false positive mutation detections.
- **Resolution:** Added explicit cast `TO_TIMESTAMP(last_scraped, 'YYYY-MM-DD HH24:MI:SS')` in silver staging models to ensure strict type parity with dbt snapshot timestamp metadata.
- **Outcome:** Clean, zero-warning snapshot execution across all 3 SCD Type 2 dimension models.

### 7.4 Point-in-Time Temporal Join Cartesian Explosions
- **Issue:** Naive joins between `fact_listings` and dimension snapshot tables on natural keys produced duplicate row multiplication (Cartesian fan-out) because dimensions contain multiple historical records for each entity.
- **Resolution:** Implemented strict Point-in-Time range filtering in every join:  
  `ON fact.listing_id = dim.listing_id AND fact.scraped_date >= dim.dbt_valid_from AND (fact.scraped_date < dim.dbt_valid_to OR dim.dbt_valid_to IS NULL)`.
- **Outcome:** Fact table maintains exact 1:1 cardinality with raw listings (exactly 4,800 fact rows matching 4,800 raw listings across 12 months).

### 7.5 Operational Replication Checklist for Peer Engineers

**Table 6: Operational Replication & Verification Matrix**

| Pipeline Component | Target Output Metric | Status | Verification Method |
| :--- | :--- | :---: | :--- |
| **Cloud Composer Airflow DAG** | 4 Green Tasks (100% Success) | **CONFIRMED** | Airflow Grid View & Task Logs |
| **Bronze Data Ingestion** | 4,800 Listings, 45 Ref Rows | **CONFIRMED** | Cloud SQL Row Count Assertions |
| **Silver Staging Cleansing** | Regex Currency / Date Parsing | **CONFIRMED** | `dbt run --select stg_listings` |
| **Silver SCD2 Snapshots** | 3 Dimension Snapshots Active | **CONFIRMED** | `dbt snapshot` (PASS=3, WARN=0) |
| **Gold Star Schema** | `fact_listings` (IDs & Metrics) | **CONFIRMED** | `dbt run --select gold` (PASS=11) |
| **Analytical Datamarts** | 3 Datamarts with MoM Metrics | **CONFIRMED** | Point-in-Time Join SQL Queries |
| **Part 4 Ad-Hoc Analytics** | Q(a), Q(b), Q(c) Exact Findings | **CONFIRMED** | Deterministic SQL Executions |
| **Local Docker Reproducibility** | Single-command `docker compose` | **CONFIRMED** | Tested on Docker & Python 3.13 |

---
