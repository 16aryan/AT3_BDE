-- Datamart View 3: dm_host_neighbourhood
-- Insights per host_neighbourhood_lga and month/year with SCD2 dimension joining logic
{{ config(materialized='view') }}

WITH fact_joined_scd2 AS (
    SELECT
        f.listing_id,
        f.host_id,
        f.scraped_date,
        TO_CHAR(f.scraped_date, 'YYYY-MM') AS month_year,
        p.has_availability,
        f.price,
        f.availability_30,
        f.number_of_stays,
        f.estimated_revenue,
        -- SCD2 joined host attributes:
        h.host_neighbourhood
    FROM {{ ref('fact_listings') }} f
    -- Join Property Dimension for availability status
    LEFT JOIN {{ ref('dim_property') }} p
        ON f.listing_id = p.listing_id
        AND f.scraped_date >= p.dbt_valid_from
        AND (f.scraped_date < p.dbt_valid_to OR p.dbt_valid_to IS NULL)
    -- Join Host Dimension using SCD Type 2 point-in-time validity
    LEFT JOIN {{ ref('dim_host') }} h
        ON f.host_id = h.host_id
        AND f.scraped_date >= h.dbt_valid_from
        AND (f.scraped_date < h.dbt_valid_to OR h.dbt_valid_to IS NULL)
),

with_lga AS (
    SELECT
        fj.*,
        -- Map host_neighbourhood (suburb) to LGA name using suburb dimension or fallback
        COALESCE(s.lga_name, 'Unknown LGA') AS host_neighbourhood_lga
    FROM fact_joined_scd2 fj
    LEFT JOIN {{ ref('dim_suburb') }} s
        ON LOWER(TRIM(fj.host_neighbourhood)) = LOWER(TRIM(s.suburb_name))
        AND fj.scraped_date >= s.dbt_valid_from
        AND (fj.scraped_date < s.dbt_valid_to OR s.dbt_valid_to IS NULL)
),

aggregated AS (
    SELECT
        host_neighbourhood_lga,
        month_year,
        
        -- Distinct hosts in this LGA & month
        COUNT(DISTINCT host_id) AS number_of_distinct_hosts,
        
        -- Active listings count
        COUNT(*) FILTER (WHERE has_availability = 't') AS active_listings,
        
        -- Total estimated revenue for active listings
        SUM(estimated_revenue) FILTER (WHERE has_availability = 't') AS total_estimated_revenue_active
    FROM with_lga
    WHERE host_neighbourhood_lga IS NOT NULL
    GROUP BY host_neighbourhood_lga, month_year
)

SELECT
    host_neighbourhood_lga,
    month_year,
    
    -- 1. Number of distinct host
    number_of_distinct_hosts,
    
    -- 2. Average Estimated Revenue per active listings
    ROUND(
        (total_estimated_revenue_active::NUMERIC / NULLIF(active_listings, 0)::NUMERIC), 
        2
    ) AS avg_estimated_revenue_active,
    
    -- 3. Estimated Revenue per host (distinct) = Total Estimated revenue / total distinct hosts
    ROUND(
        (total_estimated_revenue_active::NUMERIC / NULLIF(number_of_distinct_hosts, 0)::NUMERIC), 
        2
    ) AS estimated_revenue_per_host

FROM aggregated
ORDER BY host_neighbourhood_lga, month_year
