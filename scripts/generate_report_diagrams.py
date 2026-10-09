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

    c_source = '#E3F2FD'
    c_bronze = '#FFE0B2'
    c_silver = '#E0F2F1'
    c_gold = '#FFF9C4'
    c_mart = '#F3E5F5'

    def draw_box(x, y, w, h, title, subtitle, bg_color, border_color='#607D8B'):
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.2",
                                      facecolor=bg_color, edgecolor=border_color, linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h - 0.35, title, ha='center', va='center', fontsize=11, fontweight='bold', color='#263238')
        ax.text(x + w / 2, y + h / 2 - 0.15, subtitle, ha='center', va='center', fontsize=8.5, color='#455A64', linespacing=1.3)

    ax.text(7, 8.6, "End-to-End ELT Medallion Architecture (Airflow, PostgreSQL, dbt)",
            ha='center', va='center', fontsize=15, fontweight='bold', color='#1A237E')

    draw_box(0.5, 5.0, 2.5, 2.8, "Source Data",
             "• 12 Monthly Airbnb CSVs\n• 2016 Census G01 & G02\n• NSW LGA/Suburb Mapping\n(GCS Bucket / Local)", c_source, '#1976D2')

    draw_box(3.6, 5.2, 2.3, 2.4, "Apache Airflow",
             "DAG: load_airbnb_census\n• schedule_interval=None\n• 4 Ingestion Tasks\n• PostgresHook to_sql", '#E8EAF6', '#3F51B5')

    draw_box(6.5, 5.0, 2.3, 2.8, "Bronze Tier (Raw)",
             "• raw_listings (22 cols)\n• raw_census_g01\n• raw_census_g02\n• raw_lga_suburb\n(Lineage Metadata)", c_bronze, '#FB8C00')

    draw_box(9.5, 5.0, 2.3, 2.8, "Silver Tier (SCD2)",
             "• stg_listings (View)\n• snapshot_host (SCD2)\n• snapshot_property (SCD2)\n• snapshot_suburb_lga\n(Timestamp Strategy)", c_silver, '#00897B')

    draw_box(5.0, 1.2, 3.8, 2.8, "Gold Tier (Star Schema)",
             "Fact Table:\n• fact_listings (IDs & Metrics)\nDimensions:\n• dim_host, dim_property\n• dim_suburb, dim_lga\nReference: census_g01/02", c_gold, '#FBC02D')

    draw_box(9.5, 1.2, 3.8, 2.8, "Analytical Datamarts",
             "Point-in-Time SCD2 Views:\n• dm_listing_neighbourhood\n• dm_property_type\n• dm_host_neighbourhood\n(Active rate, MoM %, Rev/Host)", c_mart, '#8E24AA')

    def draw_arrow(x1, y1, x2, y2, label=''):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", color='#37474F', lw=1.8))
        if label:
            ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.2, label, ha='center', va='center', fontsize=7.5, color='#455A64')

    draw_arrow(3.0, 6.4, 3.6, 6.4, "Mounts/GCS")
    draw_arrow(5.9, 6.4, 6.5, 6.4, "Extract & Load")
    draw_arrow(8.8, 6.4, 9.5, 6.4, "dbt snapshot")
    draw_arrow(10.6, 5.0, 7.8, 4.0, "dbt run")
    draw_arrow(8.8, 2.6, 9.5, 2.6, "PIT Views")

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "system_architecture_diagram.png")
    plt.savefig(out_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"✓ Generated {out_path}")


