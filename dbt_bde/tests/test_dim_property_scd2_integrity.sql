-- Assert that closed SCD Type 2 dimension records have dbt_valid_to >= dbt_valid_from
SELECT
    property_sk,
    listing_id,
    dbt_valid_from,
    dbt_valid_to
FROM {{ ref('dim_property') }}
WHERE dbt_valid_to IS NOT NULL 
  AND dbt_valid_to < dbt_valid_from
