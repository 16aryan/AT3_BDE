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

SELECT DISTINCT ON (host_id, scraped_date)
    host_id,
    host_name,
    host_since,
    host_location,
    host_is_superhost,
    host_neighbourhood,
    host_listings_count,
    scraped_date
FROM {{ ref('stg_listings') }}
WHERE host_id IS NOT NULL
ORDER BY host_id, scraped_date DESC

{% endsnapshot %}
