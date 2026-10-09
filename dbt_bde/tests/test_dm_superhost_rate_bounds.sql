-- Assert that superhost rate in datamarts is strictly between 0 and 100%
SELECT
    listing_neighbourhood,
    month_year,
    superhost_rate
FROM {{ ref('dm_listing_neighbourhood') }}
WHERE superhost_rate < 0 
   OR superhost_rate > 100