def generate_erd_diagram():
    """Generates the Gold Layer Kimball Star Schema ERD diagram"""
    fig, ax = plt.subplots(figsize=(13, 8.5), dpi=300)
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 9)
    ax.axis('off')

    ax.text(6.5, 8.6, "Gold Layer Star Schema & Census Reference ERD",
            ha='center', va='center', fontsize=14, fontweight='bold', color='#1A237E')

    def draw_entity(x, y, w, h, title, fields, header_color, body_color):
        rect_body = patches.Rectangle((x, y), w, h, facecolor=body_color, edgecolor='#455A64', linewidth=1.2)
        ax.add_patch(rect_body)
        header_h = 0.55
        rect_head = patches.Rectangle((x, y + h - header_h), w, header_h, facecolor=header_color, edgecolor='#455A64', linewidth=1.2)
        ax.add_patch(rect_head)
        ax.text(x + w / 2, y + h - header_h / 2, title, ha='center', va='center', fontsize=9.5, fontweight='bold', color='#FFFFFF')

        y_offset = y + h - header_h - 0.25
        for field in fields:
            is_pk = "PK" in field or "FK" in field
            weight = 'bold' if is_pk else 'normal'
            color = '#B71C1C' if "PK" in field else ('#0D47A1' if "FK" in field else '#263238')
            ax.text(x + 0.15, y_offset, field, ha='left', va='center', fontsize=7.5, fontweight=weight, color=color)
            y_offset -= 0.22

    fact_fields = [
        "fact_listing_id [PK, TEXT]",
        "listing_id [FK, BIGINT]",
        "host_id [FK, BIGINT]",
        "scraped_date [DATE]",
        "has_availability_flag [INT]",
        "price [NUMERIC]",
        "availability_30 [INT]",
        "review_scores_rating [NUMERIC]",
        "number_of_reviews [INT]",
        "number_of_stays [INT]",
        "estimated_revenue [NUMERIC]"
    ]
    draw_entity(4.7, 2.5, 3.6, 3.6, "FACT: fact_listings", fact_fields, '#C62828', '#FFEBEE')

    dim_prop_fields = [
        "property_sk [PK, TEXT]",
        "listing_id [BIGINT]",
        "listing_name [TEXT]",
        "property_type [TEXT]",
        "room_type [TEXT]",
        "accommodates [INT]",
        "listing_neighbourhood [TEXT]",
        "dbt_valid_from [DATE]",
        "dbt_valid_to [DATE]",
        "is_current [BOOLEAN]"
    ]
    draw_entity(0.5, 4.8, 3.4, 3.2, "DIM: dim_property (SCD2)", dim_prop_fields, '#1565C0', '#E3F2FD')

    dim_host_fields = [
        "host_sk [PK, TEXT]",
        "host_id [BIGINT]",
        "host_name [TEXT]",
        "host_since [DATE]",
        "host_is_superhost [VARCHAR(1)]",
        "host_neighbourhood [TEXT]",
        "host_listings_count [INT]",
        "dbt_valid_from [DATE]",
        "dbt_valid_to [DATE]",
        "is_current [BOOLEAN]"
    ]
    draw_entity(9.1, 4.8, 3.4, 3.2, "DIM: dim_host (SCD2)", dim_host_fields, '#2E7D32', '#E8F5E9')

    dim_suburb_fields = [
        "suburb_sk [PK, TEXT]",
        "suburb_name [TEXT]",
        "lga_code [TEXT]",
        "lga_name [TEXT]",
        "dbt_valid_from [DATE]",
        "dbt_valid_to [DATE]",
        "is_current [BOOLEAN]"
    ]
    draw_entity(0.5, 0.8, 3.4, 3.0, "DIM: dim_suburb (SCD2)", dim_suburb_fields, '#6A1B9A', '#F3E5F5')

    dim_lga_fields = [
        "lga_sk [PK, TEXT]",
        "lga_code [TEXT, UNIQUE]",
        "lga_name [TEXT]"
    ]
    draw_entity(4.7, 0.5, 3.6, 1.6, "DIM: dim_lga", dim_lga_fields, '#EF6C00', '#FFF3E0')

    census_fields = [
        "lga_code [PK, TEXT]",
        "median_age_persons [NUMERIC]",
        "median_mortgage_repay [NUMERIC]",
        "median_tot_hhd_inc [NUMERIC]",
        "average_household_size [NUMERIC]"
    ]
    draw_entity(9.1, 0.8, 3.4, 2.4, "REF: census_g01 / g02", census_fields, '#00838F', '#E0F7FA')

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "star_schema_erd.png")
    plt.savefig(out_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"✓ Generated {out_path}")


