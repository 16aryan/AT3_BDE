-- Gold Fact: Fact Listings
-- Star Schema Fact table containing ONLY IDs, dates, and metrics
{{ config(materialized='table') }}

WITH stg AS (
    SELECT * FROM {{ ref('stg_listings') }}
)

SELECT
    -- Degenerate / Grain Identifier
    MD5(CONCAT(listing_id::TEXT, '-', scraped_date::TEXT)) AS fact_listing_id,

    -- Foreign Keys & Dates (Point-in-time reference for SCD2 joins)
    listing_id,
    host_id,
    scraped_date,
    month_year,

    -- Attributes / Flags
    has_availability,

    -- Metrics
    price,
    availability_30,
    review_scores_rating,
    number_of_reviews,

    -- Assignment-specific derived metrics:
    -- Number of stays (only for active listings) = 30 - availability_30
    CASE 
        WHEN has_availability = 't' THEN GREATEST(30 - availability_30, 0)
        ELSE 0
    END AS number_of_stays,

    -- Estimated revenue per active listing = stays * price
    CASE 
        WHEN has_availability = 't' THEN GREATEST(30 - availability_30, 0) * price
        ELSE 0.0
    END AS estimated_revenue

FROM stg
