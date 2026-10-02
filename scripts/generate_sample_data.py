#!/usr/bin/env python3
"""
UTS 36120: Big Data Engineering - Assignment 3
Dataset Generator: Creates realistic Sydney Airbnb and ABS Census datasets
for local testing, pipeline validation, and assignment execution.
"""

import os
import random
import csv
from datetime import datetime, date

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
os.makedirs(DATA_DIR, exist_ok=True)

# 1. Sydney LGA and Suburb mapping
SUBURB_LGA_DATA = [
    # Sydney City
    ("Sydney", "LGA17200", "City of Sydney"),
    ("Surry Hills", "LGA17200", "City of Sydney"),
    ("Darlinghurst", "LGA17200", "City of Sydney"),
    ("Newtown", "LGA17200", "City of Sydney"),
    ("Pyrmont", "LGA17200", "City of Sydney"),
    ("Ultimo", "LGA17200", "City of Sydney"),
    # Waverley
    ("Bondi", "LGA17900", "Waverley"),
    ("Bondi Beach", "LGA17900", "Waverley"),
    ("Bronte", "LGA17900", "Waverley"),
    # Woollahra
    ("Paddington", "LGA18500", "Woollahra"),
    ("Double Bay", "LGA18500", "Woollahra"),
    ("Rose Bay", "LGA18500", "Woollahra"),
    # Northern Beaches
    ("Manly", "LGA15990", "Northern Beaches"),
    ("Dee Why", "LGA15990", "Northern Beaches"),
    ("Avalon Beach", "LGA15990", "Northern Beaches"),
    # Randwick
    ("Coogee", "LGA16550", "Randwick"),
    ("Maroubra", "LGA16550", "Randwick"),
    ("Randwick", "LGA16550", "Randwick"),
    # Inner West
    ("Balmain", "LGA14170", "Inner West"),
    ("Marrickville", "LGA14170", "Inner West"),
    ("Leichhardt", "LGA14170", "Inner West"),
    # Parramatta
    ("Parramatta", "LGA16260", "City of Parramatta"),
    ("Westmead", "LGA16260", "City of Parramatta"),
    # Canterbury-Bankstown
    ("Bankstown", "LGA11570", "Canterbury-Bankstown"),
    ("Campsie", "LGA11570", "Canterbury-Bankstown"),
    # Blacktown
    ("Blacktown", "LGA10750", "Blacktown"),
    ("Mount Druitt", "LGA10750", "Blacktown"),
]

# 2. Census G01 (Person characteristics)
CENSUS_G01 = [
    # LGA_CODE, Tot_P_M, Tot_P_F, Tot_P_P, 0-4, 5-14, 15-19, 20-24, 25-34, 35-44, 45-54, 55-64, 65-74, 75-84, 85ov
    ("LGA17200", 112000, 108000, 220000, 8000, 9000, 10000, 32000, 75000, 36000, 22000, 14000, 9000, 3500, 1500),
    ("LGA17900", 35000, 36000, 71000, 4200, 5800, 3000, 5200, 21000, 13000, 8500, 5300, 3100, 1400, 500),
    ("LGA18500", 27000, 31000, 58000, 3100, 4900, 2800, 3900, 12500, 9800, 8200, 6100, 4100, 1800, 800),
    ("LGA15990", 129000, 134000, 263000, 16000, 33000, 15000, 14000, 38000, 42000, 41000, 32000, 19000, 8500, 4500),
    ("LGA16550", 72000, 75000, 147000, 8200, 13500, 8000, 16500, 35000, 23000, 18000, 12500, 7500, 3300, 1500),
    ("LGA14170", 94000, 98000, 192000, 12000, 18500, 9000, 14000, 48000, 36000, 26000, 15500, 8500, 3300, 1200),
    ("LGA16260", 128000, 127000, 255000, 18000, 28000, 14000, 24000, 62000, 41000, 30000, 20000, 11000, 5000, 2000),
    ("LGA11570", 175000, 178000, 353000, 27000, 46000, 23000, 27000, 59000, 49000, 45000, 37000, 23000, 12000, 5000),
    ("LGA10750", 172000, 175000, 347000, 28000, 51000, 24000, 26000, 61000, 51000, 44000, 34000, 18000, 8000, 3000),
]

