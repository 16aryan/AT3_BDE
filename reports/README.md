# Assignment 3: Reports & Visualizations

This directory contains publication-quality architectural diagrams, authentic Google Cloud platform captures, and analytical charts generated for the **Big Data Engineering Assignment 3 Handover Report**.

All analytical diagrams and charts were generated in Python at 300 DPI using `scripts/generate_report_diagrams.py`. Production screenshots capture live Google Cloud Platform (Cloud Composer 2 and Cloud SQL PostgreSQL 18.6) and psql CLI execution.

---

### Index of Figures in Handover Report

| Figure | Image Path | Description |
| :--- | :--- | :--- |
| **Figure 1** | `images/system_architecture_diagram.png` | **End-to-End ELT Medallion Architecture**: Complete data lifecycle from raw CSVs (Airbnb & Census) through Airflow orchestration, Bronze landing, Silver cleaning/snapshots, Gold Star Schema, and Datamarts. |
| **Figure 2** | `images/cloud_sql_instance.png` | **Active Google Cloud SQL Instance**: Live GCP Console capture of PostgreSQL 18.6 (`bde-postgres`) running in `australia-southeast1` (Sydney) with Public IP `34.40.217.131`. |
| **Figure 3** | `images/composer_environment_running.png` | **Active Cloud Composer 2 Environment**: GCP Console capture showing `bde-composer` environment in Sydney on GKE Autopilot. |
| **Figure 4** | `images/airflow_dag_run_grid.png` | **Airflow Task Execution & Duration**: Grid view capture of `load_airbnb_census_dag` showing 100% green task runs and runtime duration curves. |
| **Figure 5** | `images/scd2_timeline_diagram.png` | **SCD Type 2 Timeline Architecture**: Illustrates Ralph Kimball state tracking via `dbt_valid_from` / `dbt_valid_to` temporal validity windows and state-start logic. |
| **Figure 6** | `images/star_schema_erd.png` | **Gold Layer Star Schema ERD**: Entity-Relationship diagram showing `fact_listings` (IDs & numeric metrics only) linked to conformed dimensions (`dim_property`, `dim_host`, `dim_suburb`, `dim_lga`). |
| **Figure 7** | `images/cloud_sql_studio.png` | **Cloud SQL Studio Explorer**: Google Cloud database explorer displaying active, populated `bronze`, `silver`, and `gold` schemas. |
| **Figure 8** | `images/screenshot_part3_monthly_runs.png` | **Airflow Monthly Batch Runs**: Grid view history showing 20 consecutive runs across the 12-month sequential ingestion cycle. |
| **Figure 9** | `images/screenshot_part4_sql_results.png` | **Terminal psql Execution Capture**: CLI psql output executing Part 4 analytical queries against PostgreSQL 18.6 with authentic figures. |
| **Figure 10** | `images/chart_q1_top_bottom_lgas.png` | **Part 4 Question A Chart**: Comparison of 12-month lodging revenue alongside Census weekly household income and average household size for Top 3 vs Bottom 3 LGAs. |
| **Figure 11** | `images/chart_q2_median_age_vs_revenue.png` | **Part 4 Question B Chart**: Scatter plot and regression trendline showing positive correlation ($r = +0.6554, t \approx 4.51$) between resident median age and listing revenue. |
| **Figure 12** | `images/chart_q3_top5_neighbourhoods_stays.png` | **Part 4 Question C Chart**: Optimal accommodation configuration (`property_type`, `room_type`, `accommodates`) yielding the highest number of stays in the top 5 revenue suburbs. |
| **Figure 13** | `images/chart_q4_host_concentration.png` | **Part 4 Question D Chart**: Geographic concentration of multi-listing hosts (76.74% single-LGA focused vs 23.26% multi-LGA operators). |
| **Figure 14** | `images/chart_q5_mortgage_coverage.png` | **Part 4 Question E Chart**: Percentage of annual median mortgage covered by single-listing Airbnb revenue across Sydney LGAs. |

---

### How to Regenerate Figures
To regenerate the analytical charts:
```bash
python3 scripts/generate_report_diagrams.py
```
To recompile the Word document report:
```bash
python3 scripts/build_hd_report_docx.py
```
