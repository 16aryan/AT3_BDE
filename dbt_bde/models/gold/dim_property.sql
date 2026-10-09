-- Gold Dimension: Property (SCD Type 2)
{{ config(materialized='table') }}

SELECT
    dbt_scd_id AS property_sk,
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
    dbt_valid_from,
    dbt_valid_to,
    CASE WHEN dbt_valid_to IS NULL THEN TRUE ELSE FALSE END AS is_current
FROM {{ ref('snapshot_property') }}
