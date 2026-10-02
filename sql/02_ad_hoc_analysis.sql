-- ==============================================================================
-- UTS 36120: Big Data Engineering - Assignment 3
-- Script: 02_ad_hoc_analysis.sql
-- Description: Part 4 - Ad-Hoc Analytical SQL Queries against Gold / Datamarts
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Question A:
-- What are the demographic differences (e.g., age group distribution, household size)
-- between the top 3 performing and lowest 3 performing LGAs based on estimated
-- revenue per active listing over the last 12 months?
-- ------------------------------------------------------------------------------

WITH lga_performance AS (
    -- Calculate overall 12-month average estimated revenue per active listing by LGA
    SELECT
        s.lga_code,
        s.lga_name,
        COUNT(*) FILTER (WHERE f.has_availability = 't') AS total_active_listings,
        SUM(f.estimated_revenue) FILTER (WHERE f.has_availability = 't') AS total_revenue,
        ROUND(
            SUM(f.estimated_revenue) FILTER (WHERE f.has_availability = 't')::NUMERIC / 
            NULLIF(COUNT(*) FILTER (WHERE f.has_availability = 't'), 0)::NUMERIC, 
            2
        ) AS avg_revenue_per_active_listing
    FROM gold.fact_listings f
    JOIN gold.dim_property p 
        ON f.listing_id = p.listing_id 
        AND f.scraped_date >= p.dbt_valid_from 
        AND (f.scraped_date < p.dbt_valid_to OR p.dbt_valid_to IS NULL)
    JOIN gold.dim_suburb s 
        ON p.listing_neighbourhood = s.suburb_name
        AND f.scraped_date >= s.dbt_valid_from
        AND (f.scraped_date < s.dbt_valid_to OR s.dbt_valid_to IS NULL)
    WHERE s.lga_code IS NOT NULL AND s.lga_code != 'LGA_UNKNOWN'
    GROUP BY s.lga_code, s.lga_name
    HAVING COUNT(*) FILTER (WHERE f.has_availability = 't') > 50  -- Filter out LGAs with trivial sample size
),

ranked_lgas AS (
    SELECT
        *,
        DENSE_RANK() OVER (ORDER BY avg_revenue_per_active_listing DESC) AS rank_top,
        DENSE_RANK() OVER (ORDER BY avg_revenue_per_active_listing ASC) AS rank_bottom
    FROM lga_performance
),

top_and_bottom_lgas AS (
    SELECT 
        lga_code, 
        lga_name, 
        avg_revenue_per_active_listing,
        'Top 3' AS tier
    FROM ranked_lgas
    WHERE rank_top <= 3

    UNION ALL

    SELECT 
        lga_code, 
        lga_name, 
        avg_revenue_per_active_listing,
        'Bottom 3' AS tier
    FROM ranked_lgas
    WHERE rank_bottom <= 3
)

SELECT
    t.tier,
    t.lga_name,
    t.avg_revenue_per_active_listing,
    
    -- Demographics from Census G02 (Household size, Medians)
    g2.average_household_size,
    g2.median_age_persons,
    g2.median_tot_hhd_inc_weekly AS median_weekly_household_income,
    
    -- Age group distributions from Census G01 (%)
    ROUND(((g1.age_0_4_yr_p + g1.age_5_14_yr_p) / NULLIF(g1.tot_p_p, 0)) * 100.0, 1) AS pct_age_0_14,
    ROUND(((g1.age_15_19_yr_p + g1.age_20_24_yr_p) / NULLIF(g1.tot_p_p, 0)) * 100.0, 1) AS pct_age_15_24,
    ROUND((g1.age_25_34_yr_p / NULLIF(g1.tot_p_p, 0)) * 100.0, 1) AS pct_age_25_34,
    ROUND(((g1.age_35_44_yr_p + g1.age_45_54_yr_p) / NULLIF(g1.tot_p_p, 0)) * 100.0, 1) AS pct_age_35_54,
    ROUND(((g1.age_55_64_yr_p + g1.age_65_74_yr_p + g1.age_75_84_yr_p + g1.age_85ov_p) / NULLIF(g1.tot_p_p, 0)) * 100.0, 1) AS pct_age_55_plus

FROM top_and_bottom_lgas t
LEFT JOIN gold.census_g01 g1 ON t.lga_code = g1.lga_code
LEFT JOIN gold.census_g02 g2 ON t.lga_code = g2.lga_code
ORDER BY t.tier DESC, t.avg_revenue_per_active_listing DESC;