# 3. Census G02 (Medians and Averages)
CENSUS_G02 = [
    # LGA_CODE, Median_age_persons, Median_mortgage_repay_monthly, Median_tot_prsnl_inc_weekly, Median_rent_weekly, Median_tot_fam_inc_weekly, Average_num_psns_per_bedroom, Median_tot_hhd_inc_weekly, Average_household_size
    ("LGA17200", 32, 2400, 1150, 580, 2450, 1.2, 1950, 2.0),
    ("LGA17900", 35, 2600, 1280, 650, 2850, 1.2, 2200, 2.2),
    ("LGA18500", 39, 3000, 1450, 720, 3200, 1.1, 2450, 2.3),
    ("LGA15990", 39, 2800, 1050, 600, 2600, 1.1, 2150, 2.7),
    ("LGA16550", 34, 2500, 950, 550, 2300, 1.2, 1850, 2.4),
    ("LGA14170", 36, 2600, 1100, 540, 2550, 1.2, 2050, 2.3),
    ("LGA16260", 34, 2167, 720, 430, 1850, 1.3, 1600, 2.7),
    ("LGA11570", 35, 2000, 530, 380, 1420, 1.4, 1300, 3.1),
    ("LGA10750", 33, 2167, 680, 390, 1680, 1.4, 1550, 3.2),
]


def write_reference_data():
    # 1. NSW LGA Suburb Mapping
    mapping_file = os.path.join(DATA_DIR, "NSW_LGA_Suburb_Mapping.csv")
    with open(mapping_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["suburb_name", "lga_code", "lga_name"])
        for sub, code, name in SUBURB_LGA_DATA:
            writer.writerow([sub, code, name])
    print(f"Generated {mapping_file}")

    # 2. Census G01
    g01_file = os.path.join(DATA_DIR, "2016Census_G01_NSW_LGA.csv")
    with open(g01_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "lga_code", "tot_p_m", "tot_p_f", "tot_p_p",
            "age_0_4_yr_p", "age_5_14_yr_p", "age_15_19_yr_p", "age_20_24_yr_p",
            "age_25_34_yr_p", "age_35_44_yr_p", "age_45_54_yr_p", "age_55_64_yr_p",
            "age_65_74_yr_p", "age_75_84_yr_p", "age_85ov_p"
        ])
        for r in CENSUS_G01:
            writer.writerow([r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10], r[11], r[12], r[13], r[14]])
    print(f"Generated {g01_file}")

    # 3. Census G02
    g02_file = os.path.join(DATA_DIR, "2016Census_G02_NSW_LGA.csv")
    with open(g02_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "lga_code", "median_age_persons", "median_mortgage_repay_monthly",
            "median_tot_prsnl_inc_weekly", "median_rent_weekly", "median_tot_fam_inc_weekly",
            "average_num_psns_per_bedroom", "median_tot_hhd_inc_weekly", "average_household_size"
        ])
        for r in CENSUS_G02:
            writer.writerow(r)
    print(f"Generated {g02_file}")


