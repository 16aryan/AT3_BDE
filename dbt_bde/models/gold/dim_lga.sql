-- Gold Dimension: LGA
{{ config(materialized='table') }}

WITH distinct_lgas AS (
    SELECT DISTINCT
        TRIM(lga_code) AS lga_code,
        TRIM(lga_name) AS lga_name
    FROM {{ source('bronze', 'raw_lga_suburb') }}
    WHERE lga_code IS NOT NULL AND TRIM(lga_code) != ''
)

SELECT
    MD5(lga_code) AS lga_sk,
    lga_code,
    lga_name
FROM distinct_lgas
