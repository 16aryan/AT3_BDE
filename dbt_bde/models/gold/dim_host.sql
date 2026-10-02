-- Gold Dimension: Host (SCD Type 2)
{{ config(materialized='table') }}

SELECT
    dbt_scd_id AS host_sk,
    host_id,
    host_name,
    host_since,
    host_location,
    host_is_superhost,
    host_neighbourhood,
    host_listings_count,
    dbt_valid_from,
    dbt_valid_to,
    CASE WHEN dbt_valid_to IS NULL THEN TRUE ELSE FALSE END AS is_current
FROM {{ ref('snapshot_host') }}
