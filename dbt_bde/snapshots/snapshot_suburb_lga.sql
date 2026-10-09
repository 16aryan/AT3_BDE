{% snapshot snapshot_suburb_lga %}

{{
    config(
        target_schema='silver',
        unique_key='suburb_name',
        strategy='timestamp',
        updated_at='scraped_date',
        invalidate_hard_deletes=True
    )
}}

WITH min_scrape AS (
    SELECT DATE '2020-01-01' AS scraped_date
),

lga_mapping AS (
    -- Priority 1: Match directly against LGA name (since Inside Airbnb listing_neighbourhood uses LGAs)
    SELECT DISTINCT
        LOWER(TRIM(lga_name)) AS match_name,
        TRIM(lga_name) AS suburb_name,
        TRIM(lga_code) AS lga_code,
        TRIM(lga_name) AS lga_name,
        1 AS priority
    FROM {{ source('bronze', 'raw_lga_suburb') }}
    WHERE lga_name IS NOT NULL AND TRIM(lga_name) != ''
    UNION ALL
    -- Priority 2: Individual Suburbs from NSW LGA Suburb mapping
    SELECT DISTINCT
        LOWER(TRIM(suburb_name)) AS match_name,
        INITCAP(TRIM(suburb_name)) AS suburb_name,
        TRIM(lga_code) AS lga_code,
        TRIM(lga_name) AS lga_name,
        2 AS priority
    FROM {{ source('bronze', 'raw_lga_suburb') }}
    WHERE suburb_name IS NOT NULL AND TRIM(suburb_name) != ''
),

dedup_mapping AS (
    SELECT DISTINCT ON (match_name)
        suburb_name,
        lga_code,
        lga_name
    FROM lga_mapping
    ORDER BY match_name, priority ASC
)

SELECT
    d.suburb_name,
    d.lga_code,
    d.lga_name,
    m.scraped_date
FROM dedup_mapping d
CROSS JOIN min_scrape m

{% endsnapshot %}
