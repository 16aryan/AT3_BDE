-- Gold Reference: 2016 ABS Census G02 (Selected Medians and Averages)
{{ config(materialized='table') }}

SELECT
    REGEXP_REPLACE(TRIM(lga_code_2016), '^LGA', '') AS lga_code,
    TRIM(lga_code_2016) AS lga_code_2016,
    COALESCE(NULLIF(TRIM(median_age_persons), '')::NUMERIC, 0) AS median_age_persons,
    COALESCE(NULLIF(TRIM(median_mortgage_repay_monthly), '')::NUMERIC, 0) AS median_mortgage_repay_monthly,
    COALESCE(NULLIF(TRIM(median_tot_prsnl_inc_weekly), '')::NUMERIC, 0) AS median_tot_prsnl_inc_weekly,
    COALESCE(NULLIF(TRIM(median_rent_weekly), '')::NUMERIC, 0) AS median_rent_weekly,
    COALESCE(NULLIF(TRIM(median_tot_fam_inc_weekly), '')::NUMERIC, 0) AS median_tot_fam_inc_weekly,
    COALESCE(NULLIF(TRIM(average_num_psns_per_bedroom), '')::NUMERIC, 0) AS average_num_psns_per_bedroom,
    COALESCE(NULLIF(TRIM(median_tot_hhd_inc_weekly), '')::NUMERIC, 0) AS median_tot_hhd_inc_weekly,
    COALESCE(NULLIF(TRIM(average_household_size), '')::NUMERIC, 0) AS average_household_size
FROM {{ source('bronze', 'raw_census_g02') }}
WHERE lga_code_2016 IS NOT NULL AND TRIM(lga_code_2016) != ''
