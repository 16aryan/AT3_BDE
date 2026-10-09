-- Datamart View 2: dm_property_type
-- Insights per property_type, room_type, accommodates, and month/year with SCD2 dimension joining logic
{{ config(materialized='view') }}

WITH fact_joined_scd2 AS (
    SELECT
        f.listing_id,
        f.host_id,
        TO_CHAR(f.scraped_date, 'YYYY-MM') AS month_year,
        p.has_availability,
        f.price,
        f.availability_30,
        f.review_scores_rating,
        f.number_of_stays,
        f.estimated_revenue,
        -- SCD2 joined dimension attributes:
        p.property_type,
        p.room_type,
        p.accommodates,
        h.host_is_superhost
    FROM {{ ref('fact_listings') }} f
    -- Join Property Dimension using SCD Type 2 point-in-time validity
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

monthly_aggregated AS (
    SELECT
        COALESCE(property_type, 'Unknown') AS property_type,
        COALESCE(room_type, 'Unknown') AS room_type,
        COALESCE(accommodates, 0) AS accommodates,
        month_year,
        
        -- Listing counts
        COUNT(*) AS total_listings,
        COUNT(*) FILTER (WHERE has_availability = 't') AS active_listings,
        COUNT(*) FILTER (WHERE has_availability = 'f') AS inactive_listings,
        
        -- Host counts & Superhost
        COUNT(DISTINCT host_id) AS distinct_hosts,
        COUNT(DISTINCT host_id) FILTER (WHERE host_is_superhost = 't') AS superhosts,
        
        -- Price statistics for active listings
        MIN(price) FILTER (WHERE has_availability = 't') AS min_price_active,
        MAX(price) FILTER (WHERE has_availability = 't') AS max_price_active,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price) FILTER (WHERE has_availability = 't') AS median_price_active,
        AVG(price) FILTER (WHERE has_availability = 't') AS avg_price_active,
        
        -- Review score for active listings
        AVG(review_scores_rating) FILTER (WHERE has_availability = 't') AS avg_review_scores_rating_active,
        
        -- Total stays for active listings
        SUM(number_of_stays) FILTER (WHERE has_availability = 't') AS total_number_of_stays,
        
        -- Estimated revenue
        SUM(estimated_revenue) FILTER (WHERE has_availability = 't') AS total_estimated_revenue_active
    FROM fact_joined_scd2
    GROUP BY property_type, room_type, accommodates, month_year
),

with_mom AS (
    SELECT
        property_type,
        room_type,
        accommodates,
        month_year,
        
        -- Active listings rate = (total Active listings / total listing) * 100
        ROUND(
            (active_listings::NUMERIC / NULLIF(total_listings, 0)::NUMERIC) * 100.0, 
            2
        ) AS active_listings_rate,

        -- Min, Max, Median, Avg price for active listings
        ROUND(min_price_active, 2) AS min_price_active,
        ROUND(max_price_active, 2) AS max_price_active,
        ROUND(median_price_active::NUMERIC, 2) AS median_price_active,
        ROUND(avg_price_active, 2) AS avg_price_active,

        -- Distinct hosts
        distinct_hosts AS number_of_distinct_hosts,

        -- Superhost rate = (distinct superhosts / distinct hosts) * 100
        ROUND(
            (superhosts::NUMERIC / NULLIF(distinct_hosts, 0)::NUMERIC) * 100.0, 
            2
        ) AS superhost_rate,

        -- Avg review scores rating for active listings
        ROUND(avg_review_scores_rating_active, 2) AS avg_review_scores_rating_active,

        -- Percentage change for active listings (MoM) = ((final - original) / original) * 100
        ROUND(
            ((active_listings::NUMERIC - LAG(active_listings) OVER (
                PARTITION BY property_type, room_type, accommodates ORDER BY month_year
            )::NUMERIC) 
            / NULLIF(LAG(active_listings) OVER (
                PARTITION BY property_type, room_type, accommodates ORDER BY month_year
            ), 0)::NUMERIC) * 100.0,
            2
        ) AS pct_change_active_listings,

        -- Percentage change for inactive listings (MoM)
        ROUND(
            ((inactive_listings::NUMERIC - LAG(inactive_listings) OVER (
                PARTITION BY property_type, room_type, accommodates ORDER BY month_year
            )::NUMERIC) 
            / NULLIF(LAG(inactive_listings) OVER (
                PARTITION BY property_type, room_type, accommodates ORDER BY month_year
            ), 0)::NUMERIC) * 100.0,
            2
        ) AS pct_change_inactive_listings,

        -- Total number of stays
        COALESCE(total_number_of_stays, 0) AS total_number_of_stays,

        -- Average Estimated revenue per active listings
        ROUND(
            (total_estimated_revenue_active::NUMERIC / NULLIF(active_listings, 0)::NUMERIC), 
            2
        ) AS avg_estimated_revenue_active

    FROM monthly_aggregated
)

SELECT * 
FROM with_mom
ORDER BY property_type, room_type, accommodates, month_year
