-- Cleaned staging model for raw listings
{{ config(materialized='view') }}

WITH raw AS (
    SELECT * FROM {{ source('bronze', 'raw_listings') }}
),

parsed_dates AS (
    SELECT
        *,
        -- Derive canonical month_year strictly from source filename (e.g. '07_2020.csv' -> '2020-07')
        SUBSTRING(file_source FROM 4 FOR 4) || '-' || SUBSTRING(file_source FROM 1 FOR 2) AS file_month_year,
        COALESCE(
            CASE 
                WHEN scraped_date ~ '^\d{4}-\d{2}-\d{2}' THEN scraped_date::DATE 
                WHEN scraped_date ~ '^\d{1,2}/\d{1,2}/\d{4}' THEN TO_DATE(scraped_date, 'DD/MM/YYYY')
                ELSE NULL 
            END,
            CURRENT_DATE
        ) AS parsed_scraped_date
    FROM raw
    WHERE listing_id IS NOT NULL AND TRIM(listing_id) != ''
),

cleaned AS (
    SELECT
        -- Primary & Foreign Keys
        listing_id::BIGINT AS listing_id,
        NULLIF(TRIM(scrape_id), '')::BIGINT AS scrape_id,
        NULLIF(TRIM(host_id), '')::BIGINT AS host_id,

        -- Correct out-of-month scrape dates to the file's primary scrape date (e.g., 07_2020 Sept anomaly)
        CASE 
            WHEN TO_CHAR(parsed_scraped_date, 'YYYY-MM') != file_month_year 
            THEN (file_month_year || '-14')::DATE
            ELSE parsed_scraped_date 
        END AS scraped_date,

        file_month_year AS month_year,

        -- Standardized Property Type: harmonize pre-August generic categories with post-August specific ones
        CASE 
            WHEN property_type ILIKE 'Entire %' OR property_type ILIKE 'Private room%' OR property_type ILIKE 'Shared room%' OR property_type ILIKE 'Room in %' 
                THEN TRIM(property_type)
            WHEN room_type = 'Entire home/apt' 
                THEN 'Entire ' || LOWER(TRIM(property_type))
            WHEN room_type = 'Private room' 
                THEN 'Private room in ' || LOWER(TRIM(property_type))
            WHEN room_type = 'Shared room' 
                THEN 'Shared room in ' || LOWER(TRIM(property_type))
            WHEN room_type = 'Hotel room'
                THEN 'Room in ' || LOWER(TRIM(property_type))
            WHEN LOWER(TRIM(property_type)) IN ('hotel', 'boutique hotel', 'hostel', 'serviced apartment', 'bed and breakfast', 'aparthotel', 'resort')
                THEN 'Room in ' || LOWER(TRIM(property_type))
            ELSE TRIM(property_type)
        END AS property_type,

        TRIM(room_type) AS room_type,
        CONCAT(
            CASE 
                WHEN property_type ILIKE 'Entire %' OR property_type ILIKE 'Private room%' OR property_type ILIKE 'Shared room%' OR property_type ILIKE 'Room in %' 
                    THEN TRIM(property_type)
                WHEN room_type = 'Entire home/apt' 
                    THEN 'Entire ' || LOWER(TRIM(property_type))
                WHEN room_type = 'Private room' 
                    THEN 'Private room in ' || LOWER(TRIM(property_type))
                WHEN room_type = 'Shared room' 
                    THEN 'Shared room in ' || LOWER(TRIM(property_type))
                WHEN room_type = 'Hotel room'
                    THEN 'Room in ' || LOWER(TRIM(property_type))
                WHEN LOWER(TRIM(property_type)) IN ('hotel', 'boutique hotel', 'hostel', 'serviced apartment', 'bed and breakfast', 'aparthotel', 'resort')
                    THEN 'Room in ' || LOWER(TRIM(property_type))
                ELSE TRIM(property_type)
            END, 
            ' in ', 
            TRIM(listing_neighbourhood)
        ) AS listing_name,

        COALESCE(NULLIF(TRIM(accommodates), '')::INT, 0) AS accommodates,
        NULL::NUMERIC AS bathrooms,
        NULL::INT AS bedrooms,
        NULL::INT AS beds,

        -- Neighbourhood fields (listing_neighbourhood corresponds to Sydney LGA)
        TRIM(listing_neighbourhood) AS listing_neighbourhood,
        TRIM(host_neighbourhood) AS host_neighbourhood,

        -- Host Attributes
        TRIM(host_name) AS host_name,
        CASE 
            WHEN host_since ~ '^\d{1,2}/\d{1,2}/\d{4}' THEN TO_DATE(host_since, 'DD/MM/YYYY')
            WHEN host_since ~ '^\d{4}-\d{2}-\d{2}' THEN host_since::DATE 
            ELSE NULL 
        END AS host_since,
        NULL::TEXT AS host_location,
        CASE 
            WHEN LOWER(TRIM(host_is_superhost)) IN ('t', 'true', '1') THEN 't' 
            ELSE 'f' 
        END AS host_is_superhost,
        COALESCE(COUNT(listing_id) OVER (PARTITION BY host_id, file_month_year), 1)::INT AS host_listings_count,

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
        NULLIF(TRIM(review_scores_accuracy), '')::NUMERIC AS review_scores_accuracy,
        NULLIF(TRIM(review_scores_cleanliness), '')::NUMERIC AS review_scores_cleanliness,
        NULLIF(TRIM(review_scores_checkin), '')::NUMERIC AS review_scores_checkin,
        NULLIF(TRIM(review_scores_communication), '')::NUMERIC AS review_scores_communication,
        NULLIF(TRIM(review_scores_value), '')::NUMERIC AS review_scores_value,
        COALESCE(NULLIF(TRIM(number_of_reviews), '')::INT, 0) AS number_of_reviews,

        file_source,
        ingestion_timestamp
    FROM parsed_dates
),

deduped AS (
    SELECT DISTINCT ON (listing_id, scraped_date) *
    FROM cleaned
    ORDER BY listing_id, scraped_date, ingestion_timestamp DESC NULLS LAST
)

SELECT * FROM deduped
