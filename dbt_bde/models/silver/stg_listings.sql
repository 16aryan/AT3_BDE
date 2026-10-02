-- Cleaned staging model for raw listings
{{ config(materialized='view') }}

WITH raw AS (
    SELECT * FROM {{ source('bronze', 'raw_listings') }}
),

cleaned AS (
    SELECT
        -- Primary & Foreign Keys
        id::BIGINT AS listing_id,
        NULLIF(TRIM(scrape_id), '')::BIGINT AS scrape_id,
        NULLIF(TRIM(host_id), '')::BIGINT AS host_id,

        -- Scrape Date / Timestamp Handling
        -- Handles both ISO formats and standard YYYY-MM-DD
        COALESCE(
            CASE 
                WHEN last_scraped ~ '^\d{4}-\d{2}-\d{2}' THEN last_scraped::DATE 
                ELSE NULL 
            END,
            CURRENT_DATE
        ) AS scraped_date,

        -- Year-Month for temporal grouping
        TO_CHAR(
            COALESCE(
                CASE 
                    WHEN last_scraped ~ '^\d{4}-\d{2}-\d{2}' THEN last_scraped::DATE 
                    ELSE NULL 
                END, 
                CURRENT_DATE
            ), 
            'YYYY-MM'
        ) AS month_year,

        -- Listing & Property Attributes
        TRIM(name) AS listing_name,
        TRIM(property_type) AS property_type,
        TRIM(room_type) AS room_type,
        COALESCE(NULLIF(TRIM(accommodates), '')::INT, 0) AS accommodates,
        COALESCE(NULLIF(TRIM(bathrooms), '')::NUMERIC, NULLIF(TRIM(REGEXP_REPLACE(bathrooms_text, '[^0-9.]', '', 'g')), '')::NUMERIC, 0) AS bathrooms,
        COALESCE(NULLIF(TRIM(bedrooms), '')::INT, 0) AS bedrooms,
        COALESCE(NULLIF(TRIM(beds), '')::INT, 0) AS beds,

        -- Neighbourhood fields
        LOWER(TRIM(COALESCE(neighbourhood_cleansed, neighbourhood))) AS listing_neighbourhood,
        LOWER(TRIM(host_neighbourhood)) AS host_neighbourhood,

        -- Host Attributes
        TRIM(host_name) AS host_name,
        CASE 
            WHEN host_since ~ '^\d{4}-\d{2}-\d{2}' THEN host_since::DATE 
            ELSE NULL 
        END AS host_since,
        TRIM(host_location) AS host_location,
        CASE 
            WHEN LOWER(TRIM(host_is_superhost)) IN ('t', 'true', '1') THEN 't' 
            ELSE 'f' 
        END AS host_is_superhost,
        COALESCE(NULLIF(TRIM(host_listings_count), '')::INT, 1) AS host_listings_count,

        -- Availability & Pricing Metrics
        CASE 
            WHEN LOWER(TRIM(has_availability)) IN ('t', 'true', '1') THEN 't' 
            ELSE 'f' 
        END AS has_availability,
        
        COALESCE(NULLIF(TRIM(availability_30), '')::INT, 0) AS availability_30,

        -- Clean price: strip '$' and commas
        COALESCE(
            NULLIF(TRIM(REGEXP_REPLACE(price, '[^0-9.]', '', 'g')), '')::NUMERIC, 
            0.0
        ) AS price,

        -- Review Scores
        NULLIF(TRIM(review_scores_rating), '')::NUMERIC AS review_scores_rating,
        COALESCE(NULLIF(TRIM(number_of_reviews), '')::INT, 0) AS number_of_reviews,

        file_source,
        ingestion_timestamp
    FROM raw
    WHERE id IS NOT NULL AND TRIM(id) != ''
)

SELECT * FROM cleaned
