{% snapshot snapshot_host %}

{{
    config(
        target_schema='silver',
        unique_key='host_id',
        strategy='timestamp',
        updated_at='scraped_date',
        invalidate_hard_deletes=True
    )
}}

WITH distinct_host_months AS (
    SELECT DISTINCT ON (host_id, DATE_TRUNC('month', scraped_date))
        host_id, host_name, host_since, host_location, host_is_superhost, host_neighbourhood, host_listings_count, scraped_date
    FROM {{ ref('stg_listings') }}
    WHERE host_id IS NOT NULL
    ORDER BY host_id, DATE_TRUNC('month', scraped_date), scraped_date
),

state_marked AS (
    SELECT 
        host_id, host_name, host_since, host_location, host_is_superhost, host_neighbourhood, host_listings_count, scraped_date,
        CASE 
            WHEN LAG(MD5(CONCAT_WS('|', host_name, host_since, host_location, host_is_superhost, host_neighbourhood)))
                 OVER (PARTITION BY host_id ORDER BY scraped_date) 
                 = MD5(CONCAT_WS('|', host_name, host_since, host_location, host_is_superhost, host_neighbourhood))
            THEN 0
            ELSE 1
        END AS is_new_state
    FROM distinct_host_months
),

state_grouped AS (
    SELECT
        *,
        SUM(is_new_state) OVER (PARTITION BY host_id ORDER BY scraped_date) AS state_group
    FROM state_marked
),

state_with_start AS (
    SELECT
        host_id,
        host_name,
        host_since,
        host_location,
        host_is_superhost,
        host_neighbourhood,
        host_listings_count,
        scraped_date,
        FIRST_VALUE(scraped_date) OVER (PARTITION BY host_id, state_group ORDER BY scraped_date) AS state_start_date
    FROM state_grouped
)

SELECT DISTINCT ON (host_id)
    host_id,
    host_name,
    host_since,
    host_location,
    host_is_superhost,
    host_neighbourhood,
    host_listings_count,
    state_start_date AS scraped_date
FROM state_with_start
ORDER BY host_id, scraped_date DESC

{% endsnapshot %}
