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

SELECT DISTINCT ON (listing_id, scraped_date)
    listing_id,
    listing_name,
    property_type,
    room_type,
    accommodates,
    bathrooms,
    bedrooms,
    beds,
    listing_neighbourhood,
    scraped_date
FROM {{ ref('stg_listings') }}
WHERE listing_id IS NOT NULL
ORDER BY listing_id, scraped_date DESC

{% endsnapshot %}