-- ------------------------------------------------------------------------------
-- Question B:
-- Is there a correlation between the median age of a neighbourhood (from Census data)
-- and the revenue generated per active listing in that neighbourhood?
-- ------------------------------------------------------------------------------

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
    JOIN gold.dim_property p 
        ON f.listing_id = p.listing_id 
        AND f.scraped_date >= p.dbt_valid_from 
        AND (f.scraped_date < p.dbt_valid_to OR p.dbt_valid_to IS NULL)
    JOIN gold.dim_suburb s 
        ON p.listing_neighbourhood = s.suburb_name
        AND f.scraped_date >= s.dbt_valid_from
        AND (f.scraped_date < s.dbt_valid_to OR s.dbt_valid_to IS NULL)
    WHERE s.lga_code IS NOT NULL AND s.lga_code != 'LGA_UNKNOWN'
    GROUP BY s.lga_code, s.lga_name
    HAVING COUNT(*) FILTER (WHERE f.has_availability = 't') > 10
),

joined_stats AS (
    SELECT
        r.lga_name,
        r.avg_revenue_per_active_listing,
        g2.median_age_persons
    FROM lga_revenue r
    JOIN gold.census_g02 g2 ON r.lga_code = g2.lga_code
    WHERE g2.median_age_persons > 0
)

-- 1. Pearson Correlation Coefficient
SELECT
    ROUND(CORR(avg_revenue_per_active_listing, median_age_persons)::NUMERIC, 4) AS pearson_correlation_coefficient,
    COUNT(*) AS total_lgas_compared,
    ROUND(AVG(avg_revenue_per_active_listing), 2) AS overall_avg_revenue,
    ROUND(AVG(median_age_persons), 1) AS overall_avg_median_age
FROM joined_stats;


-- ------------------------------------------------------------------------------
-- Question C:
-- What will be the best type of listing (property type, room type and accommodates for)
-- for the top 5 "listing_neighbourhood" (in terms of average estimated revenue per
-- active listing) to have the highest number of stays?
-- ------------------------------------------------------------------------------

WITH top_5_neighbourhoods AS (
    -- Step 1: Identify top 5 listing neighbourhoods by average estimated revenue per active listing
    SELECT
        listing_neighbourhood,
        ROUND(
            SUM(estimated_revenue) FILTER (WHERE has_availability = 't')::NUMERIC / 
            NULLIF(COUNT(*) FILTER (WHERE has_availability = 't'), 0)::NUMERIC, 
            2
        ) AS avg_revenue_per_active_listing
    FROM (
        SELECT
            f.has_availability,
            f.estimated_revenue,
            p.listing_neighbourhood
        FROM gold.fact_listings f
        JOIN gold.dim_property p 
            ON f.listing_id = p.listing_id 
            AND f.scraped_date >= p.dbt_valid_from 
            AND (f.scraped_date < p.dbt_valid_to OR p.dbt_valid_to IS NULL)
    ) sub
    WHERE listing_neighbourhood IS NOT NULL
    GROUP BY listing_neighbourhood
    ORDER BY avg_revenue_per_active_listing DESC
    LIMIT 5
),

configuration_stats AS (
    -- Step 2: Aggregate stays by listing configuration within those top 5 neighbourhoods
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
    JOIN gold.dim_property p 
        ON f.listing_id = p.listing_id 
        AND f.scraped_date >= p.dbt_valid_from 
        AND (f.scraped_date < p.dbt_valid_to OR p.dbt_valid_to IS NULL)
    WHERE p.listing_neighbourhood IN (SELECT listing_neighbourhood FROM top_5_neighbourhoods)
      AND f.has_availability = 't'
    GROUP BY p.listing_neighbourhood, p.property_type, p.room_type, p.accommodates
),

ranked_configurations AS (
    -- Step 3: Rank configurations within each top neighbourhood by total stays
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY listing_neighbourhood 
            ORDER BY total_stays DESC, avg_stays_per_listing DESC
        ) AS rank_in_neighbourhood
    FROM configuration_stats
)

-- Result: Best listing configuration for each of the top 5 neighbourhoods
SELECT
    t5.listing_neighbourhood,
    t5.avg_revenue_per_active_listing AS neighbourhood_avg_revenue,
    rc.property_type AS best_property_type,
    rc.room_type AS best_room_type,
    rc.accommodates AS best_accommodates,
    rc.total_stays AS total_stays_recorded,
    rc.avg_stays_per_listing,
    rc.avg_price,
    rc.distinct_listings
FROM top_5_neighbourhoods t5
JOIN ranked_configurations rc 
    ON t5.listing_neighbourhood = rc.listing_neighbourhood 
    AND rc.rank_in_neighbourhood = 1
ORDER BY t5.avg_revenue_per_active_listing DESC;
