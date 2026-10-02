-- Gold Reference: 2016 ABS Census G01 (Person Characteristics by Sex & Age)
{{ config(materialized='table') }}

SELECT
    TRIM(lga_code) AS lga_code,
    COALESCE(NULLIF(TRIM(tot_p_m), '')::NUMERIC, 0) AS tot_p_m,
    COALESCE(NULLIF(TRIM(tot_p_f), '')::NUMERIC, 0) AS tot_p_f,
    COALESCE(NULLIF(TRIM(tot_p_p), '')::NUMERIC, 0) AS tot_p_p,
    COALESCE(NULLIF(TRIM(age_0_4_yr_p), '')::NUMERIC, 0) AS age_0_4_yr_p,
    COALESCE(NULLIF(TRIM(age_5_14_yr_p), '')::NUMERIC, 0) AS age_5_14_yr_p,
    COALESCE(NULLIF(TRIM(age_15_19_yr_p), '')::NUMERIC, 0) AS age_15_19_yr_p,
    COALESCE(NULLIF(TRIM(age_20_24_yr_p), '')::NUMERIC, 0) AS age_20_24_yr_p,
    COALESCE(NULLIF(TRIM(age_25_34_yr_p), '')::NUMERIC, 0) AS age_25_34_yr_p,
    COALESCE(NULLIF(TRIM(age_35_44_yr_p), '')::NUMERIC, 0) AS age_35_44_yr_p,
    COALESCE(NULLIF(TRIM(age_45_54_yr_p), '')::NUMERIC, 0) AS age_45_54_yr_p,
    COALESCE(NULLIF(TRIM(age_55_64_yr_p), '')::NUMERIC, 0) AS age_55_64_yr_p,
    COALESCE(NULLIF(TRIM(age_65_74_yr_p), '')::NUMERIC, 0) AS age_65_74_yr_p,
    COALESCE(NULLIF(TRIM(age_75_84_yr_p), '')::NUMERIC, 0) AS age_75_84_yr_p,
    COALESCE(NULLIF(TRIM(age_85ov_p), '')::NUMERIC, 0) AS age_85ov_p
FROM {{ source('bronze', 'raw_census_g01') }}
WHERE lga_code IS NOT NULL AND TRIM(lga_code) != ''
