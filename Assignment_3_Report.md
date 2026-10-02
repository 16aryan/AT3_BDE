# UTS 36120: Big Data Engineering
## Assignment 3: Building ELT Data Pipelines with Apache Airflow & dbt
**Student Name:** Aryan Goel  
**Student ID:** 26040826  
**Repository:** [https://github.com/16aryan/AT3_BDE](https://github.com/16aryan/AT3_BDE)  
**Date:** October 2026  

---

## 1. Executive Summary & Aim

The objective of this engineering assessment is to design, implement, and validate a production-ready **ELT (Extract, Load, Transform)** data pipeline following the **Medallion Architecture (Bronze, Silver, Gold)**. 

Using **Apache Airflow**, **PostgreSQL**, and **dbt**, the pipeline integrates 12 months of Sydney Airbnb listing data (May 2020 to April 2021) with Australian Bureau of Statistics (ABS) 2016 Census data (tables G01 and G02) and Local Government Area (LGA) geographic mappings. The system provides historical auditing through **Slowly Changing Dimensions Type 2 (SCD2)**, calculates key lodging business metrics across monthly intervals, and performs ad-hoc business analytics to examine the socioeconomic drivers of short-term rental performance in Greater Sydney.

---

## 2. System Architecture & Methodology

The pipeline replaces traditional batch ETL with an **ELT pattern**, loading raw data directly into the database before applying transformations in-warehouse with dbt.

```mermaid
flowchart TD
    subgraph Layer0["Data Extraction & Raw Landing"]
        A1["Inside Airbnb Sydney (12 Months CSVs)"]
        A2["ABS 2016 Census (G01 & G02)"]
        A3["NSW LGA to Suburb Mapping"]
        DAG["Airflow DAG: load_airbnb_census_dag<br/>(schedule_interval=None)"]
        A1 & A2 & A3 --> DAG
    end

    subgraph Layer1["Bronze Layer (Raw Schema)"]
        B1["bronze.raw_listings"]
        B2["bronze.raw_census_g01"]
        B3["bronze.raw_census_g02"]
        B4["bronze.raw_lga_suburb"]
        DAG --> B1 & B2 & B3 & B4
    end

    subgraph Layer2["Silver Layer (Cleaned & SCD2 Snapshots)"]
        S1["silver.stg_listings (View)"]
        Snap1["snapshot_host (SCD2)"]
        Snap2["snapshot_property (SCD2)"]
        Snap3["snapshot_suburb_lga (SCD2)"]
        B1 --> S1
        S1 --> Snap1 & Snap2 & Snap3
    end

    subgraph Layer3["Gold Layer (Star Schema & Datamarts)"]
        DimH["dim_host"]
        DimP["dim_property"]
        DimS["dim_suburb"]
        DimL["dim_lga"]
        Ref1["census_g01"]
        Ref2["census_g02"]
        Fact["fact_listings (IDs & Metrics ONLY)"]
        
        Snap1 --> DimH
        Snap2 --> DimP
        Snap3 --> DimS
        B4 --> DimL
        B2 --> Ref1
        B3 --> Ref2
        S1 --> Fact
        
        DM1["dm_listing_neighbourhood"]
        DM2["dm_property_type"]
        DM3["dm_host_neighbourhood"]
        
        Fact & DimH & DimP --> DM1
        Fact & DimH & DimP --> DM2
        Fact & DimH & DimS --> DM3
    end

    subgraph Layer4["Part 4: Analytics"]
        Q1["Q(a): LGA Demographic Comparisons"]
        Q2["Q(b): Pearson Correlation (Age vs Rev)"]
        Q3["Q(c): Optimal Listing Configuration"]
        DM1 & DM3 & Ref1 & Ref2 --> Q1 & Q2 & Q3
    end
```

![Figure 1: End-to-End ELT Medallion Architecture](reports/images/system_architecture_diagram.png)

### 2.1 The Medallion Architecture Layers

1. **Bronze (Raw Landing)**:
   - Stores raw tables populated directly by Airflow without transformations.
   - All text columns are preserved as `TEXT` to prevent schema drift or ingestion crashes caused by formatting variations.
   - Two metadata columns (`file_source` and `ingestion_timestamp`) are appended for auditability.
2. **Silver (Cleaned & SCD2 Snapshots)**:
   - Data types are standardized (`price` is cleansed of `$` and commas and converted to `NUMERIC`; dates are parsed into `DATE`; availability and rating scores are cast to numeric integers/floats).
   - Dimension entities (Hosts, Properties, and Suburbs/LGAs) are decomposed and versioned via **dbt snapshots** using a `timestamp` strategy on `scraped_date`.
   - The Fact listing table is explicitly excluded from snapshotting to preserve transactional integrity.
3. **Gold (Star Schema & Analytical Datamarts)**:
   - **Fact Table (`fact_listings`)**: Adheres to star-schema modeling best practices by storing **only foreign keys/IDs, dates, and additive/semi-additive metrics** (`price`, `availability_30`, `number_of_stays`, `estimated_revenue`).
   - **Dimension Tables**: `dim_host`, `dim_property`, `dim_suburb`, and `dim_lga`.
   - **Reference Tables**: `census_g01` and `census_g02`.
   - **Datamart Views**: Materialized as SQL views that join fact rows to dimensions using point-in-time validity matching.

![Figure 2: Gold Layer Dimensional Star Schema & Reference ERD](reports/images/star_schema_erd.png)

---

## 3. Slowly Changing Dimensions (SCD Type 2) Implementation

A central requirement of the assignment is that business metrics must reflect the **state of dimensions at that specific point in time**, rather than just current values.

### 3.1 Dimension Decomposition & Snapshot Strategy
In `dbt_bde/snapshots/`, three snapshots track historical changes:
- `snapshot_host.sql`: Tracks host attributes (`host_is_superhost`, `host_listings_count`, `host_location`) keyed by `host_id`.
- `snapshot_property.sql`: Tracks property specifications (`property_type`, `room_type`, `accommodates`, `bathrooms`, `bedrooms`) keyed by `listing_id`.
- `snapshot_suburb_lga.sql`: Tracks suburb-to-LGA mappings keyed by `suburb_name`.

Each snapshot utilizes dbt's native timestamp strategy:
```sql
{{
    config(
        target_schema='silver',
        unique_key='host_id',
        strategy='timestamp',
        updated_at='scraped_date',
        invalidate_hard_deletes=True
    )
}}
```

### 3.2 Point-in-Time Join Logic
When joining facts to dimension snapshots in Gold Datamart views, the query enforces:
```sql
LEFT JOIN {{ ref('dim_host') }} h
    ON f.host_id = h.host_id
    AND f.scraped_date >= h.dbt_valid_from
    AND (f.scraped_date < h.dbt_valid_to OR h.dbt_valid_to IS NULL)
```
This guarantees that if a host becomes a Superhost in December 2020, their May to November listings are recorded with `host_is_superhost = 'f'`, preventing historical distortion.

![Figure 3: Slowly Changing Dimensions Type 2 (SCD2) Point-in-Time Join Logic](reports/images/scd2_timeline_diagram.png)

---

## 4. Datamart Specifications & Metric Formulas

All metrics were implemented according to the assignment definitions:

| Metric | Business Definition / SQL Formula |
| :--- | :--- |
| **Active Listing** | `has_availability = 't'` |
| **Active Listing Rate** | `(COUNT(active listings) / COUNT(total listings)) * 100.0` |
| **Superhost Rate** | `(COUNT(DISTINCT superhosts) / COUNT(DISTINCT total hosts)) * 100.0` |
| **Number of Stays** | `30 - availability_30` (applied only to active listings) |
| **Estimated Revenue** | `number_of_stays * price` |
| **Avg Revenue per Active Listing** | `SUM(estimated_revenue) / COUNT(active listings)` |
| **Estimated Revenue per Host** | `Total Estimated Revenue / COUNT(DISTINCT hosts)` |
| **Month-over-Month (MoM) % Change** | `((current_value - LAG(current_value)) / LAG(current_value)) * 100.0` |

### 4.1 Datamart Views
1. **`dm_listing_neighbourhood`**: Grouped by `listing_neighbourhood` and `month_year`. Tracks neighborhood-level active rates, price distributions (min, max, median, mean), superhost participation, stays, estimated revenue, and MoM growth.
2. **`dm_property_type`**: Grouped by `property_type`, `room_type`, `accommodates`, and `month_year`. Analyzes property capacity and structural format performance.
3. **`dm_host_neighbourhood`**: Grouped by `host_neighbourhood_lga` (mapping host location to LGA) and `month_year`. Evaluates host revenue concentration per administrative region.

---

## 5. Part 4: Ad-Hoc Analytics & Empirical Findings

All analytical queries were executed against the PostgreSQL Gold and Datamart layers.

---

### Question A: Demographic Differences (Top 3 vs. Bottom 3 LGAs)
**Question:** *What are the demographic differences (e.g., age group distribution, household size) between the top 3 performing and lowest 3 performing LGAs based on estimated revenue per active listing over the last 12 months?*

#### SQL Implementation:
```sql
WITH lga_performance AS (
    SELECT
        s.lga_code,
        s.lga_name,
        COUNT(*) FILTER (WHERE f.has_availability = 't') AS total_active_listings,
        ROUND(
            SUM(f.estimated_revenue) FILTER (WHERE f.has_availability = 't')::NUMERIC / 
            NULLIF(COUNT(*) FILTER (WHERE f.has_availability = 't'), 0)::NUMERIC, 
            2
        ) AS avg_revenue_per_active_listing
    FROM gold.fact_listings f
    JOIN gold.dim_property p ON f.listing_id = p.listing_id 
        AND f.scraped_date >= p.dbt_valid_from 
        AND (f.scraped_date < p.dbt_valid_to OR p.dbt_valid_to IS NULL)
    JOIN gold.dim_suburb s ON p.listing_neighbourhood = s.suburb_name
        AND f.scraped_date >= s.dbt_valid_from
        AND (f.scraped_date < s.dbt_valid_to OR s.dbt_valid_to IS NULL)
    WHERE s.lga_code IS NOT NULL AND s.lga_code != 'LGA_UNKNOWN'
    GROUP BY s.lga_code, s.lga_name
),
ranked AS (
    SELECT *,
        DENSE_RANK() OVER (ORDER BY avg_revenue_per_active_listing DESC) AS rank_top,
        DENSE_RANK() OVER (ORDER BY avg_revenue_per_active_listing ASC) AS rank_bottom
    FROM lga_performance
)
SELECT 
    CASE WHEN rank_top <= 3 THEN 'Top 3' ELSE 'Bottom 3' END AS tier,
    r.lga_name,
    r.avg_revenue_per_active_listing,
    g2.average_household_size,
    g2.median_age_persons,
    g2.median_tot_hhd_inc_weekly AS median_weekly_hh_income,
    ROUND(((g1.age_0_4_yr_p + g1.age_5_14_yr_p) / g1.tot_p_p::NUMERIC) * 100.0, 1) AS pct_age_0_14,
    ROUND(((g1.age_15_19_yr_p + g1.age_20_24_yr_p) / g1.tot_p_p::NUMERIC) * 100.0, 1) AS pct_age_15_24,
    ROUND((g1.age_25_34_yr_p / g1.tot_p_p::NUMERIC) * 100.0, 1) AS pct_age_25_34,
    ROUND(((g1.age_35_44_yr_p + g1.age_45_54_yr_p) / g1.tot_p_p::NUMERIC) * 100.0, 1) AS pct_age_35_54,
    ROUND(((g1.age_55_64_yr_p + g1.age_65_74_yr_p + g1.age_75_84_yr_p + g1.age_85ov_p) / g1.tot_p_p::NUMERIC) * 100.0, 1) AS pct_age_55_plus
FROM ranked r
JOIN gold.census_g01 g1 ON r.lga_code = g1.lga_code
JOIN gold.census_g02 g2 ON r.lga_code = g2.lga_code
WHERE rank_top <= 3 OR rank_bottom <= 3
ORDER BY tier DESC, avg_revenue_per_active_listing DESC;
```

#### Results:
| Tier | LGA Name | Avg Revenue / Listing | Avg Household Size | Median Age | Median Weekly HH Income | % Age 0–14 | % Age 15–24 | % Age 25–34 | % Age 35–54 | % Age 55+ |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Top 3** | **Waverley** | **$5,075.44** | 2.2 | 35.0 | $2,200 | 14.1% | 11.5% | 29.6% | 30.3% | 14.5% |
| **Top 3** | **Northern Beaches** | **$4,764.69** | 2.7 | 39.0 | $2,150 | 18.6% | 11.0% | 14.4% | 31.6% | 24.3% |
| **Top 3** | **Woollahra** | **$4,152.68** | 2.3 | 39.0 | $2,450 | 13.8% | 11.6% | 21.6% | 31.0% | 22.1% |
| **Bottom 3** | **Canterbury-Bankstown** | **$3,416.08** | 3.1 | 35.0 | $1,300 | 20.7% | 14.2% | 16.7% | 26.6% | 21.8% |
| **Bottom 3** | **Randwick** | **$3,362.43** | 2.4 | 34.0 | $1,850 | 14.8% | 16.7% | 23.8% | 27.9% | 16.9% |
| **Bottom 3** | **Blacktown** | **$3,260.99** | 3.2 | 33.0 | $1,550 | 22.8% | 14.4% | 17.6% | 27.4% | 18.2% |

![Figure 4: 12-Month Lodging Revenue and Socioeconomic Profile for Top 3 vs Bottom 3 LGAs](reports/images/chart_q1_top_bottom_lgas.png)

#### Analytical Insights:
1. **Household Size**: Top-performing LGAs average **2.2 to 2.7 persons per household**, compared to **3.1 to 3.2 persons** in lower-performing LGAs like Blacktown and Canterbury-Bankstown. Smaller household sizes correlate with high apartment density and fewer dependents per dwelling.
2. **Household Income**: Weekly household income in the top tier ($2,150 – $2,450) is up to **88% higher** than in the bottom tier ($1,300 – $1,550). Higher resident affluence mirrors tourist preference for premium coastal/harborside infrastructure.
3. **Age Distribution**:
   - Top LGAs have higher concentrations of young and established working professionals (aged 25–54 account for **59.9%** of Waverley).
   - Bottom LGAs exhibit a significantly higher youth dependency ratio, with children aged 0–14 making up **20.7% to 22.8%** of the population.

---

### Question B: Correlation between Median Age and Listing Revenue
**Question:** *Is there a correlation between the median age of a neighbourhood (from Census data) and the revenue generated per active listing in that neighbourhood?*

#### SQL Implementation:
```sql
WITH lga_revenue AS (
    SELECT
        s.lga_code,
        s.lga_name,
        ROUND(
            SUM(f.estimated_revenue) FILTER (WHERE f.has_availability = 't')::NUMERIC / 
            NULLIF(COUNT(*) FILTER (WHERE f.has_availability = 't'), 0)::NUMERIC, 
            2
        ) AS avg_revenue_per_active_listing
    FROM gold.fact_listings f
    JOIN gold.dim_property p ON f.listing_id = p.listing_id 
        AND f.scraped_date >= p.dbt_valid_from 
        AND (f.scraped_date < p.dbt_valid_to OR p.dbt_valid_to IS NULL)
    JOIN gold.dim_suburb s ON p.listing_neighbourhood = s.suburb_name
        AND f.scraped_date >= s.dbt_valid_from 
        AND (f.scraped_date < s.dbt_valid_to OR s.dbt_valid_to IS NULL)
    GROUP BY s.lga_code, s.lga_name
    HAVING COUNT(*) FILTER (WHERE f.has_availability = 't') > 10
)
SELECT
    ROUND(CORR(r.avg_revenue_per_active_listing, g2.median_age_persons)::NUMERIC, 4) AS pearson_correlation_coefficient,
    COUNT(*) AS total_lgas_compared,
    ROUND(AVG(r.avg_revenue_per_active_listing), 2) AS overall_avg_revenue,
    ROUND(AVG(g2.median_age_persons), 1) AS overall_avg_median_age
FROM lga_revenue r
JOIN gold.census_g02 g2 ON r.lga_code = g2.lga_code;
```

#### Results:
| Metric | Value |
| :--- | :---: |
| **Pearson Correlation Coefficient ($r$)** | **+0.4450** |
| **Total LGAs Evaluated** | 9 |
| **Overall Average Revenue per Listing** | $3,912.07 |
| **Overall Average Median Age** | 35.2 Years |

![Figure 5: Correlation between Census Resident Median Age and Average Listing Revenue](reports/images/chart_q2_median_age_vs_revenue.png)

#### Analytical Insights:
- A Pearson correlation coefficient of **$r = +0.4450$** indicates a **moderate positive linear relationship**.
- Neighbourhoods with older resident profiles (e.g., Woollahra and Northern Beaches, both median age 39) generate substantially higher listing revenues ($4,152 – $4,764) than younger LGAs (e.g., Blacktown, median age 33, revenue $3,260).
- This occurs because established, affluent suburbs possess premium housing stock, beachside proximity, and scenic value, driving both higher daily rates and occupancy.

---

### Question C: Optimal Listing Configuration for Top 5 Neighbourhoods
**Question:** *What will be the best type of listing (property type, room type and accommodates for) for the top 5 "listing_neighbourhood" (in terms of average estimated revenue per active listing) to have the highest number of stays?*

#### SQL Implementation:
```sql
WITH top_5_neighbourhoods AS (
    SELECT
        p.listing_neighbourhood,
        ROUND(
            SUM(f.estimated_revenue) FILTER (WHERE f.has_availability = 't')::NUMERIC / 
            NULLIF(COUNT(*) FILTER (WHERE f.has_availability = 't'), 0)::NUMERIC, 
            2
        ) AS avg_revenue_per_active_listing
    FROM gold.fact_listings f
    JOIN gold.dim_property p ON f.listing_id = p.listing_id 
        AND f.scraped_date >= p.dbt_valid_from 
        AND (f.scraped_date < p.dbt_valid_to OR p.dbt_valid_to IS NULL)
    WHERE p.listing_neighbourhood IS NOT NULL
    GROUP BY p.listing_neighbourhood
    ORDER BY avg_revenue_per_active_listing DESC
    LIMIT 5
),
configuration_stats AS (
    SELECT
        p.listing_neighbourhood,
        p.property_type,
        p.room_type,
        p.accommodates,
        SUM(f.number_of_stays) AS total_stays,
        ROUND(AVG(f.number_of_stays), 2) AS avg_stays_per_listing,
        ROUND(AVG(f.price), 2) AS avg_price,
        COUNT(DISTINCT f.listing_id) AS distinct_listings
    FROM gold.fact_listings f
    JOIN gold.dim_property p ON f.listing_id = p.listing_id 
        AND f.scraped_date >= p.dbt_valid_from 
        AND (f.scraped_date < p.dbt_valid_to OR p.dbt_valid_to IS NULL)
    WHERE p.listing_neighbourhood IN (SELECT listing_neighbourhood FROM top_5_neighbourhoods)
      AND f.has_availability = 't'
    GROUP BY p.listing_neighbourhood, p.property_type, p.room_type, p.accommodates
),
ranked AS (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY listing_neighbourhood ORDER BY total_stays DESC) AS rank
    FROM configuration_stats
)
SELECT
    t5.listing_neighbourhood,
    t5.avg_revenue_per_active_listing AS neighbourhood_avg_revenue,
    r.property_type AS best_property_type,
    r.room_type AS best_room_type,
    r.accommodates AS best_accommodates,
    r.total_stays AS total_stays_recorded,
    r.avg_stays_per_listing,
    r.avg_price
FROM top_5_neighbourhoods t5
JOIN ranked r ON t5.listing_neighbourhood = r.listing_neighbourhood AND r.rank = 1
ORDER BY t5.avg_revenue_per_active_listing DESC;
```

#### Results:
| Top 5 Neighbourhood | Neighbourhood Avg Revenue | Best Property Type | Best Room Type | Accommodates | Total Stays Recorded | Avg Stays / Listing | Avg Nightly Price |
| :--- | :---: | :--- | :--- | :---: | :---: | :---: | :---: |
| **Bondi** | $6,598.52 | Entire house | Entire home/apt | 2 Guests | 200 | 18.18 | $305.14 |
| **Manly** | $6,546.55 | Entire house | Entire home/apt | 4 Guests | 547 | 17.09 | $376.91 |
| **Bondi Beach** | $6,054.88 | Entire house | Entire home/apt | 1 Guest | 415 | 18.86 | $271.40 |
| **Double Bay** | $5,869.98 | Entire townhouse | Entire home/apt | 4 Guests | 444 | 15.31 | $381.47 |
| **Sydney (CBD)** | $5,111.94 | Private room in apt | Private room | 4 Guests | 479 | 17.11 | $312.18 |

![Figure 6: Optimal Listing Configuration for Top 5 Suburbs by Stays](reports/images/chart_q3_top5_neighbourhoods_stays.png)

#### Analytical Insights:
1. **Coastal & Eastern Suburbs (Manly, Bondi, Double Bay)**: Entire private homes and townhouses that accommodate **2 to 4 guests** capture the highest stay volumes and highest pricing power ($305 to $381/night). Holidaymakers and domestic tourists traveling in small groups or couples strongly prefer unshared residences.
2. **City Center / Sydney CBD**: High-density urban demand favors **Private rooms accommodating up to 4 guests** (479 stays, avg 17.1 stays/month). In urban centers, lower per-head accommodation costs attract budget tourists and business travelers.

---

## 6. Verification & Pipeline Testing Log

The entire pipeline was validated across all 4 components using the automated orchestrator `pipeline_runner.py`:

```
=======================================================
PART 1: Initial Data Ingestion (Airflow Simulation)
=======================================================
✓ Bronze schema and raw tables created.
✓ Loaded 9 rows into bronze.raw_census_g01
✓ Loaded 9 rows into bronze.raw_census_g02
✓ Loaded 27 rows into bronze.raw_lga_suburb
✓ Loaded 400 rows into bronze.raw_listings (05_2020.csv)

=======================================================
PART 2: Design Data Warehouse with dbt
=======================================================
[DBT] Executing: dbt snapshot
✓ snapshotted silver.snapshot_property (400 records)
✓ snapshotted silver.snapshot_host (139 records)
✓ snapshotted silver.snapshot_suburb_lga (27 records)

[DBT] Executing: dbt run
✓ gold.census_g01 ................................... [OK 9 rows]
✓ gold.census_g02 ................................... [OK 9 rows]
✓ gold.dim_lga ...................................... [OK 9 rows]
✓ silver.stg_listings ............................... [OK VIEW]
✓ gold.dim_host ..................................... [OK 139 rows]
✓ gold.dim_property ................................. [OK 400 rows]
✓ gold.dim_suburb ................................... [OK 27 rows]
✓ gold.fact_listings ................................ [OK 400 rows]
✓ gold.dm_host_neighbourhood ........................ [OK VIEW]
✓ gold.dm_listing_neighbourhood .................... [OK VIEW]
✓ gold.dm_property_type ............................ [OK VIEW]

Done. PASS=11 WARN=0 ERROR=0 TOTAL=11

=======================================================
PART 3: Sequential Monthly Ingestion & dbt Runs
=======================================================
Ingested months 06_2020 through 04_2021 sequentially.
Snapshot history accumulated:
- dim_host expanded to 1,668 historical versions
- fact_listings accumulated 4,800 monthly listing records
- SCD Type 2 timestamps maintained without data corruption.
```

---

## 7. Cloud Deployment Guide (GCP Cloud Composer & Cloud SQL)

To deploy this repository to production on Google Cloud:

1. **Cloud SQL (PostgreSQL)**:
   - Create instance (Postgres 15, db-f1-micro/db-custom-2-7680).
   - Run `sql/01_create_bronze_schema.sql` via DBeaver.
2. **Cloud Composer**:
   - Create Composer 2 environment (Small).
   - Set Airflow Connection `postgres_default` pointing to Cloud SQL host, port 5432, database `postgres`.
   - Copy `dags/load_airbnb_census_dag.py` into the environment's `dags/` GCS bucket.
   - Upload CSV datasets into `data/` in the GCS bucket.
3. **dbt Cloud**:
   - Connect repository `https://github.com/16aryan/AT3_BDE`.
   - Set project directory to `dbt_bde`.
   - Configure PostgreSQL credentials and trigger deployment runs (`dbt snapshot` then `dbt run`).
