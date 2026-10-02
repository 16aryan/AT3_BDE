#!/usr/bin/env python3
"""
UTS 36120: Big Data Engineering - Assignment 3
Diagram & Visualization Generator for Report
Generates publication-quality diagrams and analytical charts in reports/images/
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "reports", "images"))
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Set global style
plt.rcParams['font.sans-serif'] = 'Helvetica, Arial, sans-serif'
plt.rcParams['axes.edgecolor'] = '#CCCCCC'
plt.rcParams['axes.linewidth'] = 0.8


def generate_architecture_diagram():
    """Generates the end-to-end Medallion Architecture diagram"""
    fig, ax = plt.subplots(figsize=(14, 8), dpi=300)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 9)
    ax.axis('off')

    # Color palette
    c_source = '#E3F2FD'
    c_bronze = '#FFE0B2'
    c_silver = '#E0F2F1'
    c_gold = '#FFF9C4'
    c_mart = '#F3E5F5'
    c_border = '#455A64'

    def draw_box(x, y, w, h, title, subtitle, bg_color, border_color='#607D8B'):
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.2",
                                      facecolor=bg_color, edgecolor=border_color, linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h - 0.35, title, ha='center', va='center', fontsize=11, fontweight='bold', color='#263238')
        ax.text(x + w / 2, y + h / 2 - 0.15, subtitle, ha='center', va='center', fontsize=8.5, color='#455A64', linespacing=1.3)

    # Title
    ax.text(7, 8.6, "End-to-End ELT Medallion Architecture (Airflow & dbt)",
            ha='center', va='center', fontsize=15, fontweight='bold', color='#1A237E')

    # 1. Sources
    draw_box(0.5, 5.0, 2.5, 2.8, "Source Data",
             "• 12 Monthly Airbnb CSVs\n• 2016 Census G01 & G02\n• NSW LGA/Suburb Mapping\n(GCS Bucket / Local)", c_source, '#1976D2')

    # 2. Airflow
    draw_box(3.6, 5.2, 2.3, 2.4, "Apache Airflow",
             "DAG: load_airbnb_census\n• schedule_interval=None\n• Sequential Monthly Loads\n• PostgresHook ingestion", '#E8EAF6', '#3F51B5')

    # 3. Bronze Layer
    draw_box(6.5, 5.0, 2.3, 2.8, "Bronze Layer (Raw)",
             "• raw_listings (74 cols)\n• raw_census_g01\n• raw_census_g02\n• raw_lga_suburb\n(Audit Metadata added)", c_bronze, '#FB8C00')

    # 4. Silver Layer
    draw_box(9.4, 5.0, 2.4, 2.8, "Silver Layer (Cleaned)",
             "• stg_listings (View)\n• snapshot_host (SCD2)\n• snapshot_property (SCD2)\n• snapshot_suburb_lga (SCD2)\n(Timestamp Strategy)", c_silver, '#00897B')

    # 5. Gold Layer
    draw_box(6.0, 1.2, 3.2, 3.0, "Gold Star Schema",
             "Fact Table:\n• fact_listings (IDs & Metrics)\nDimensions:\n• dim_host, dim_property\n• dim_suburb, dim_lga\nReference: census_g01/02", c_gold, '#FBC02D')

    # 6. Datamarts
    draw_box(9.8, 1.2, 3.6, 3.0, "Business Datamarts",
             "Point-in-Time SCD2 Views:\n• dm_listing_neighbourhood\n• dm_property_type\n• dm_host_neighbourhood\n(Active rate, MoM %, Rev/Host)", c_mart, '#8E24AA')

    # Connectors (Arrows)
    arrow_props = dict(facecolor='#455A64', edgecolor='#455A64', width=1.5, headwidth=7)
    ax.annotate('', xy=(3.6, 6.4), xytext=(3.0, 6.4), arrowprops=arrow_props)
    ax.annotate('', xy=(6.5, 6.4), xytext=(5.9, 6.4), arrowprops=arrow_props)
    ax.annotate('', xy=(9.4, 6.4), xytext=(8.8, 6.4), arrowprops=arrow_props)
    ax.annotate('', xy=(7.6, 4.2), xytext=(10.6, 5.0), arrowprops=arrow_props)
    ax.annotate('', xy=(9.8, 2.7), xytext=(9.2, 2.7), arrowprops=arrow_props)

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "system_architecture_diagram.png")
    plt.savefig(out_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"✓ Generated {out_path}")


def generate_erd_diagram():
    """Generates the Star Schema ERD diagram for Gold layer"""
    fig, ax = plt.subplots(figsize=(13, 8), dpi=300)
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 8.5)
    ax.axis('off')

    def draw_entity(x, y, w, h, title, fields, header_color='#1E88E5', bg_color='#F5F5F5'):
        # Header
        h_rect = patches.FancyBboxPatch((x, y + h - 0.6), w, 0.6, boxstyle="round,pad=0.1",
                                        facecolor=header_color, edgecolor=header_color)
        ax.add_patch(h_rect)
        ax.text(x + w / 2, y + h - 0.3, title, ha='center', va='center', fontsize=9.5, fontweight='bold', color='white')

        # Body
        b_rect = patches.FancyBboxPatch((x, y), w, h - 0.6, boxstyle="round,pad=0.1",
                                        facecolor=bg_color, edgecolor='#BDBDBD', linewidth=1)
        ax.add_patch(b_rect)
        y_text = y + h - 0.9
        for field in fields:
            ax.text(x + 0.15, y_text, field, ha='left', va='center', fontsize=7.8, color='#212121')
            y_text -= 0.32

    # Title
    ax.text(6.5, 8.1, "Gold Layer Dimensional Star Schema & Reference ERD",
            ha='center', va='center', fontsize=14, fontweight='bold', color='#263238')

    # Fact Table (Center)
    fact_fields = [
        "PK  fact_listing_id (MD5)",
        "FK  listing_id (INT)",
        "FK  host_id (INT)",
        "    scraped_date (DATE)",
        "    month_year (VARCHAR)",
        "    has_availability (CHAR)",
        "    price (NUMERIC)",
        "    availability_30 (INT)",
        "    number_of_stays (INT)",
        "    estimated_revenue (NUMERIC)",
        "    review_scores_rating (NUMERIC)"
    ]
    draw_entity(4.8, 2.0, 3.4, 4.4, "FACT: fact_listings", fact_fields, '#C62828', '#FFEBEE')

    # Dimensions
    dim_host_fields = [
        "PK  host_sk (MD5)",
        "    host_id (INT)",
        "    host_name (VARCHAR)",
        "    host_is_superhost (CHAR)",
        "    host_neighbourhood (TEXT)",
        "    dbt_valid_from (DATETIME)",
        "    dbt_valid_to (DATETIME)"
    ]
    draw_entity(0.5, 4.6, 3.2, 3.1, "DIM: dim_host (SCD2)", dim_host_fields, '#1565C0', '#E3F2FD')

    dim_property_fields = [
        "PK  property_sk (MD5)",
        "    listing_id (INT)",
        "    property_type (TEXT)",
        "    room_type (TEXT)",
        "    accommodates (INT)",
        "    listing_neighbourhood (TEXT)",
        "    dbt_valid_from (DATETIME)",
        "    dbt_valid_to (DATETIME)"
    ]
    draw_entity(9.3, 4.6, 3.2, 3.3, "DIM: dim_property (SCD2)", dim_property_fields, '#2E7D32', '#E8F5E9')

    dim_suburb_fields = [
        "PK  suburb_sk (MD5)",
        "    suburb_name (TEXT)",
        "FK  lga_code (VARCHAR)",
        "    lga_name (TEXT)",
        "    dbt_valid_from (DATETIME)",
        "    dbt_valid_to (DATETIME)"
    ]
    draw_entity(0.5, 0.8, 3.2, 3.0, "DIM: dim_suburb (SCD2)", dim_suburb_fields, '#6A1B9A', '#F3E5F5')

    dim_lga_fields = [
        "PK  lga_sk (MD5)",
        "    lga_code (VARCHAR)",
        "    lga_name (TEXT)"
    ]
    draw_entity(9.3, 0.8, 3.2, 1.8, "DIM: dim_lga", dim_lga_fields, '#EF6C00', '#FFF3E0')

    # Connectors
    ax.annotate('', xy=(4.8, 4.6), xytext=(3.7, 5.5),
                arrowprops=dict(facecolor='#546E7A', edgecolor='#546E7A', width=1.2, headwidth=6))
    ax.annotate('', xy=(8.2, 4.6), xytext=(9.3, 5.5),
                arrowprops=dict(facecolor='#546E7A', edgecolor='#546E7A', width=1.2, headwidth=6))
    ax.annotate('', xy=(4.8, 3.0), xytext=(3.7, 2.2),
                arrowprops=dict(facecolor='#546E7A', edgecolor='#546E7A', width=1.2, headwidth=6))

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "star_schema_erd.png")
    plt.savefig(out_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"✓ Generated {out_path}")


def generate_scd2_timeline_diagram():
    """Generates visual explanation of SCD Type 2 point-in-time matching"""
    fig, ax = plt.subplots(figsize=(12, 5), dpi=300)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 5)
    ax.axis('off')

    # Title
    ax.text(6, 4.6, "Slowly Changing Dimensions Type 2 (SCD2) Point-in-Time Joins",
            ha='center', va='center', fontsize=13, fontweight='bold', color='#263238')

    # Timeline Bar
    timeline_y = 2.4
    ax.plot([1, 11], [timeline_y, timeline_y], color='#90A4AE', linewidth=3, zorder=1)

    # Months marks
    months = ["May 2020", "Aug 2020", "Dec 2020", "Apr 2021"]
    x_positions = [1.5, 4.5, 7.5, 10.5]
    for x, m in zip(x_positions, months):
        ax.plot([x, x], [timeline_y - 0.15, timeline_y + 0.15], color='#37474F', linewidth=2)
        ax.text(x, timeline_y - 0.45, m, ha='center', va='center', fontsize=8.5, color='#455A64')

    # Version 1 Box
    v1_box = patches.FancyBboxPatch((1.2, 2.8), 5.8, 1.2, boxstyle="round,pad=0.1",
                                    facecolor='#E3F2FD', edgecolor='#1976D2', linewidth=1.5)
    ax.add_patch(v1_box)
    ax.text(4.1, 3.65, "Host Record Version 1 (dbt_valid_to = '2020-11-15')",
            ha='center', va='center', fontsize=9, fontweight='bold', color='#0D47A1')
    ax.text(4.1, 3.2, "host_is_superhost = 'f'  |  listings_count = 1",
            ha='center', va='center', fontsize=8.5, color='#1565C0')

    # Version 2 Box
    v2_box = patches.FancyBboxPatch((7.2, 2.8), 3.6, 1.2, boxstyle="round,pad=0.1",
                                    facecolor='#C8E6C9', edgecolor='#388E3C', linewidth=1.5)
    ax.add_patch(v2_box)
    ax.text(9.0, 3.65, "Host Record Version 2 (Current)",
            ha='center', va='center', fontsize=9, fontweight='bold', color='#1B5E20')
    ax.text(9.0, 3.2, "host_is_superhost = 't'  |  dbt_valid_to = NULL",
            ha='center', va='center', fontsize=8.5, color='#2E7D32')

    # Fact matching explanation
    callout = patches.FancyBboxPatch((1.5, 0.4), 9.0, 1.1, boxstyle="round,pad=0.1",
                                     facecolor='#FFF9C4', edgecolor='#FBC02D', linewidth=1.2)
    ax.add_patch(callout)
    ax.text(6.0, 1.15, "Point-in-Time SCD2 Join Rule:",
            ha='center', va='center', fontsize=9.5, fontweight='bold', color='#F57F17')
    ax.text(6.0, 0.75, "fact.scraped_date >= dim.dbt_valid_from AND (fact.scraped_date < dim.dbt_valid_to OR dim.dbt_valid_to IS NULL)",
            ha='center', va='center', fontsize=8.5, family='monospace', color='#BF360C')

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "scd2_timeline_diagram.png")
    plt.savefig(out_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"✓ Generated {out_path}")


def generate_q1_chart():
    """Generates Part 4 Question A chart: Top 3 vs Bottom 3 LGAs Demographics"""
    lgas = ['Waverley', 'Northern Beaches', 'Woollahra', 'Canterbury-Bankstown', 'Randwick', 'Blacktown']
    revenues = [5075.44, 4764.69, 4152.68, 3416.08, 3362.43, 3260.99]
    incomes = [2200, 2150, 2450, 1300, 1850, 1550]
    hh_sizes = [2.2, 2.7, 2.3, 3.1, 2.4, 3.2]
    colors = ['#1E88E5', '#1E88E5', '#1E88E5', '#E53935', '#E53935', '#E53935']

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300)

    # 1. Revenue
    bars = ax1.barh(lgas[::-1], revenues[::-1], color=colors[::-1], height=0.6, alpha=0.9)
    ax1.set_xlabel("Average Estimated Revenue per Active Listing ($)", fontsize=10, fontweight='bold')
    ax1.set_title("12-Month Lodging Revenue: Top 3 vs Bottom 3 LGAs", fontsize=11, fontweight='bold')
    ax1.set_xlim(0, 6000)
    for bar in bars:
        w = bar.get_width()
        ax1.text(w + 80, bar.get_y() + bar.get_height() / 2, f"${w:,.2f}", va='center', fontsize=8.5, fontweight='bold')

    # 2. Socioeconomic indicators
    x = np.arange(len(lgas))
    w = 0.35
    ax2.bar(x - w / 2, incomes, w, label='Median Weekly HH Income ($)', color='#3949AB', alpha=0.85)
    ax2.set_ylabel("Income ($)", fontsize=10, color='#3949AB')
    ax2.set_xticks(x)
    ax2.set_xticklabels(lgas, rotation=35, ha='right', fontsize=8.5)
    ax2.set_title("Census Socioeconomic Profile by LGA", fontsize=11, fontweight='bold')

    ax2_twin = ax2.twinx()
    ax2_twin.plot(x, hh_sizes, color='#D81B60', marker='o', linewidth=2.2, label='Avg Household Size (Persons)')
    ax2_twin.set_ylabel("Avg Household Size (Persons)", fontsize=10, color='#D81B60')
    ax2_twin.set_ylim(1.5, 4.0)

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "chart_q1_top_bottom_lgas.png")
    plt.savefig(out_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"✓ Generated {out_path}")


def generate_q2_chart():
    """Generates Part 4 Question B chart: Median Age vs Revenue Correlation"""
    median_ages = [32, 35, 39, 39, 34, 36, 34, 35, 33]
    revenues = [4250.2, 5075.4, 4152.7, 4764.7, 3362.4, 3950.1, 3520.4, 3416.1, 3261.0]
    lga_names = ['Sydney', 'Waverley', 'Woollahra', 'N. Beaches', 'Randwick', 'Inner West', 'Parramatta', 'C-Bankstown', 'Blacktown']

    fig, ax = plt.subplots(figsize=(8, 5.5), dpi=300)
    ax.scatter(median_ages, revenues, s=120, color='#0288D1', edgecolors='#01579B', linewidth=1.5, zorder=3)

    # Trend line
    z = np.polyfit(median_ages, revenues, 1)
    p = np.poly1d(z)
    x_vals = np.linspace(31.5, 40, 50)
    ax.plot(x_vals, p(x_vals), color='#D32F2F', linestyle='--', linewidth=1.8, label=f'Trendline (r = +0.4450)', zorder=2)

    for i, name in enumerate(lga_names):
        ax.annotate(name, (median_ages[i], revenues[i]), textcoords="offset points", xytext=(6, 6), fontsize=8, color='#37474F')

    ax.set_title("Correlation: Census Median Age vs Average Listing Revenue", fontsize=11, fontweight='bold')
    ax.set_xlabel("Census Median Age of Residents (Years)", fontsize=10, fontweight='bold')
    ax.set_ylabel("Average Revenue per Active Listing ($)", fontsize=10, fontweight='bold')
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper left', frameon=True)

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "chart_q2_median_age_vs_revenue.png")
    plt.savefig(out_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"✓ Generated {out_path}")


def generate_q3_chart():
    """Generates Part 4 Question C chart: Best listing configurations for Top 5 suburbs"""
    neighbourhoods = ['Bondi', 'Manly', 'Bondi Beach', 'Double Bay', 'Sydney (CBD)']
    stays = [200, 547, 415, 444, 479]
    configs = [
        "Entire house (2 guests)",
        "Entire house (4 guests)",
        "Entire house (1 guest)",
        "Entire townhouse (4 guests)",
        "Private room in apt (4 guests)"
    ]

    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
    bars = ax.bar(neighbourhoods, stays, color='#00897B', width=0.55, edgecolor='#004D40', linewidth=1.2)

    ax.set_title("Optimal Listing Configuration for Top 5 Revenue Suburbs", fontsize=11, fontweight='bold')
    ax.set_ylabel("Total Number of Stays Recorded", fontsize=10, fontweight='bold')
    ax.set_ylim(0, 650)
    ax.grid(axis='y', linestyle=':', alpha=0.6)

    for i, bar in enumerate(bars):
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + 15, f"{h} Stays\n{configs[i]}",
                ha='center', va='bottom', fontsize=8, color='#004D40', linespacing=1.2)

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "chart_q3_top5_neighbourhoods_stays.png")
    plt.savefig(out_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"✓ Generated {out_path}")


if __name__ == "__main__":
    print("Generating report figures and diagrams in reports/images/...")
    generate_architecture_diagram()
    generate_erd_diagram()
    generate_scd2_timeline_diagram()
    generate_q1_chart()
    generate_q2_chart()
    generate_q3_chart()
    print("✓ All 6 report diagrams generated successfully!")
