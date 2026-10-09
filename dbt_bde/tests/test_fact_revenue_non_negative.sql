-- Assert that estimated_revenue and number_of_stays in fact_listings are always non-negative
SELECT
    fact_listing_id,
    listing_id,
    scraped_date,
    number_of_stays,
    estimated_revenue
FROM {{ ref('fact_listings') }}
WHERE number_of_stays < 0 
   OR estimated_revenue < 0
