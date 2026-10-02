-- Gold Dimension: Suburb & LGA Mapping (SCD Type 2)
{{ config(materialized='table') }}

SELECT
    dbt_scd_id AS suburb_sk,
    suburb_name,
    lga_code,
    lga_name,
    dbt_valid_from,
    dbt_valid_to,
    CASE WHEN dbt_valid_to IS NULL THEN TRUE ELSE FALSE END AS is_current
FROM {{ ref('snapshot_suburb_lga') }}
