-- ==============================================================================
-- UTS 36120: Big Data Engineering - Assignment 3
-- Script: part_1.sql (also 01_create_bronze_schema.sql)
-- Description: Sets up the Bronze (raw) schema and tables in PostgreSQL
-- ==============================================================================

-- 1. Create Bronze, Silver, and Gold Schemas
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;

-- 2. Raw Airbnb Listings Table
-- Ingests raw data from monthly Airbnb CSVs (05_2020.csv to 04_2021.csv)
-- Exactly matching the 22 provided attributes + lineage metadata
DROP TABLE IF EXISTS bronze.raw_listings CASCADE;
CREATE TABLE bronze.raw_listings (
    listing_id TEXT,
    scrape_id TEXT,
    scraped_date TEXT,
    host_id TEXT,
    host_name TEXT,
    host_since TEXT,
    host_is_superhost TEXT,
    host_neighbourhood TEXT,
    listing_neighbourhood TEXT,
    property_type TEXT,
    room_type TEXT,
    accommodates TEXT,
    price TEXT,
    has_availability TEXT,
    availability_30 TEXT,
    number_of_reviews TEXT,
    review_scores_rating TEXT,
    review_scores_accuracy TEXT,
    review_scores_cleanliness TEXT,
    review_scores_checkin TEXT,
    review_scores_communication TEXT,
    review_scores_value TEXT,
    -- Audit metadata added by ingestion pipeline:
    file_source TEXT,
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Raw Census G01 Table ("Selected Person Characteristics by Sex")
DROP TABLE IF EXISTS bronze.raw_census_g01 CASCADE;
CREATE TABLE bronze.raw_census_g01 (
    lga_code_2016 TEXT,
    tot_p_m TEXT,
    tot_p_f TEXT,
    tot_p_p TEXT,
    age_0_4_yr_m TEXT,
    age_0_4_yr_f TEXT,
    age_0_4_yr_p TEXT,
    age_5_14_yr_m TEXT,
    age_5_14_yr_f TEXT,
    age_5_14_yr_p TEXT,
    age_15_19_yr_m TEXT,
    age_15_19_yr_f TEXT,
    age_15_19_yr_p TEXT,
    age_20_24_yr_m TEXT,
    age_20_24_yr_f TEXT,
    age_20_24_yr_p TEXT,
    age_25_34_yr_m TEXT,
    age_25_34_yr_f TEXT,
    age_25_34_yr_p TEXT,
    age_35_44_yr_m TEXT,
    age_35_44_yr_f TEXT,
    age_35_44_yr_p TEXT,
    age_45_54_yr_m TEXT,
    age_45_54_yr_f TEXT,
    age_45_54_yr_p TEXT,
    age_55_64_yr_m TEXT,
    age_55_64_yr_f TEXT,
    age_55_64_yr_p TEXT,
    age_65_74_yr_m TEXT,
    age_65_74_yr_f TEXT,
    age_65_74_yr_p TEXT,
    age_75_84_yr_m TEXT,
    age_75_84_yr_f TEXT,
    age_75_84_yr_p TEXT,
    age_85ov_m TEXT,
    age_85ov_f TEXT,
    age_85ov_p TEXT,
    counted_census_night_home_m TEXT,
    counted_census_night_home_f TEXT,
    counted_census_night_home_p TEXT,
    counted_census_night_away_m TEXT,
    counted_census_night_away_f TEXT,
    counted_census_night_away_p TEXT,
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Raw Census G02 Table ("Selected Medians and Averages")
DROP TABLE IF EXISTS bronze.raw_census_g02 CASCADE;
CREATE TABLE bronze.raw_census_g02 (
    lga_code_2016 TEXT,
    median_age_persons TEXT,
    median_mortgage_repay_monthly TEXT,
    median_tot_prsnl_inc_weekly TEXT,
    median_rent_weekly TEXT,
    median_tot_fam_inc_weekly TEXT,
    average_num_psns_per_bedroom TEXT,
    median_tot_hhd_inc_weekly TEXT,
    average_household_size TEXT,
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Raw LGA and Suburb Mapping Table
DROP TABLE IF EXISTS bronze.raw_lga_suburb CASCADE;
CREATE TABLE bronze.raw_lga_suburb (
    lga_code TEXT,
    lga_name TEXT,
    suburb_name TEXT,
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Utility Command to Truncate All Bronze Tables (Per Assignment Advice)
-- TRUNCATE TABLE bronze.raw_listings;
-- TRUNCATE TABLE bronze.raw_census_g01;
-- TRUNCATE TABLE bronze.raw_census_g02;
-- TRUNCATE TABLE bronze.raw_lga_suburb;
