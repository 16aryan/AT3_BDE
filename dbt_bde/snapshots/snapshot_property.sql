{% snapshot snapshot_property %}

{{
    config(
        target_schema='silver',
        unique_key='listing_id',
        strategy='timestamp',
        updated_at='scraped_date',
        invalidate_hard_deletes=True
    )
}}

WITH state_marked AS (
    SELECT
        listing_id,
        listing_name,
        property_type,
        room_type,
        accommodates,
        bathrooms,
        bedrooms,
        beds,
        listing_neighbourhood,
        has_availability,
        scraped_date,
        CASE 
            WHEN LAG(MD5(CONCAT_WS('|', listing_name, property_type, room_type, accommodates, bathrooms, bedrooms, beds, listing_neighbourhood, has_availability)))
                 OVER (PARTITION BY listing_id ORDER BY scraped_date) 
                 = MD5(CONCAT_WS('|', listing_name, property_type, room_type, accommodates, bathrooms, bedrooms, beds, listing_neighbourhood, has_availability))
            THEN 0
            ELSE 1
        END AS is_new_state
    FROM {{ ref('stg_listings') }}
    WHERE listing_id IS NOT NULL
),

state_grouped AS (
    SELECT
        *,
        SUM(is_new_state) OVER (PARTITION BY listing_id ORDER BY scraped_date) AS state_group
    FROM state_marked
),

state_with_start AS (
    SELECT
        listing_id,
        listing_name,
        property_type,
        room_type,
        accommodates,
        bathrooms,
        bedrooms,
        beds,
        listing_neighbourhood,
        has_availability,
        scraped_date,
        FIRST_VALUE(scraped_date) OVER (PARTITION BY listing_id, state_group ORDER BY scraped_date) AS state_start_date
    FROM state_grouped
)

SELECT DISTINCT ON (listing_id)
    listing_id,
    listing_name,
    property_type,
    room_type,
    accommodates,
    bathrooms,
    bedrooms,
    beds,
    listing_neighbourhood,
    has_availability,
    state_start_date AS scraped_date
FROM state_with_start
ORDER BY listing_id, scraped_date DESC

{% endsnapshot %}
