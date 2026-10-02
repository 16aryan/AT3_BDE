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

WITH base_suburbs AS (
    SELECT DISTINCT ON (listing_neighbourhood, scraped_date)
        listing_neighbourhood AS suburb_name,
        scraped_date
    FROM {{ ref('stg_listings') }}
    WHERE listing_neighbourhood IS NOT NULL
    ORDER BY listing_neighbourhood, scraped_date DESC
),

mapping AS (
    SELECT DISTINCT
        LOWER(TRIM(suburb_name)) AS suburb_name,
        TRIM(lga_code) AS lga_code,
        TRIM(lga_name) AS lga_name
    FROM {{ source('bronze', 'raw_lga_suburb') }}
)

SELECT
    b.suburb_name,
    COALESCE(m.lga_code, 'LGA_UNKNOWN') AS lga_code,
    COALESCE(m.lga_name, 'Unknown LGA') AS lga_name,
    b.scraped_date
FROM base_suburbs b
LEFT JOIN mapping m ON b.suburb_name = m.suburb_name

{% endsnapshot %}