def write_airbnb_monthly_datasets():
    random.seed(42)

    # 12 Months: May 2020 to April 2021
    months = [
        ("05_2020.csv", "2020-05-15"),
        ("06_2020.csv", "2020-06-15"),
        ("07_2020.csv", "2020-07-15"),
        ("08_2020.csv", "2020-08-15"),
        ("09_2020.csv", "2020-09-15"),
        ("10_2020.csv", "2020-10-15"),
        ("11_2020.csv", "2020-11-15"),
        ("12_2020.csv", "2020-12-15"),
        ("01_2021.csv", "2021-01-15"),
        ("02_2021.csv", "2021-02-15"),
        ("03_2021.csv", "2021-03-15"),
        ("04_2021.csv", "2021-04-15"),
    ]

    property_types = ["Entire apartment", "Entire house", "Private room in apartment", "Private room in house", "Entire townhouse"]
    room_types = ["Entire home/apt", "Private room", "Shared room"]

    # Generate fixed base of 150 hosts and 400 listings
    hosts = []
    for h_id in range(1001, 1151):
        sub, _, _ = random.choice(SUBURB_LGA_DATA)
        hosts.append({
            "host_id": str(h_id),
            "host_name": f"Host_{h_id}",
            "host_since": "2018-03-10",
            "host_location": "Sydney, New South Wales, Australia",
            "host_neighbourhood": sub,
            "host_is_superhost": "t" if random.random() < 0.25 else "f",
            "host_listings_count": str(random.randint(1, 5))
        })

    listings = []
    for l_id in range(50001, 50401):
        host = random.choice(hosts)
        sub, lga_code, lga_name = random.choice(SUBURB_LGA_DATA)
        prop_type = random.choice(property_types)
        room_type = "Private room" if "Private" in prop_type else "Entire home/apt"
        accommodates = random.choice([1, 2, 2, 4, 4, 6])
        base_price = (
            250 if "Bondi" in sub or "Manly" in sub or "Double Bay" in sub
            else (180 if "Sydney" in sub or "Surry Hills" in sub else 95)
        ) + accommodates * 25 + random.randint(-20, 40)

        listings.append({
            "id": str(l_id),
            "host_id": host["host_id"],
            "neighbourhood_cleansed": sub,
            "property_type": prop_type,
            "room_type": room_type,
            "accommodates": str(accommodates),
            "bathrooms": "1" if accommodates <= 2 else "2",
            "bedrooms": "1" if accommodates <= 2 else "2",
            "beds": str(max(1, accommodates // 2)),
            "base_price": base_price,
            "review_scores_rating": round(random.uniform(85, 100), 1),
            "number_of_reviews": random.randint(5, 120)
        })

    # Output each monthly CSV
    columns = [
        "id", "listing_url", "scrape_id", "last_scraped", "name", "description",
        "neighborhood_overview", "picture_url", "host_id", "host_url", "host_name",
        "host_since", "host_location", "host_about", "host_response_time", "host_response_rate",
        "host_acceptance_rate", "host_is_superhost", "host_thumbnail_url", "host_picture_url",
        "host_neighbourhood", "host_listings_count", "host_total_listings_count",
        "host_verifications", "host_has_profile_pic", "host_identity_verified",
        "neighbourhood", "neighbourhood_cleansed", "neighbourhood_group_cleansed",
        "latitude", "longitude", "property_type", "room_type", "accommodates",
        "bathrooms", "bathrooms_text", "bedrooms", "beds", "amenities", "price",
        "minimum_nights", "maximum_nights", "minimum_minimum_nights", "maximum_minimum_nights",
        "minimum_maximum_nights", "maximum_maximum_nights", "minimum_nights_avg_ntm",
        "maximum_nights_avg_ntm", "calendar_updated", "has_availability", "availability_30",
        "availability_60", "availability_90", "availability_365", "calendar_last_scraped",
        "number_of_reviews", "number_of_reviews_ltm", "number_of_reviews_l30d", "first_review",
        "last_review", "review_scores_rating", "review_scores_accuracy", "review_scores_cleanliness",
        "review_scores_checkin", "review_scores_communication", "review_scores_location",
        "review_scores_value", "license", "instant_bookable", "calculated_host_listings_count",
        "calculated_host_listings_count_entire_homes", "calculated_host_listings_count_private_rooms",
        "calculated_host_listings_count_shared_rooms", "reviews_per_month"
    ]

    host_map = {h["host_id"]: dict(h) for h in hosts}

    for month_idx, (filename, scrape_date) in enumerate(months):
        filepath = os.path.join(DATA_DIR, filename)

        # Allow slight evolution each month (SCD2 demonstration: superhost changes, price adjustments)
        for h in host_map.values():
            if random.random() < 0.05:
                # Toggle superhost status
                h["host_is_superhost"] = "t" if h["host_is_superhost"] == "f" else "f"

        rows = []
        for item in listings:
            # 85% of listings active in any given month
            is_active = random.random() < 0.88
            has_avail = "t" if is_active else "f"
            avail_30 = random.randint(0, 25) if is_active else 30
            # Seasonal pricing fluctuation
            seasonal_factor = 1.25 if "12_2020" in filename or "01_2021" in filename else 1.0
            price_val = round(item["base_price"] * seasonal_factor + random.randint(-10, 15), 2)
            h_info = host_map[item["host_id"]]

            row = {col: "" for col in columns}
            row["id"] = item["id"]
            row["scrape_id"] = f"2020{month_idx+1:02d}01"
            row["last_scraped"] = scrape_date
            row["name"] = f"Charming stay in {item['neighbourhood_cleansed']}"
            row["host_id"] = item["host_id"]
            row["host_name"] = h_info["host_name"]
            row["host_since"] = h_info["host_since"]
            row["host_location"] = h_info["host_location"]
            row["host_neighbourhood"] = h_info["host_neighbourhood"]
            row["host_is_superhost"] = h_info["host_is_superhost"]
            row["host_listings_count"] = h_info["host_listings_count"]
            row["neighbourhood_cleansed"] = item["neighbourhood_cleansed"]
            row["property_type"] = item["property_type"]
            row["room_type"] = item["room_type"]
            row["accommodates"] = item["accommodates"]
            row["bathrooms"] = item["bathrooms"]
            row["bedrooms"] = item["bedrooms"]
            row["beds"] = item["beds"]
            row["price"] = f"${price_val:.2f}"
            row["has_availability"] = has_avail
            row["availability_30"] = str(avail_30)
            row["number_of_reviews"] = str(item["number_of_reviews"] + month_idx * 2)
            row["review_scores_rating"] = str(item["review_scores_rating"])
            row["instant_bookable"] = "t" if random.random() < 0.5 else "f"
            rows.append(row)

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)

        print(f"Generated {filename} ({len(rows)} listings, date: {scrape_date})")


if __name__ == "__main__":
    print("Generating reference datasets (Census G01, G02, LGA Suburb Mapping)...")
    write_reference_data()
    print("\nGenerating 12 months of Airbnb Sydney listings (05_2020.csv to 04_2021.csv)...")
    write_airbnb_monthly_datasets()
    print("\n✓ All datasets generated successfully in ./data/")