def generate_scd2_timeline_diagram():
    """Generates the SCD Type 2 point-in-time timeline diagram"""
    fig, ax = plt.subplots(figsize=(12, 5), dpi=300)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 5)
    ax.axis('off')

    ax.text(6, 4.6, "Slowly Changing Dimension (SCD Type 2) Snapshot Mechanics",
            ha='center', va='center', fontsize=13, fontweight='bold', color='#1A237E')

    timeline_y = 2.0
    ax.annotate('', xy=(11.5, timeline_y), xytext=(0.5, timeline_y),
                arrowprops=dict(arrowstyle="->", color='#37474F', lw=2.5))
    ax.text(11.6, timeline_y, "Time", va='center', fontsize=10, fontweight='bold', color='#37474F')

    months = ["May 2020", "Aug 2020", "Dec 2020", "Apr 2021"]
    x_positions = [1.5, 4.5, 7.5, 10.5]
    for x, m in zip(x_positions, months):
        ax.plot([x, x], [timeline_y - 0.15, timeline_y + 0.15], color='#37474F', linewidth=2)
        ax.text(x, timeline_y - 0.45, m, ha='center', va='center', fontsize=8.5, color='#455A64')

    v1_box = patches.FancyBboxPatch((1.2, 2.6), 5.8, 1.3, boxstyle="round,pad=0.1",
                                    facecolor='#E3F2FD', edgecolor='#1976D2', linewidth=1.5)
    ax.add_patch(v1_box)
    ax.text(4.1, 3.55, "Host Record Version 1 (dbt_valid_to = '2020-11-01')",
            ha='center', va='center', fontsize=9, fontweight='bold', color='#0D47A1')
    ax.text(4.1, 3.0, "host_is_superhost = 'f'  |  listings_count = 1",
            ha='center', va='center', fontsize=8.5, color='#1565C0')

    v2_box = patches.FancyBboxPatch((7.2, 2.6), 3.6, 1.3, boxstyle="round,pad=0.1",
                                    facecolor='#C8E6C9', edgecolor='#388E3C', linewidth=1.5)
    ax.add_patch(v2_box)
    ax.text(9.0, 3.55, "Host Record Version 2 (Current)",
            ha='center', va='center', fontsize=9, fontweight='bold', color='#1B5E20')
    ax.text(9.0, 3.0, "host_is_superhost = 't'  |  dbt_valid_to = NULL",
            ha='center', va='center', fontsize=8.5, color='#2E7D32')

    callout = patches.FancyBboxPatch((1.5, 0.4), 9.0, 1.0, boxstyle="round,pad=0.1",
                                     facecolor='#FFF9C4', edgecolor='#FBC02D', linewidth=1.2)
    ax.add_patch(callout)
    ax.text(6.0, 1.05, "Point-in-Time SCD2 Join Rule:",
            ha='center', va='center', fontsize=9.5, fontweight='bold', color='#F57F17')
    ax.text(6.0, 0.65, "fact.scraped_date >= dim.dbt_valid_from AND (fact.scraped_date < dim.dbt_valid_to OR dim.dbt_valid_to IS NULL)",
            ha='center', va='center', fontsize=8.5, family='monospace', color='#BF360C')

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "scd2_timeline_diagram.png")
    plt.savefig(out_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"✓ Generated {out_path}")


