-- Assert that active listings rate in datamarts is strictly between 0 and 100%
SELECT
    listing_neighbourhood,
    month_year,
    active_listings_rate
FROM {{ ref('dm_listing_neighbourhood') }}
WHERE active_listings_rate < 0 
   OR active_listings_rate > 100
