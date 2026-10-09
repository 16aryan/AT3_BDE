# Assignment-3 Engineering Handover Report: Building ELT Pipelines (Airflow, PostgreSQL, dbt)

**Individual Engineering Handover Submission**  
**Student Name:** Aryan Goel | **Student ID:** 26040826  
**Subject:** 94693 / 36120 Big Data Engineering (Spring 2026), University of Technology Sydney  
**Repository:** [https://github.com/16aryan/AT3_BDE](https://github.com/16aryan/AT3_BDE)  
**Environment:** Validated locally on Docker (PostgreSQL 15, Airflow 2.8.1, dbt Core 1.11); Deployed to GCP (Cloud Composer 2 Airflow 2.11, Cloud SQL PostgreSQL 18)  
**Dataset:** Course Authentic Inside Airbnb (412,122 rows across 12 monthly snapshots) & 2016 ABS Census  

---

## Table of Contents
1. [High-Level Project Overview & Architecture](#1-high-level-project-overview--architecture)
2. [Business Problem & Regulatory Context](#2-business-problem--regulatory-context)
3. [PART 1: Data Ingestion & Pipeline Orchestration (Tasks 1 to 3)](#3-part-1-data-ingestion--pipeline-orchestration-tasks-1-to-3)
4. [PART 2: Data Warehouse Design with dbt (Silver & Gold Layers)](#4-part-2-data-warehouse-design-with-dbt-silver--gold-layers)
5. [PART 3: Sequential Incremental Ingestion & Longitudinal Processing](#5-part-3-sequential-incremental-ingestion--longitudinal-processing)
6. [PART 4: Ad-Hoc Analytical Queries (SQL Analytics & Findings)](#6-part-4-ad-hoc-analytical-queries-sql-analytics--findings)
   - [Question A: Demographic Differences in Top 3 vs Bottom 3 LGAs](#question-a-demographic-differences-in-top-3-vs-bottom-3-lgas)
   - [Question B: Pearson Correlation Analysis (Median Age vs Revenue)](#question-b-pearson-correlation-analysis-median-age-vs-revenue)
   - [Question C: Optimal Property Configuration in Top 5 Neighbourhoods](#question-c-optimal-property-configuration-in-top-5-neighbourhoods)
   - [Question D: Host Portfolio Concentration Across LGAs](#question-d-host-portfolio-concentration-across-lgas)
   - [Question E: Single-Listing Hosts vs Annualised Median Mortgages](#question-e-single-listing-hosts-vs-annualised-median-mortgages)
7. [Issues, Bugs Faced and Engineering Resolutions](#7-issues-bugs-faced-and-engineering-resolutions)
   - [Operational Replication Checklist for Peer Engineers](#77-operational-replication-checklist-for-peer-engineers)

---

## 1. High-Level Project Overview & Architecture

This engineering handover report details the architectural design, orchestration, data modeling, and deterministic SQL analytics developed for Inside Airbnb Sydney listings and Australian Bureau of Statistics (ABS) 2016 Census datasets spanning May 2020 to April 2021 (412,122 listing records across 12 monthly snapshots). Written for peer data engineers, the document outlines an enterprise Medallion ELT pipeline operationalized across Docker and Google Cloud Platform.

Adhering to the modern ELT paradigm, raw ingestion lands untyped high-fidelity data directly into Bronze schemas, while transformations, cleansing, and Slowly Changing Dimension (SCD Type 2) tracking are pushed into the warehouse using declarative dbt models. This decouples compute from storage, ensures full idempotency across batch loads, and establishes complete longitudinal auditability.

- **Bronze Tier (Raw Ingestion):** Airflow DAG (`load_airbnb_census_dag.py`) extracts 12 monthly Airbnb CSVs, Census G01/G02 tables, and NSW LGA-suburb mappings into PostgreSQL bronze tables as raw TEXT, capturing 22 raw listing attributes and appending `file_source` and `ingestion_timestamp` metadata.
- **Silver Tier (Cleansing & SCD2):** dbt staging views sanitize currency strings, parse dates, and normalize property types. Three dbt snapshots implement SCD Type 2 tracking across properties (49,072 versions) and hosts (34,610 versions) dated from when each attribute state began, and suburb mappings (4,520 rows).
- **Gold Tier (Star Schema & Datamarts):** A pure Kimball Star Schema with a metric/key fact table (`gold.fact_listings`, 412,122 rows) connected to four conformed dimensions. Three specialized datamarts utilize point-in-time (PIT) temporal joins to eliminate data leakage and support multi-dimensional business analytics.

![Figure 1: End-to-End Medallion ELT Architecture](reports/images/system_architecture_diagram.png)

---

## 2. Business Problem & Regulatory Context

### a. Objective
The primary mandate is delivering a robust ELT data platform ingesting short-term rental (STR) listings and demographic census data to resolve urban housing, tourism demand, and capital investment questions. Core technical requirements include decoupled schema landing, automated Airflow orchestration, SCD2 audit trails, pure numeric fact tables, and point-in-time joins.

### b. Stakeholders
- **Municipal Regulators (City of Sydney):** Assess housing availability and evaluate short-term rental density across local neighbourhoods.
- **STR Commercial Investors & Hosts:** Identify revenue-maximizing configurations (property type, room type, accommodates) across Greater Sydney.
- **Tourism Analysts (Destination NSW):** Track coastal vs metropolitan demand recovery patterns during domestic travel shifts.
- **Data Engineering Teams:** Require automated orchestration with layer isolation, testing assertions, and reproducible builds.

### c. Business Context & Market Dynamics
The May 2020 to April 2021 study period captured substantial shifts across Greater Sydney: metropolitan CBD listings experienced decreased occupancy, while affluent coastal and harbour enclaves (Waverley, Northern Beaches, Mosman) saw sustained domestic demand and commanded nightly rates significantly higher than the metropolitan baseline.

---

## 3. PART 1: Data Ingestion & Pipeline Orchestration (Tasks 1 to 3)

> **Part 1 Specification Summary: Data Ingestion & Orchestration**  
> Implement an ELT pipeline using Apache Airflow to ingest Inside Airbnb monthly data, ABS Census G01/G02 tables, and LGA-Suburb mappings into PostgreSQL Bronze tables. Ensure atomic replacement for reference tables, append with lineage for monthly batches, dynamic runtime file execution, and full auditability.

**Pipeline Orchestration Architecture:** The Airflow DAG (`dags/load_airbnb_census_dag.py`) executes with `schedule_interval=None` and `max_active_runs=1`. Upstream reference tasks execute concurrently before listing ingestion:  
`[task_load_census_g01, task_load_census_g02, task_load_lga_suburb] >> task_load_airbnb`  
Reference tables utilize `if_exists='replace'` for idempotency, while monthly listings utilize `if_exists='append'` enriched with lineage metadata (`file_source` and `ingestion_timestamp`), achieving end-to-end idempotency via downstream staging deduplication.

**Dynamic Execution:** Dynamic batching is supported via `dag_run.conf['file']`, allowing peer engineers to ingest any batch (`05_2020.csv` for initial load, subsequent months for incremental batches). Multi-tier helper `get_file_content()` transparently resolves file paths across Composer GCS mounts (`/home/airflow/gcs/data`), direct GCSHook blob streaming, and local POSIX paths (`/opt/airflow/data`).

**Schema Definition:** Script `sql/01_create_bronze_schema.sql` (and `part_1.sql`) provisions bronze, silver, and gold namespaces. In `bronze.raw_listings`, all 22 Inside Airbnb columns are declared as raw TEXT to absorb upstream schema drift and field reordering. Census tables define `lga_code_2016 TEXT`, matching the raw ABS CSV headers identically.

### Table 1: Raw Bronze Ingestion Accounting Across PostgreSQL Database
| Target Bronze Table | Source File | Strategy | Rows | Status |
| :--- | :--- | :--- | :---: | :---: |
| `bronze.raw_census_g01` | `2016Census_G01_NSW_LGA.csv` | Idempotent Replace | 132 | CONFIRMED |
| `bronze.raw_census_g02` | `2016Census_G02_NSW_LGA.csv` | Idempotent Replace | 132 | CONFIRMED |
| `bronze.raw_lga_suburb` | `NSW_LGA_Suburb_Mapping.csv` | Idempotent Replace | 4,470 | CONFIRMED |
| `bronze.raw_listings` (Initial) | `05_2020.csv` | Append + Metadata | 37,562 | CONFIRMED |
| `bronze.raw_listings` (12-Mo Full) | `05_2020 to 04_2021 (12 CSVs)` | Monthly Append | 412,122 | CONFIRMED |

> **Part 1 Direct Output & Verification:**  
> • Autonomous Orchestration: Airflow executed all DAG tasks with 100% green status, streaming directly to PostgreSQL in 1.1 seconds.  
> • Zero Data Loss: All 22 Inside Airbnb columns captured in raw TEXT to preserve original fidelity for downstream modeling.  
> • Full Lineage: Every row tagged with `file_source` and `ingestion_timestamp` for complete provenance tracking.

---

## 4. PART 2: Data Warehouse Design with dbt (Silver & Gold Layers)

> **Part 2 Specification Summary: Warehouse Modeling, Snapshots & Datamarts**  
> Cleanse raw Bronze records to standardize types, sanitize currency strings, and harmonize property categories. Implement SCD Type 2 tracking using dbt snapshots with the timestamp strategy. Build a Gold Star Schema where the fact table strictly contains foreign keys and numerical metrics, and construct three analytical datamart views with MoM metrics.

**Silver Cleansing & Normalization (`silver.stg_listings.sql`):** Authored as a declarative dbt view executing:
1. **Currency Sanitization & Defensive Defaults:** `REGEXP_REPLACE(price, '[^0-9.]', '', 'g')::NUMERIC` strips non-numeric formatting (dollar signs and commas). Missing prices defensively coalesce via `COALESCE(..., 0.0)` to preserve staging record volume; because datamarts aggregate these directly, unlisted zero-dollar items are retained in calculations, pulling down minimum and average pricing as a documented design choice and known limitation.
2. **July Date Anomaly Alignment:** Canonical `month_year` is derived directly from `file_source`, and out-of-month scrape dates in `07_2020.csv` (such as anomalous September timestamps) are aligned to the 14th of the file's month: `(file_month_year || '-14')::DATE`.
3. **Property Type Harmonization:** Pre-August generic categories (e.g. Apartment, House, Hotel, Hostel) are standardized to post-August naming (e.g. Entire apartment, Private room in house, Room in hotel) across 100% of rows.
4. **End-to-End Deduplication:** Enforced via `DISTINCT ON (listing_id, scraped_date) ORDER BY listing_id, scraped_date, ingestion_timestamp DESC NULLS LAST`, guaranteeing exact single-record monthly cardinality and idempotent batch re-execution.

**SCD Type 2 Snapshot Mechanics:** Slowly Changing Dimensions preserve historical state without destructive overwrites. Under the hood, dbt's snapshot engine computes an MD5 surrogate hash, compares incoming records against active rows (`dbt_valid_to IS NULL`), closes modified records by setting `dbt_valid_to` to the new timestamp, and inserts the new version. To prevent premature freezing or false-positive mutations, snapshots date each key's state from when that state began (state-start strategy), capturing 49,072 property versions and 34,610 host versions with zero active-flag mismatches.

![Figure 2: SCD Type 2 Timeline Diagram](reports/images/scd2_timeline_diagram.png)

### Table 2: Silver Layer SCD Type 2 Snapshot Summary Across 12 Months
| Snapshot Model | Unique Key | Strategy | Tracked Attributes | Total Rows |
| :--- | :--- | :--- | :--- | :---: |
| `silver.snapshot_host` | `host_id` | timestamp (state-start) | name, since, location, superhost, neighbourhood | 34,610 (3,609 closed, 31,001 active) |
| `silver.snapshot_property` | `listing_id` | timestamp (state-start) | property_type, room_type, accommodates, baths, beds, neighbourhood, active | 49,072 (3,459 closed, 45,613 active) |
| `silver.snapshot_suburb_lga` | `suburb_name` | timestamp | suburb_name, lga_code, lga_name | 4,520 (Static crosswalk) |

**Gold Star Schema Design Standards:** Following Ralph Kimball's dimensional modeling standards, the fact table contains strictly foreign keys and numerical metrics—no descriptive text attributes reside in facts:
- **Fact Table (`gold.fact_listings`):** 412,122 rows. Grain & Keys: `fact_listing_id` (surrogate MD5 hash), `listing_id`, `host_id`, `scraped_date`. Numeric metrics & flags only: `price`, `has_availability_flag` (1/0), `availability_30`, `number_of_reviews`, `review_scores_rating`, `number_of_stays`, `estimated_revenue` (`(30 - availability_30) * price`). Spatial dimensions (`suburb_name`, `lga_code`) are joined dynamically via `dim_property` and `dim_suburb` point-in-time relationships.
- **Dimension Models:** `gold.dim_host` (34,610 rows), `gold.dim_property` (49,072 rows), `gold.dim_suburb` (4,520 rows), `gold.dim_lga` (128 rows), `census_g01` (132 rows), and `census_g02` (132 rows) maintain conformed descriptive context.

![Figure 3: Gold Tier Star Schema Entity-Relationship Diagram (ERD)](reports/images/star_schema_erd.png)

**Point-in-Time Temporal Joins:** To eliminate lookahead bias (data leakage), facts are matched strictly against the dimension record effective at transaction time:
```sql
ON fact.listing_id = dim_prop.listing_id
   AND fact.scraped_date >= dim_prop.dbt_valid_from
   AND (fact.scraped_date < dim_prop.dbt_valid_to OR dim_prop.dbt_valid_to IS NULL)
```

**Analytical Datamarts:** Three specialized analytical views aggregate multi-dimensional business metrics:
1. `dm_listing_neighbourhood`: Computes monthly metrics per neighbourhood: active listing count, minimum/maximum/median/average nightly price, distinct host count, superhost rate, total reviews/ratings, total stays, estimated revenue, and MoM active listing rate growth percentage using `LAG()`.
2. `dm_property_type`: Computes active listing rate, pricing distributions, distinct hosts, superhost percentage, total stays, and estimated revenue across `property_type`, `room_type`, `accommodates`, and `year_month`.
3. `dm_host_neighbourhood`: Tracks host count, total estimated revenue, estimated revenue per host, and MoM revenue change per host across host LGAs.

> **Part 2 Architecture & Tooling Compliance:**  
> • Pure Dimensional Fact: `fact_listings` holds strictly surrogate/natural keys and numeric metrics (412,122 rows).  
> • True SCD2 History: 3,459 closed property versions and 3,609 closed host versions capture temporal transitions accurately.  
> • Tooling Implementation: dbt Core CLI was selected to enable containerized, headless automation in local Docker and Apache Airflow, providing direct terminal execution and automated CI/CD testing.

---

## 5. PART 3: Sequential Incremental Ingestion & Longitudinal Processing

> **Part 3 Specification Summary: Sequential Ingestion & Monthly dbt Runs**  
> Ingest the remaining 11 months sequentially (06_2020.csv to 04_2021.csv). After each monthly load, execute dbt snapshot and dbt run to build the longitudinal warehouse history, tracking Slowly Changing Dimensions chronologically over time.

**Sequential Ingestion Execution:** To simulate real-world production ELT operations, all 12 monthly Inside Airbnb files were ingested in strict chronological sequence (`05_2020` through `04_2021`). The orchestrator (`scripts/pipeline_runner.py`) appends each monthly batch into `bronze.raw_listings` and immediately triggers `dbt snapshot` and `dbt run`.

**Longitudinal State Tracking:** As consecutive months are processed, dbt evaluates each entity against active snapshot records. When an existing host gains superhost status or a listing modifies its availability or price, dbt snapshot automatically stamps `dbt_valid_to` on the prior version and creates a new active version with `dbt_valid_from` set to the batch date. Point-in-time temporal joins in downstream Gold models ensure that historical transactions reflect the exact state effective at scrape time.

> **Part 3 Verification Audit:**  
> • Sequential Ingestion: All 12 monthly CSVs processed chronologically without pipeline interruption.  
> • Deterministic SCD2 Accumulation: Snapshots expanded progressively from month 1 (37,562 rows) to month 12 (49,072 property and 34,610 host versions).  
> • Fact Integrity: Across all 12 months, 100% of fact records (412,122 rows) match their corresponding SCD2 dimension records with 0 active-flag mismatches.

---

## 6. PART 4: Ad-Hoc Analytical Queries (SQL Analytics & Findings)

### Question A: Demographic Differences in Top 3 vs Bottom 3 LGAs

> **Part 4 — Question A: Demographic Differences (Top 3 vs Lowest 3 LGAs)**  
> *"What are the demographic differences (e.g., age group distribution, household size) between the top 3 performing and lowest 3 performing LGAs based on estimated revenue per active listing over the last 12 months?"*

Question A evaluated 12-month average estimated revenue per active listing across Sydney LGAs (>50 active listings). Cohorts were ranked via `DENSE_RANK()` and linked to ABS Census tables G01 and G02.

### Table 3: Demographic & Economic Comparison: Top 3 vs Bottom 3 Performing LGAs
| Cohort | LGA Name | Avg Revenue | Household | Median Age | Weekly Inc | % Age 25-54 | % Age 55+ |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Top 3 | Mosman | $9,326.52 | 2.4 | 42.0 | $2,522 | 41.4% | 31.1% |
| Top 3 | Northern Beaches | $7,591.13 | 2.7 | 40.0 | $2,178 | 41.6% | 28.0% |
| Top 3 | Woollahra | $6,887.47 | 2.3 | 39.0 | $2,687 | 44.8% | 29.4% |
| Bottom 3 | Canterbury-Bankstown | $1,495.72 | 3.0 | 35.0 | $1,298 | 41.5% | 24.6% |
| Bottom 3 | Blacktown | $1,310.99 | 3.2 | 33.0 | $1,711 | 43.2% | 20.3% |
| Bottom 3 | Fairfield | $1,298.32 | 3.3 | 36.0 | $1,222 | 39.7% | 26.3% |

![Figure 4: Comparative Performance & Income Disparities](reports/images/chart_q1_top_bottom_lgas.png)

> **Question A Direct Findings & Demographic Insights:**  
> • Revenue Disparity: Top 3 LGAs (Mosman: $9,327, Northern Beaches: $7,591, Woollahra: $6,887) average $7,935/listing — 5.8x higher than Bottom 3 LGAs (Canterbury-Bankstown: $1,496, Blacktown: $1,311, Fairfield: $1,298 averaging $1,368).  
> • Household Size Inversion: Top LGAs average smaller households (2.3–2.7) vs outer suburban LGAs (3.0–3.3 persons).  
> • Income Gap: Median weekly household income in Mosman ($2,522) and Woollahra ($2,687) is over double that of Fairfield ($1,222) and Canterbury-Bankstown ($1,298), while Northern Beaches ($2,178) is approximately 1.7–1.8× higher.  
> • Mature Demographics: Top LGAs feature significantly older populations (median age 39.0–42.0 vs 33.0–36.0 in Bottom 3).

---

### Question B: Pearson Correlation Analysis (Median Age vs Revenue)

> **Part 4 — Question B Specification Summary: Correlation Analysis**  
> Evaluate the correlation between the median age of an LGA and estimated revenue per active listing over the last 12 months. Calculate Pearson's correlation coefficient r across all Greater Sydney LGAs and provide statistical and business interpretation.

Question B calculates Pearson's correlation coefficient r between LGA median age (`census_g02`) and 12-month average estimated revenue per active listing (`gold.fact_listings`) across all $N = 29$ Sydney LGAs.

### Table 4: Pearson Correlation Statistical Summary
| Metric | Sample Size (LGAs) | Mean Value | Statistical Result |
| :--- | :---: | :---: | :--- |
| Pearson Correlation (r) | 29 LGAs | N/A | **+0.6554 (Strong Positive Correlation)** |
| t-statistic / Significance | 29 LGAs | t ≈ 4.51 | **p < 0.001 (Statistically Significant)** |
| Average Revenue per Listing | 29 LGAs | $3,480.13 | Range: $1,298.32 - $9,326.52 |
| Median Age of Population | 29 LGAs | 35.9 Years | Range: 32.0 - 42.0 Years |

![Figure 5: Scatter Plot & Trendline](reports/images/chart_q2_median_age_vs_revenue.png)

> **Question B Direct Findings & Statistical Verdict:**  
> • Correlation Coefficient: Pearson $r = +0.6554$ confirms a strong, statistically significant positive linear relationship ($t \approx 4.51$, $p < 0.001$).  
> • Demographic Explanation: Older LGAs (Mosman: 42 yrs, Northern Beaches: 40 yrs, Woollahra: 39 yrs) represent affluent harbourside and coastal enclaves commanding premium nightly rates ($189–$237).  
> • Younger Enclaves: Younger LGAs (Blacktown: 33 yrs, Canterbury-Bankstown: 35 yrs, Strathfield: 32 yrs) feature family/student clusters and lower yields ($1,311–$1,496).

---

### Question C: Optimal Property Configuration in Top 5 Neighbourhoods

> **Part 4 — Question C: Optimal Property Configuration in Top 5 Neighbourhoods**  
> *"What will be the best type of listing (property type, room type and accommodates for) for the top 5 'listing_neighbourhood' (by average estimated revenue per active listing) to have the highest number of stays?"*

Question C identified Sydney's Top 5 revenue-generating neighbourhoods and determined the specific property configuration (`property_type` × `room_type` × `accommodates`) that maximized total guest stays recorded over the 12-month period.

### Table 5: Optimal Property Configuration for Most Stays in Top 5 Highest-Revenue Neighbourhoods
| Neighbourhood | Avg Rev | Best Property Type | Room Type | Acc. | Total Stays | Avg Stays | Avg Price |
| :--- | :---: | :--- | :--- | :---: | :---: | :---: | :---: |
| Mosman | $9,326.52 | Entire apartment | Entire home/apt | 2 | 26,476 | 24.77 | $189.43 |
| Northern Beaches | $7,591.13 | Entire apartment | Entire home/apt | 4 | 176,680 | 23.63 | $237.16 |
| Woollahra | $6,887.47 | Entire apartment | Entire home/apt | 2 | 76,641 | 24.87 | $158.24 |
| Hunters Hill | $5,903.32 | Entire apartment | Entire home/apt | 4 | 1,807 | 27.80 | $157.46 |
| Waverley | $5,650.55 | Entire apartment | Entire home/apt | 2 | 279,805 | 25.57 | $170.24 |

![Figure 6: Total Stays by Optimal Configuration](reports/images/chart_q3_top5_neighbourhoods_stays.png)

> **Question C Strategic Investment Recommendations:**  
> • Entire Apartment Dominance: Across all Top 5 neighbourhoods, Entire apartment (Entire home/apt) drove the highest number of stays.  
> • 2-Guest vs 4-Guest Capacity: Couples/solo travelers dominate urban coastal hubs (Waverley: 279,805 stays, Woollahra: 76,641 stays, Mosman: 26,476 stays in 2-guest units). Family-oriented destinations like Northern Beaches peak with 4-guest units (176,680 stays at $237.16/night).  
> • Turnover Rate: High-revenue configurations average 23.6 to 27.8 stays per listing annually, demonstrating consistent short-term occupancy.

---

### Question D: Host Portfolio Concentration Across LGAs

> **Part 4 — Question D: Host Portfolio Concentration Across LGAs**  
> *"For hosts with multiple listings, are their properties concentrated within the same LGA, or are they distributed across different LGAs?"*

Question D evaluates the geographic footprint of multi-listing hosts ($n = 5,095$ hosts with 2+ listings) across Local Government Areas using point-in-time dimension links between `fact_listings`, `dim_property`, and `dim_suburb`.

### Table 6: Multi-Listing Host Geographic Distribution Pattern
| Distribution Pattern | Total Hosts | Percentage of Multi-Listing Hosts |
| :--- | :---: | :---: |
| Concentrated (Same LGA) | 3,910 | **76.74%** |
| Distributed (2+ LGAs) | 1,185 | **23.26%** |

![Figure 7: Host Geographic Distribution Pattern](reports/images/chart_q4_host_concentration.png)

> **Question D Direct Findings & Strategic Implications:**  
> • Localized Operations: Over three-quarters (76.74%, 3,910 hosts) of multi-listing operators concentrate all units within a single LGA, reflecting localized clustering and operational efficiencies in maintenance and key management.  
> • Distributed Operators: 23.26% (1,185 hosts) operate multi-LGA portfolios, representing commercial multi-unit property managers scaling across Greater Sydney.

---

### Question E: Single-Listing Hosts vs Annualised Median Mortgages

> **Part 4 — Question E: Single-Listing Hosts vs Annualised Median Mortgage Repayments**  
> *"For hosts with a single Airbnb listing, does the estimated revenue over the last 12 months cover the annualised median mortgage repayment in the corresponding LGA? Which LGA has the highest percentage of hosts that can cover it?"*

Question E evaluates single-listing hosts by aggregating their 12-month estimated revenue and benchmarking against the annualised median mortgage repayment (`median_mortgage_repay_monthly * 12`) from Census G02 for each LGA.

### Table 7: Single-Listing Hosts Covering Annualised Median Mortgage (Top LGAs)
| LGA Name | Single Hosts | Hosts Covering | % Covering | Avg Annual Rev | Annual Mortgage |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Northern Beaches | 4,223 | 2,382 | **56.41%** | $70,955.49 | $33,600.00 |
| Mosman | 340 | 178 | **52.35%** | $74,570.27 | $36,000.00 |
| Sutherland Shire | 492 | 232 | **47.15%** | $43,727.79 | $29,124.00 |
| Waverley | 4,119 | 1,903 | **46.20%** | $52,211.35 | $36,000.00 |
| Hunters Hill | 55 | 25 | **45.45%** | $47,992.33 | $36,396.00 |
| Sydney | 5,576 | 2,487 | **44.60%** | $36,123.32 | $29,988.00 |
| Randwick | 2,434 | 1,085 | **44.58%** | $42,329.13 | $31,200.00 |
| North Sydney | 958 | 414 | **43.22%** | $43,325.06 | $31,200.00 |
| Inner West | 1,888 | 747 | **39.57%** | $38,011.95 | $31,200.00 |
| Willoughby | 352 | 130 | **36.93%** | $53,688.10 | $34,524.00 |
| Woollahra | 1,262 | 465 | **36.85%** | $48,412.01 | $38,400.00 |
| Blacktown | 213 | 27 | **12.68%** | $14,905.41 | $25,800.00 |

![Figure 8: Percentage Covering Median Mortgage Repayments](reports/images/chart_q5_mortgage_coverage.png)

> **Question E Direct Findings & Economic Insights:**  
> • Top Performing LGA: Northern Beaches ranks #1 in Greater Sydney, with 56.41% of single-listing hosts earning more than the annualised median mortgage ($33,600), generating an average of $70,955 in annual revenue.  
> • Second Ranked: Mosman follows at 52.35% covering mortgage, averaging $74,570 in annual STR income against a $36,000 annual mortgage.  
> • Third Ranked: Sutherland Shire achieves 47.15% coverage, averaging $43,728 revenue against a $29,124 mortgage.  
> • Western Suburbs Gap: In outer Western Sydney (Blacktown: 12.68%, Campbelltown: 14.81%, Fairfield: 15.00%), fewer than 1 in 6 single-listing hosts generate enough revenue to cover the median mortgage.

---

## 7. Issues, Bugs Faced and Engineering Resolutions

### 7.1 Cross-Platform POSIX Path Incompatibilities in Cloud Composer
- **Issue:** Composer mounts GCS to `/home/airflow/gcs/data/`, while Docker mounts `/opt/airflow/data/`, causing path resolution errors.
- **Resolution:** Created `get_file_content()` checking Composer mounts, GCSHook, and local POSIX paths dynamically.
- **Outcome:** Fully portable DAG execution across Docker and Composer with zero path errors.

### 7.2 Custom Schema Name Macro Override in dbt
- **Issue:** dbt's default schema macro prefixed schemas as `public_silver` and `public_gold` instead of `silver` and `gold`.
- **Resolution:** Added `dbt_bde/macros/generate_schema_name.sql` to override prefix logic and return custom schema names cleanly.
- **Outcome:** Schemas materialized cleanly as `bronze`, `silver`, and `gold` namespaces.

### 7.3 July Scrape Date Anomaly & September Double-Count Fix
- **Issue:** File `07_2020.csv` contained 4,780 rows with scrape dates stamped `2020-09-05`, causing staging models that derived `month_year` from scrape date to undercount July (31,277) and inflate September (39,609 with duplicate listings).
- **Resolution:** In `silver.stg_listings`, derived canonical `month_year` strictly from `file_source` and re-aligned any out-of-month scrape dates directly to the 14th of the file's month: `(file_month_year || '-14')::DATE`.
- **Outcome:** Restored correct monthly volume (July: 36,057, September: 34,829), eliminated 4,758 duplicate listings in September, and ensured flawless temporal joins.

### 7.4 Property Type Harmonization Across Longitudinal Batches
- **Issue:** Pre-August files used generic categories (Apartment, House, Hotel, Hostel) while post-August used specific names (Entire apartment, Room in hotel), causing property type fracturing in datamarts.
- **Resolution:** Implemented standardized CASE mapping in `silver.stg_listings` matching `room_type` and `property_type` to post-August naming conventions across 100% of rows.
- **Outcome:** Eliminated fragmented groupings across all 412,122 records in `dm_property_type` and Question C.

### 7.5 SCD Type 2 State-Start Snapshot Strategy
- **Issue:** Snapshots ordering by `scraped_date ASC` froze records at their first-seen version, ignoring subsequent attribute changes and causing active-flag mismatches against fact records.
- **Resolution:** Re-architected snapshots to track state changes dynamically, setting `updated_at` to the timestamp when each distinct attribute state began.
- **Outcome:** Generated 49,072 property versions and 34,610 host versions with 0 mismatches between fact availability flags and dimension records.

### 7.6 Point-in-Time Temporal Join Cardinality Control
- **Issue:** Joins on natural keys between facts and snapshots produced Cartesian row fan-out due to multiple historical dimension versions.
- **Resolution:** Enforced strict validity interval predicates: `fact.scraped_date >= dim.dbt_valid_from AND (fact.scraped_date < dim.dbt_valid_to OR dim.dbt_valid_to IS NULL)`.
- **Outcome:** Maintained exact 1:1 cardinality matching all 412,122 fact rows across all 12 snapshot months.

---

### 7.7 Operational Replication Checklist for Peer Engineers

To reproduce the complete pipeline end-to-end on local Docker or GCP Cloud Composer, execute the following verified CLI sequence:

```bash
# 1. Launch local Docker infrastructure or connect to Cloud SQL
docker compose up -d

# 2. Initialize Bronze schemas & trigger Airflow ingestion
psql -h <CLOUD_SQL_IP> -U postgres -d postgres -f sql/01_create_bronze_schema.sql  # or localhost for Docker
airflow dags trigger load_airbnb_census_dag

# 3. Execute dbt Silver staging views & SCD Type 2 snapshots
dbt run --select stg_listings
dbt snapshot

# 4. Build Gold Star Schema, analytical datamarts & test assertions
dbt run --select gold
dbt test
```

### Table 8: Pipeline Component Verification Audit
| Pipeline Component | Target Output Metric | Status | Verification Method |
| :--- | :--- | :---: | :--- |
| Airflow Ingestion DAG | 4 Green Tasks (100% Success) | CONFIRMED | Airflow Grid View & Task Logs |
| Bronze Data Ingestion | 412,122 Listings, 4,734 Ref Rows | CONFIRMED | PostgreSQL Row Count Assertions |
| Silver Staging Cleansing | Regex Currency / Date Parsing | CONFIRMED | `dbt run --select stg_listings` |
| Silver SCD2 Snapshots | 3 Dimension Snapshots Active | CONFIRMED | `dbt snapshot` (PASS=3, WARN=0) |
| Gold Star Schema | fact_listings (IDs & Metrics) | CONFIRMED | `dbt run --select gold` (PASS=11) |
| Analytical Datamarts | 3 Datamarts with MoM Metrics | CONFIRMED | Point-in-Time Join SQL Queries |
| Part 4 Ad-Hoc Analytics | Q(a) through Q(e) Empirical Findings | CONFIRMED | Deterministic SQL Executions |
| Local Docker Reproducibility | Single-command docker compose | CONFIRMED | Tested on Docker & Python 3.10 |