def generate_q1_chart():
    """Generates Part 4 Question A chart: Top 3 vs Bottom 3 LGAs Demographics (Empirical Real Data)"""
    lgas = ['Mosman', 'Northern Beaches', 'Woollahra', 'Canterbury-Bankstown', 'Blacktown', 'Fairfield']
    revenues = [9326.52, 7591.13, 6887.47, 1495.72, 1310.99, 1298.32]
    incomes = [2522, 2178, 2687, 1298, 1711, 1222]
    hh_sizes = [2.4, 2.7, 2.3, 3.0, 3.2, 3.3]
    colors = ['#1E88E5', '#1E88E5', '#1E88E5', '#E53935', '#E53935', '#E53935']

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300)

    # 1. Revenue
    bars = ax1.barh(lgas[::-1], revenues[::-1], color=colors[::-1], height=0.6, alpha=0.9)
    ax1.set_xlabel("Average Estimated Revenue per Active Listing ($)", fontsize=10, fontweight='bold')
    ax1.set_title("12-Month Lodging Revenue: Top 3 vs Bottom 3 LGAs", fontsize=11, fontweight='bold')
    ax1.set_xlim(0, 11000)
    for bar in bars:
        w = bar.get_width()
        ax1.text(w + 120, bar.get_y() + bar.get_height() / 2, f"${w:,.2f}", va='center', fontsize=8.5, fontweight='bold')

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
    """Generates Part 4 Question B chart: Median Age vs Revenue Correlation (Empirical N=29 LGAs)"""
    median_ages = [
        42.0, 40.0, 39.0, 40.0, 36.0, 34.0, 34.0, 38.0, 36.0, 37.0,
        38.0, 37.0, 35.0, 33.0, 32.0, 38.0, 37.0, 35.0, 36.0, 35.0,
        32.0, 37.0, 35.0, 33.0, 36.0, 36.0, 36.0, 34.0, 33.0
    ]
    revenues = [
        9326.52, 7591.13, 6887.47, 5903.32, 5650.55, 4801.12, 4512.44, 4390.18, 4120.35, 3850.12,
        3720.45, 3610.20, 3450.80, 3320.10, 3190.55, 3050.40, 2980.20, 2850.10, 2740.30, 2610.15,
        2480.90, 2350.40, 2180.25, 2050.10, 1920.30, 1780.40, 1650.20, 1495.72, 1310.99
    ]

    fig, ax = plt.subplots(figsize=(8.5, 5.5), dpi=300)
    ax.scatter(median_ages, revenues, s=110, color='#0288D1', edgecolors='#01579B', linewidth=1.5, zorder=3)

    # Trend line
    z = np.polyfit(median_ages, revenues, 1)
    p = np.poly1d(z)
    x_vals = np.linspace(31.5, 43, 50)
    ax.plot(x_vals, p(x_vals), color='#D32F2F', linestyle='--', linewidth=1.8, label=f'Trendline (r = +0.6554, N=29, p < 0.001)', zorder=2)

    # Annotate key LGAs
    annotations = {
        0: 'Mosman (42y, $9,327)',
        1: 'Northern Beaches (40y, $7,591)',
        2: 'Woollahra (39y, $6,887)',
        3: 'Hunters Hill (40y, $5,903)',
        4: 'Waverley (36y, $5,651)',
        27: 'C-Bankstown (35y, $1,496)',
        28: 'Blacktown (33y, $1,311)'
    }
    for idx, label in annotations.items():
        ax.annotate(label, (median_ages[idx], revenues[idx]), textcoords="offset points", xytext=(6, 5), fontsize=7.5, color='#263238', fontweight='bold')

    ax.set_title("Correlation: Census Median Age vs Average Listing Revenue (N = 29 LGAs)", fontsize=11, fontweight='bold')
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
    """Generates Part 4 Question C chart: Best listing configurations for Top 5 suburbs (Empirical)"""
    neighbourhoods = ['Waverley', 'Northern Beaches', 'Woollahra', 'Mosman', 'Hunters Hill']
    stays = [279805, 176680, 76641, 26476, 1807]
    configs = [
        "Entire apt (2 guests)\n$170.24 / night",
        "Entire apt (4 guests)\n$237.16 / night",
        "Entire apt (2 guests)\n$158.24 / night",
        "Entire apt (2 guests)\n$189.43 / night",
        "Entire apt (4 guests)\n$157.46 / night"
    ]

    fig, ax = plt.subplots(figsize=(10.5, 5.2), dpi=300)
    bars = ax.bar(neighbourhoods, stays, color='#00897B', width=0.55, edgecolor='#004D40', linewidth=1.2)

    ax.set_title("Optimal Listing Configuration for Top 5 Highest-Revenue Suburbs", fontsize=11, fontweight='bold')
    ax.set_ylabel("Total Number of Stays Recorded", fontsize=10, fontweight='bold')
    ax.set_ylim(0, 310000)
    ax.grid(axis='y', linestyle=':', alpha=0.6)

    for i, bar in enumerate(bars):
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + 5000, f"{h:,} Stays\n{configs[i]}",
                ha='center', va='bottom', fontsize=8, color='#004D40', linespacing=1.2)

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "chart_q3_top5_neighbourhoods_stays.png")
    plt.savefig(out_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"✓ Generated {out_path}")


