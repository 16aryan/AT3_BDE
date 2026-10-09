-- Assert that all fact records fall within the 12-month study timeframe (2020-05 to 2021-04)
SELECT
    fact_listing_id,
    listing_id,
    scraped_date
FROM {{ ref('fact_listings') }}
WHERE scraped_date < '2020-05-01'::DATE 
   OR scraped_date > '2021-04-30'::DATE
