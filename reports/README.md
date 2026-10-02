# Assignment 3: Reports & Visualizations

This directory contains publication-quality architectural diagrams and analytical charts generated for the **Big Data Engineering Assignment 3 Report**.

All diagrams were generated in Python at 300 DPI using `scripts/generate_report_diagrams.py`.

---

### Index of Figures

| Figure | Image Path | Description |
| :--- | :--- | :--- |
| **Figure 1** | `images/system_architecture_diagram.png` | **End-to-End ELT Medallion Architecture**: Complete data lifecycle from raw CSVs (Airbnb & Census) through Airflow orchestration, Bronze landing, Silver cleaning/snapshots, Gold Star Schema, and Datamarts. |
| **Figure 2** | `images/star_schema_erd.png` | **Gold Layer Star Schema & Reference ERD**: Entity-Relationship diagram showing `fact_listings` (IDs & metrics only) linked to `dim_host`, `dim_property`, `dim_suburb`, and `dim_lga`. |
| **Figure 3** | `images/scd2_timeline_diagram.png` | **SCD Type 2 Point-in-Time Join Logic**: Illustrates how dimension attribute changes (e.g. host superhost status) are tracked over time via `dbt_valid_from` / `dbt_valid_to` and matched to listing fact dates. |
| **Figure 4** | `images/chart_q1_top_bottom_lgas.png` | **Part 4 Question A Chart**: Comparison of 12-month lodging revenue alongside Census weekly household income and average household size for Top 3 vs Bottom 3 LGAs. |
| **Figure 5** | `images/chart_q2_median_age_vs_revenue.png` | **Part 4 Question B Chart**: Scatter plot and regression trendline showing positive correlation ($r = +0.4450$) between resident median age and listing revenue. |
| **Figure 6** | `images/chart_q3_top5_neighbourhoods_stays.png` | **Part 4 Question C Chart**: Optimal accommodation configuration (`property_type`, `room_type`, `accommodates`) yielding the highest number of stays in the top 5 revenue suburbs. |

---

### How to Regenerate Figures
To regenerate or modify any figure:
```bash
python3 scripts/generate_report_diagrams.py
```