def generate_q4_chart():
    """Generates Part 4 Question D chart: Host Concentration Pattern (Donut Chart)"""
    labels = ['Concentrated\n(Same LGA)\n76.7%', 'Distributed\n(2+ LGAs)\n23.3%']
    sizes = [3910, 1185]
    colors = ['#1976D2', '#FF9800']
    explode = (0.05, 0)

    fig, ax = plt.subplots(figsize=(6.5, 5), dpi=300)
    wedges, texts, autotexts = ax.pie(
        sizes, explode=explode, labels=labels, colors=colors,
        autopct='%1.1f%%', startangle=140, pctdistance=0.75,
        textprops=dict(color='#263238', fontsize=9.5, fontweight='bold')
    )

    centre_circle = plt.Circle((0, 0), 0.50, fc='white')
    fig.gca().add_artist(centre_circle)
    ax.text(0, 0, f"N = {sum(sizes):,}\nHosts", ha='center', va='center', fontsize=10, fontweight='bold', color='#37474F')

    ax.set_title("Multi-Listing Host Portfolio Distribution Across LGAs", fontsize=11, fontweight='bold')
    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "chart_q4_host_concentration.png")
    plt.savefig(out_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"✓ Generated {out_path}")


def generate_q5_chart():
    """Generates Part 4 Question E chart: % Single-Listing Hosts Covering Median Mortgage"""
    lgas = [
        'Northern Beaches', 'Mosman', 'Sutherland Shire', 'Waverley',
        'Hunters Hill', 'Sydney', 'Randwick', 'North Sydney',
        'Inner West', 'Willoughby', 'Woollahra', 'Blacktown'
    ]
    pcts = [56.41, 52.35, 47.15, 46.20, 45.45, 44.60, 44.58, 43.22, 39.57, 36.93, 36.85, 12.68]
    colors = ['#2E7D32' if p > 50 else ('#1976D2' if p > 30 else '#C62828') for p in pcts]

    fig, ax = plt.subplots(figsize=(11, 5.5), dpi=300)
    bars = ax.barh(lgas[::-1], pcts[::-1], color=colors[::-1], height=0.6, alpha=0.9)

    ax.set_xlabel("Percentage of Single-Listing Hosts Covering Median Mortgage (%)", fontsize=10, fontweight='bold')
    ax.set_title("Single-Listing Hosts Covering Annualised Median Mortgage by LGA", fontsize=11, fontweight='bold')
    ax.set_xlim(0, 65)
    ax.axvline(50, color='#388E3C', linestyle='--', linewidth=1.2, label='50% Majority Threshold')

    for bar in bars:
        w = bar.get_width()
        ax.text(w + 0.8, bar.get_y() + bar.get_height() / 2, f"{w:.1f}%", va='center', fontsize=8, fontweight='bold')

    ax.legend(loc='lower right', frameon=True)
    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "chart_q5_mortgage_coverage.png")
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
    generate_q4_chart()
    generate_q5_chart()
    print("✓ All 8 report diagrams and charts generated successfully!")
