"""
UTS 36120 Big Data Engineering - Assignment 3 Handover Report Generator
Calibrates the handover report to provide comprehensive, publication-grade depth
strictly within the 2,500 word limit specified in the brief (~2,400 to 2,460 total words).
Includes authentic empirical numbers from true SCD2 runs and 13 publication-grade figures.
"""

import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=40, bottom=40, left=80, right=80):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def add_callout_box(doc, title, content_lines, border_color="0080FF", bg_color="F4F8FC"):
    p_before = doc.add_paragraph()
    p_before.paragraph_format.space_before = Pt(2)
    p_before.paragraph_format.space_after = Pt(2)
    
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    tbl.columns[0].width = Inches(6.5)
    
    cell = tbl.cell(0, 0)
    set_cell_background(cell, bg_color)
    set_cell_margins(cell, top=40, bottom=40, left=80, right=80)
    
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(f'''
        <w:tcBorders {nsdecls("w")}>
            <w:top w:val="none" w:sz="0" w:space="0" w:color="auto"/>
            <w:left w:val="single" w:sz="20" w:space="0" w:color="{border_color}"/>
            <w:bottom w:val="none" w:sz="0" w:space="0" w:color="auto"/>
            <w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/>
        </w:tcBorders>
    ''')
    tcPr.append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after = Pt(1)
    run_t = p.add_run(title)
    run_t.bold = True
    run_t.font.name = 'Arial'
    run_t.font.size = Pt(8.5)
    run_t.font.color.rgb = RGBColor(0, 80, 160)
    
    for line in content_lines:
        p2 = cell.add_paragraph()
        p2.paragraph_format.space_before = Pt(0.5)
        p2.paragraph_format.space_after = Pt(0.5)
        run_l = p2.add_run(line)
        run_l.font.name = 'Arial'
        run_l.font.size = Pt(8)
        run_l.font.color.rgb = RGBColor(40, 40, 40)
        
    doc.add_paragraph().paragraph_format.space_after = Pt(2)

def add_summary_box(doc, title, summary_lines):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    tbl.columns[0].width = Inches(6.5)
    
    cell = tbl.cell(0, 0)
    set_cell_background(cell, "F9FAFB")
    set_cell_margins(cell, top=40, bottom=40, left=80, right=80)
    
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(f'''
        <w:tcBorders {nsdecls("w")}>
            <w:top w:val="single" w:sz="6" w:space="0" w:color="0080FF"/>
            <w:left w:val="single" w:sz="6" w:space="0" w:color="0080FF"/>
            <w:bottom w:val="single" w:sz="6" w:space="0" w:color="0080FF"/>
            <w:right w:val="single" w:sz="6" w:space="0" w:color="0080FF"/>
        </w:tcBorders>
    ''')
    tcPr.append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after = Pt(1)
    run_t = p.add_run(title)
    run_t.bold = True
    run_t.font.name = 'Arial'
    run_t.font.size = Pt(8.5)
    run_t.font.color.rgb = RGBColor(0, 80, 160)
    
    for line in summary_lines:
        p2 = cell.add_paragraph()
        p2.paragraph_format.space_before = Pt(0.5)
        p2.paragraph_format.space_after = Pt(0.5)
        run_l = p2.add_run(line)
        run_l.font.name = 'Arial'
        run_l.font.size = Pt(8)
        run_l.font.italic = True
        run_l.font.color.rgb = RGBColor(60, 60, 60)
        
    doc.add_paragraph().paragraph_format.space_after = Pt(2)

def add_code_block(doc, code_str):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    tbl.columns[0].width = Inches(6.5)
    
    cell = tbl.cell(0, 0)
    set_cell_background(cell, "2B2B2B")
    set_cell_margins(cell, top=40, bottom=40, left=80, right=80)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after = Pt(1)
    run = p.add_run(code_str)
    run.font.name = 'Consolas'
    run.font.size = Pt(7.5)
    run.font.color.rgb = RGBColor(240, 240, 240)
    
    doc.add_paragraph().paragraph_format.space_after = Pt(2)

def add_figure(doc, img_path, caption_str, width_inches=5.0):
    if os.path.exists(img_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(4)
        p_img.paragraph_format.space_after = Pt(2)
        doc.add_picture(img_path, width=Inches(width_inches))
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_before = Pt(2)
        p_cap.paragraph_format.space_after = Pt(6)
        r_cap = p_cap.add_run(caption_str)
        r_cap.font.name = 'Arial'
        r_cap.font.size = Pt(7.5)
        r_cap.font.italic = True
        r_cap.font.color.rgb = RGBColor(100, 100, 100)

def format_table(tbl, col_widths, headers, data_rows):
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    
    # Header Row
    hdr_row = tbl.rows[0]
    for i, title in enumerate(headers):
        cell = hdr_row.cells[i]
        cell.width = Inches(col_widths[i])
        set_cell_background(cell, "0080FF")
        set_cell_margins(cell, top=30, bottom=30, left=50, right=50)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(0.5)
        p.paragraph_format.space_after = Pt(0.5)
        run = p.add_run(title)
        run.bold = True
        run.font.name = 'Arial'
        run.font.size = Pt(7.5)
        run.font.color.rgb = RGBColor(255, 255, 255)
        
    # Data Rows
    for r_idx, row_data in enumerate(data_rows):
        row = tbl.add_row()
        bg_color = "F4F8FC" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(row_data):
            cell = row.cells[c_idx]
            cell.width = Inches(col_widths[c_idx])
            set_cell_background(cell, bg_color)
            set_cell_margins(cell, top=25, bottom=25, left=50, right=50)
            p = cell.paragraphs[0]
            if c_idx in [0, 1] and len(headers) > 4:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(0.5)
            p.paragraph_format.space_after = Pt(0.5)
            run = p.add_run(str(val))
            run.font.name = 'Arial'
            run.font.size = Pt(7.5)
            run.font.color.rgb = RGBColor(30, 30, 30)

def generate_report():
    doc = docx.Document()
    
    # Set page margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)
        
    # COVER PAGE
    p_pre = doc.add_paragraph()
    p_pre.paragraph_format.space_before = Pt(40)
    
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_after = Pt(6)
    r = p_title.add_run("ENGINEERING HANDOVER REPORT")
    r.font.name = 'Arial'
    r.font.size = Pt(24)
    r.bold = True
    r.font.color.rgb = RGBColor(0, 80, 160)
    
    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_after = Pt(20)
    r = p_sub.add_run("Building ELT Data Pipelines with Apache Airflow & dbt\nInside Airbnb & ABS Census Sydney Data Platform")
    r.font.name = 'Arial'
    r.font.size = Pt(13)
    r.font.color.rgb = RGBColor(80, 80, 80)
    
    p_meta = doc.add_paragraph()
    p_meta.paragraph_format.space_before = Pt(30)
    p_meta.paragraph_format.space_after = Pt(40)
    
    meta_runs = [
        ("Student Name: ", True), ("Aryan Goel\n", False),
        ("Student ID: ", True), ("26040826\n", False),
        ("Subject: ", True), ("94693 / 36120 Big Data Engineering (Spring 2026)\n", False),
        ("Institution: ", True), ("University of Technology Sydney\n", False),
        ("Repository: ", True), ("https://github.com/16aryan/AT3_BDE\n", False),
        ("Environment: ", True), ("Validated locally on Docker (Postgres 15, Airflow 2.8, dbt 1.11); Deployed on GCP (Composer 2, Cloud SQL Postgres 18)\n", False),
        ("Dataset: ", True), ("Course Authentic Inside Airbnb (412,122 rows) & 2016 ABS Census", False)
    ]
    for text, bold in meta_runs:
        r = p_meta.add_run(text)
        r.font.name = 'Arial'
        r.font.size = Pt(9.5)
        r.bold = bold
        r.font.color.rgb = RGBColor(50, 50, 50)
        
    doc.add_page_break()

    # TABLE OF CONTENTS
    p_toc_t = doc.add_paragraph()
    p_toc_t.paragraph_format.space_before = Pt(6)
    p_toc_t.paragraph_format.space_after = Pt(10)
    r = p_toc_t.add_run("Table of Contents")
    r.font.name = 'Arial'
    r.font.size = Pt(15)
    r.bold = True
    r.font.color.rgb = RGBColor(0, 80, 160)

    toc_items = [
        ("1. High-Level Project Overview & Architecture", "3"),
        ("2. Business Problem & Regulatory Context", "4"),
        ("3. PART 1: Data Ingestion & Cloud Orchestration (Tasks 1 to 3)", "5"),
        ("4. PART 2: Data Warehouse Design with dbt (Silver & Gold Layers)", "7"),
        ("5. PART 3: Sequential Incremental Ingestion & Longitudinal Processing", "9"),
        ("6. PART 4: Ad-Hoc Analytical Queries (SQL Analytics & Findings)", "11"),
        ("    Question A: Demographic Differences in Top 3 vs Bottom 3 LGAs", "11"),
        ("    Question B: Pearson Correlation Analysis (Median Age vs Revenue)", "12"),
        ("    Question C: Optimal Property Configuration in Top 5 Neighbourhoods", "13"),
        ("    Question D: Host Portfolio Concentration Across LGAs", "14"),
        ("    Question E: Single-Listing Hosts vs Annualised Median Mortgages", "15"),
        ("7. Issues, Bugs Faced and Engineering Resolutions", "16"),
        ("    Operational Replication Checklist for Peer Engineers", "17"),
    ]

    for item, page_str in toc_items:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(1)
        r_item = p.add_run(item)
        r_item.font.name = 'Arial'
        r_item.font.size = Pt(8.5)
        if not item.startswith("    "):
            r_item.bold = True
        dots_count = max(4, (75 - len(item)) // 2)
        r_dots = p.add_run(" " + "." * dots_count + " ")
        r_dots.font.color.rgb = RGBColor(180, 180, 180)
        r_page = p.add_run(page_str)
        r_page.font.name = 'Arial'
        r_page.font.size = Pt(8.5)
        if not item.startswith("    "):
            r_page.bold = True

    doc.add_page_break()

    # 1. High-Level Project Overview & Architecture
    h1 = doc.add_heading(level=1)
    r = h1.add_run("1. High-Level Project Overview & Architecture")
    r.font.size = Pt(13)
    r.bold = True
    r.font.color.rgb = RGBColor(0, 80, 160)

    doc.add_paragraph(
        "This engineering handover report documents the complete architectural design, workflow orchestration, multi-layered data modeling, "
        "and empirical SQL analytics developed for Inside Airbnb Sydney listings and Australian Bureau of Statistics (ABS) 2016 Census datasets. "
        "The project encompasses a longitudinal evaluation window spanning May 2020 to April 2021, totaling 412,122 listing records across 12 consecutive "
        "monthly snapshots. Authored for peer data engineers and technical assessors, this document establishes a reproducible, production-grade "
        "Medallion ELT pipeline operationalized across local containerized Docker environments and enterprise Google Cloud Platform (GCP) infrastructure."
    )

    doc.add_paragraph(
        "Modern data engineering mandates an Extract-Load-Transform (ELT) pattern over legacy ETL. In our architecture, "
        "raw ingestion lands high-fidelity source data directly into Bronze schemas without type coercion, preventing failures from "
        "upstream schema drift or malformed values. Downstream cleansing, categorical harmonization, and longitudinal Slowly Changing "
        "Dimension (SCD Type 2) tracking are pushed into the warehouse using dbt Core. Decoupling ingestion from transformation "
        "ensures idempotency across batch loads, enforces point-in-time auditability, and optimizes warehouse compute performance."
    )

    p = doc.add_paragraph()
    p.add_run("• Bronze Tier (Raw Landing & Lineage): ").bold = True
    p.add_run(
        "Orchestrated via Apache Airflow (load_airbnb_census_dag.py), raw ingestion extracts 12 monthly Inside Airbnb CSVs, Census G01 and G02 tables, and NSW "
        "LGA-suburb crosswalk files into PostgreSQL bronze schemas. All 22 Inside Airbnb columns land as raw TEXT, capturing source formatting faithfully "
        "while automatically appending ingestion_timestamp and file_source audit watermarks for end-to-end data lineage."
    )

    p = doc.add_paragraph()
    p.add_run("• Silver Tier (Cleansing & SCD Type 2 Snapshots): ").bold = True
    p.add_run(
        "Declarative dbt staging views sanitize text strings, strip currency symbols, resolve missing fields via COALESCE, and normalize property "
        "classifications. Three dbt snapshots implement Ralph Kimball's SCD Type 2 state tracking across properties (49,072 total versions, 3,459 closed, 45,613 active), "
        "hosts (34,610 total versions, 3,609 closed, 31,001 active), and suburb crosswalk mappings (4,520 records) using state-start timestamp strategies."
    )

    p = doc.add_paragraph()
    p.add_run("• Gold Tier (Kimball Star Schema & Datamarts): ").bold = True
    p.add_run(
        "A dimensional star schema centered around a pure numeric metric and key fact table (gold.fact_listings, 412,122 rows) linked to four conformed dimension "
        "tables. Built atop this star schema, three business datamarts utilize point-in-time (PIT) temporal joins to eliminate data leakage and support longitudinal "
        "urban housing, host portfolio, and revenue velocity analytics."
    )

    add_figure(doc, "reports/images/system_architecture_diagram.png", "Figure 1: End-to-End Medallion ELT Architecture on Google Cloud Platform & dbt", width_inches=5.2)

    doc.add_page_break()

    # 2. Business Problem & Regulatory Context
    h2 = doc.add_heading(level=1)
    r = h2.add_run("2. Business Problem & Regulatory Context")
    r.font.size = Pt(13)
    r.bold = True
    r.font.color.rgb = RGBColor(0, 80, 160)

    doc.add_heading("a. Objective", level=2)
    doc.add_paragraph(
        "The overarching mandate of this data platform is delivering an enterprise analytics foundation to investigate the socioeconomic "
        "impact of short-term rental (STR) accommodation across Greater Sydney. By linking dynamic Airbnb listing metrics with static ABS 2016 Census "
        "demographics, the warehouse answers critical questions surrounding housing affordability, tourist recovery dynamics, and host commercialization. "
        "Key engineering objectives include establishing zero-data-loss ingestion, enforcing idempotency across recurring monthly loads, implementing "
        "flawless SCD Type 2 audit trails, maintaining pure numeric fact tables, and guaranteeing point-in-time join integrity."
    )

    doc.add_heading("b. Stakeholders", level=2)
    stakeholders = [
        ("• Municipal Regulators (City of Sydney & NSW Planning): ", 
         "Evaluate short-term rental density, monitor the NSW 180-day unhosted cap, and assess displacement of long-term housing stock across urban and suburban zones."),
        ("• STR Commercial Investors & Professional Hosts: ", 
         "Identify optimal property configurations (property type, room type, capacity), assess tourist demand, and optimize nightly rates across Sydney LGAs."),
        ("• Tourism Analysts (Destination NSW): ", 
         "Track domestic travel recovery patterns across travel restriction periods, monitoring shifts between metropolitan hubs and coastal leisure enclaves."),
        ("• Data Engineering & Operations Teams: ", 
         "Require automated, idempotent orchestration with layer isolation, automated testing assertions, and fully reproducible infrastructure deployments.")
    ]
    for s_title, s_desc in stakeholders:
        p = doc.add_paragraph()
        p.add_run(s_title).bold = True
        p.add_run(s_desc)

    doc.add_heading("c. Business Context & Market Dynamics", level=2)
    doc.add_paragraph(
        "The evaluation timeframe of May 2020 to April 2021 represents an unprecedented period in Australian urban economics, characterized by international "
        "border closures and fluctuating domestic travel restrictions during the COVID-19 pandemic. Consequently, metropolitan Sydney experienced a bifurcated market: "
        "high-density urban centers like the Sydney CBD experienced severe occupancy declines, whereas scenic coastal enclaves (such as the Northern Beaches, Waverley, "
        "and Mosman) benefited from intense domestic 'staycation' demand. These dynamic market conditions underscored the critical necessity of tracking listing "
        "and host status transitions over time through robust Slowly Changing Dimensions."
    )

    doc.add_page_break()

    # 3. PART 1: Data Ingestion & Pipeline Orchestration
    h3 = doc.add_heading(level=1)
    r = h3.add_run("3. PART 1: Data Ingestion & Pipeline Orchestration (Tasks 1 to 3)")
    r.font.size = Pt(13)
    r.bold = True
    r.font.color.rgb = RGBColor(0, 80, 160)

    add_summary_box(
        doc,
        "Part 1 Specification Summary: Data Ingestion & Orchestration",
        ["Implement an ELT pipeline using Apache Airflow to ingest Inside Airbnb monthly data, ABS Census G01/G02 tables, "
         "and LGA-Suburb mappings into PostgreSQL Bronze tables. Ensure atomic replacement for reference tables, append with lineage "
         "for monthly batches, dynamic runtime file execution, and full auditability."]
    )

    doc.add_paragraph(
        "Pipeline Orchestration Architecture: The ingestion workflow is orchestrated via Apache Airflow (dags/load_airbnb_census_dag.py). "
        "The DAG operates with schedule_interval=None, max_active_runs=1, and catchup=False to prevent concurrency conflicts. "
        "Upstream reference tasks execute in parallel before listing ingestion: [task_load_census_g01, task_load_census_g02, task_load_lga_suburb] >> task_load_airbnb, "
        "ensuring dimensional reference tables are fully populated before transactional records are appended.\n\n"
        "Ingestion Strategies & Idempotency: Reference datasets (Census G01, G02, and Suburb crosswalk) utilize idempotent atomic replacement (if_exists='replace'). "
        "Monthly listings use an append-only strategy (if_exists='append') enriched with file_source and ingestion_timestamp lineage watermarks. "
        "Dynamic runtime batching via dag_run.conf['file'] allows engineers to execute any monthly batch on demand.\n\n"
        "Cross-Platform Storage Abstraction: To guarantee portability across local Docker and GCP Cloud Composer, get_file_content() transparently "
        "evaluates Cloud Composer GCS FUSE mounts (/home/airflow/gcs/data/), native GCSHook blob streaming, and container POSIX paths (/opt/airflow/data/), "
        "executing identical code across dev and cloud environments.\n\n"
        "Schema Definition & Raw Landing: Script sql/01_create_bronze_schema.sql (and part_1.sql) provisions bronze, silver, and gold schemas. "
        "In bronze.raw_listings, all 22 Inside Airbnb attributes land as raw TEXT to absorb schema drift and preserve source fidelity until dbt models execute in Silver."
    )

    add_figure(doc, "reports/images/cloud_sql_instance.png", "Figure 2: Active Google Cloud SQL PostgreSQL Instance in Sydney (australia-southeast1)", width_inches=4.8)
    add_figure(doc, "reports/images/composer_environment_running.png", "Figure 3: Active Google Cloud Composer 2 Environment on GKE Autopilot", width_inches=4.8)
    add_figure(doc, "reports/images/airflow_dag_run_grid.png", "Figure 4: Live Airflow DAG Execution Grid (100% Green Success Status across All Tasks)", width_inches=4.8)

    p_tbl_title = doc.add_paragraph()
    r = p_tbl_title.add_run("Table 1: Raw Bronze Ingestion Accounting Across PostgreSQL Database")
    r.bold = True
    r.font.size = Pt(8)

    tbl1 = doc.add_table(rows=1, cols=5)
    format_table(
        tbl1,
        [1.8, 1.4, 1.2, 1.0, 1.0],
        ["Target Bronze Table", "Source File", "Strategy", "Rows", "Status"],
        [
            ["bronze.raw_census_g01", "2016Census_G01_NSW_LGA.csv", "Idempotent Replace", "132", "CONFIRMED"],
            ["bronze.raw_census_g02", "2016Census_G02_NSW_LGA.csv", "Idempotent Replace", "132", "CONFIRMED"],
            ["bronze.raw_lga_suburb", "NSW_LGA_Suburb_Mapping.csv", "Idempotent Replace", "4,470", "CONFIRMED"],
            ["bronze.raw_listings (Initial)", "05_2020.csv", "Append + Metadata", "37,562", "CONFIRMED"],
            ["bronze.raw_listings (12-Mo Full)", "05_2020 to 04_2021 (12 CSVs)", "Monthly Append", "412,122", "CONFIRMED"]
        ]
    )

    add_callout_box(
        doc,
        "Part 1 Direct Output & Verification:",
        [
            "• Autonomous Orchestration: Airflow executed all DAG tasks with 100% green status, streaming directly to PostgreSQL in 1.1 seconds.",
            "• Zero Data Loss: All 22 Inside Airbnb columns captured in raw TEXT to preserve original fidelity for downstream modeling.",
            "• Full Lineage: Every row tagged with file_source and ingestion_timestamp for complete provenance tracking."
        ]
    )

    doc.add_page_break()

    # 4. PART 2: Data Warehouse Design with dbt
    h4 = doc.add_heading(level=1)
    r = h4.add_run("4. PART 2: Data Warehouse Design with dbt (Silver & Gold Layers)")
    r.font.size = Pt(13)
    r.bold = True
    r.font.color.rgb = RGBColor(0, 80, 160)

    add_summary_box(
        doc,
        "Part 2 Specification Summary: Warehouse Modeling, Snapshots & Datamarts",
        ["Cleanse raw Bronze records to standardize types, sanitize currency strings, and harmonize property categories. "
         "Implement SCD Type 2 tracking using dbt snapshots with the timestamp strategy. Build a Gold Star Schema where the "
         "fact table strictly contains foreign keys and numerical metrics, and construct three analytical datamart views with MoM metrics."]
    )

    doc.add_paragraph(
        "Silver Cleansing & Normalization (silver.stg_listings.sql): Authored as a declarative dbt view executing the following cleansing operations:\n"
        "1. Currency Sanitization & Defensive Defaults: Uses REGEXP_REPLACE(price, '[^0-9.]', '', 'g')::NUMERIC to eliminate currency symbols and commas, casting to decimal. Missing prices coalesce via COALESCE(..., 0.0) to preserve staging row volume, while analytical queries filter unlisted zero-values.\n"
        "2. July Date Anomaly Alignment: Canonical month_year is derived directly from file_source, and out-of-month scrape dates in 07_2020.csv (such as anomalous September timestamps) are aligned to the 14th of the file's month ((file_month_year || '-14')::DATE).\n"
        "3. Property Type Harmonization: Pre-August generic categories (e.g. Apartment, House, Hotel, Hostel) are standardized to post-August naming (e.g. Entire apartment, Private room in house, Room in hotel) across 100% of rows via comprehensive CASE mapping.\n"
        "4. End-to-End Deduplication: Enforced via DISTINCT ON (listing_id, scraped_date) ORDER BY listing_id, scraped_date, ingestion_timestamp DESC NULLS LAST, guaranteeing exact single-record cardinality and idempotent batch re-execution."
    )

    doc.add_paragraph(
        "SCD Type 2 Snapshot Mechanics: Slowly Changing Dimensions preserve historical state without destructive overwrites. Under the hood, "
        "dbt's snapshot engine computes an MD5 surrogate hash across tracked attributes, compares incoming records against active rows (dbt_valid_to IS NULL), "
        "closes modified records by setting dbt_valid_to to the new timestamp, and inserts the new version. To prevent premature freezing or false-positive mutations, "
        "snapshots date each key's state from when that state began (state-start strategy), capturing 49,072 property versions and 34,610 host versions with zero active-flag mismatches."
    )

    add_figure(doc, "reports/images/scd2_timeline_diagram.png", "Figure 5: SCD Type 2 Timeline Diagram Demonstrating State-Start Validity Windows", width_inches=5.0)

    p_tbl_title = doc.add_paragraph()
    r = p_tbl_title.add_run("Table 2: Silver Layer SCD Type 2 Snapshot Summary Across 12 Months")
    r.bold = True
    r.font.size = Pt(8)

    tbl2 = doc.add_table(rows=1, cols=5)
    format_table(
        tbl2,
        [1.8, 1.2, 1.2, 1.2, 1.1],
        ["Snapshot Model", "Unique Key", "Strategy", "Tracked Attributes", "Total Rows"],
        [
            ["silver.snapshot_host", "host_id", "timestamp (state-start)", "name, since, location, superhost, neighbourhood", "34,610 (3,609 closed, 31,001 active)"],
            ["silver.snapshot_property", "listing_id", "timestamp (state-start)", "property_type, room_type, accommodates, baths, beds, neighbourhood, active", "49,072 (3,459 closed, 45,613 active)"],
            ["silver.snapshot_suburb_lga", "suburb_name", "timestamp", "suburb_name, lga_code, lga_name", "4,520 (Static crosswalk)"]
        ]
    )

    doc.add_paragraph(
        "Gold Star Schema Design Standards: Following Ralph Kimball's dimensional modeling standards, the fact table contains strictly "
        "foreign keys and numerical metrics—no descriptive text attributes reside in facts:\n"
        "• Fact Table (gold.fact_listings): 412,122 rows. Keys: fact_listing_id, listing_id, host_id, suburb_name, lga_code, scraped_date. "
        "Numeric metrics: price, has_availability_flag (1/0), availability_30, number_of_reviews, review_scores_rating, estimated_revenue, number_of_stays. "
        "Estimated revenue follows the brief formula: estimated_revenue = (30 - availability_30) * price.\n"
        "• Dimension Models: gold.dim_host (34,610 rows), gold.dim_property (49,072 rows), gold.dim_suburb (4,520 rows), gold.dim_lga (128 rows), "
        "census_g01 (132 rows), and census_g02 (132 rows) maintain conformed descriptive context."
    )

    add_figure(doc, "reports/images/star_schema_erd.png", "Figure 6: Gold Tier Star Schema Entity-Relationship Diagram (Pure Numeric Fact & Conformed Dimensions)", width_inches=5.0)

    doc.add_paragraph(
        "Point-in-Time Temporal Joins: To eliminate lookahead bias (data leakage), facts are matched strictly against the dimension record effective at transaction time:"
    )
    add_code_block(doc,
        "ON fact.listing_id = dim_prop.listing_id\n"
        "   AND fact.scraped_date >= dim_prop.dbt_valid_from\n"
        "   AND (fact.scraped_date < dim_prop.dbt_valid_to OR dim_prop.dbt_valid_to IS NULL)"
    )

    doc.add_paragraph(
        "Analytical Datamarts: Three specialized analytical views aggregate multi-dimensional business metrics:\n"
        "1. dm_listing_neighbourhood: Computes monthly metrics per neighbourhood: active listing count, minimum/maximum/median/average nightly price, "
        "distinct host count, superhost rate, total reviews/ratings, total stays, estimated revenue, and MoM active listing rate growth percentage using LAG().\n"
        "2. dm_property_type: Computes active listing rate, pricing distributions, distinct hosts, superhost percentage, total stays, and estimated revenue across property_type, room_type, accommodates, and year_month.\n"
        "3. dm_host_neighbourhood: Tracks host count, total estimated revenue, estimated revenue per host, and MoM revenue change per host across host LGAs."
    )

    add_callout_box(
        doc,
        "Part 2 Architecture & Tooling Compliance:",
        [
            "• Pure Dimensional Fact: fact_listings holds strictly surrogate/natural keys and numeric metrics (412,122 rows).",
            "• True SCD2 History: 3,459 closed property versions and 3,609 closed host versions capture temporal transitions accurately.",
            "• Tooling Implementation: dbt Core CLI was selected to enable containerized, headless automation in local Docker and Apache Airflow, providing direct terminal execution and automated CI/CD testing."
        ]
    )

    doc.add_page_break()

    # 5. PART 3: Sequential Incremental Ingestion
    h5 = doc.add_heading(level=1)
    r = h5.add_run("5. PART 3: Sequential Incremental Ingestion & Longitudinal Processing")
    r.font.size = Pt(13)
    r.bold = True
    r.font.color.rgb = RGBColor(0, 80, 160)

    add_summary_box(
        doc,
        "Part 3 Specification Summary: Sequential Ingestion & Monthly dbt Runs",
        ["Ingest the remaining 11 months sequentially (06_2020.csv to 04_2021.csv). After each monthly load, execute dbt snapshot and dbt run "
         "to build the longitudinal warehouse history, tracking Slowly Changing Dimensions chronologically over time."]
    )

    doc.add_paragraph(
        "Sequential Ingestion Execution: To simulate real-world production ELT operations, all 12 monthly Inside Airbnb files were ingested "
        "in strict chronological sequence (05_2020 through 04_2021). The orchestrator appends each monthly batch into bronze.raw_listings "
        "and triggers dbt snapshot and dbt run sequentially.\n\n"
        "Longitudinal State Tracking: As consecutive months are processed, dbt evaluates each entity against active snapshot records. "
        "When an existing host gains superhost status or a listing modifies its availability or property attributes, dbt snapshot automatically stamps "
        "dbt_valid_to on the prior version and creates a new active version with dbt_valid_from set to the batch date. Point-in-time temporal joins "
        "in downstream Gold models ensure that historical transactions reflect the exact state effective at scrape time."
    )

    add_figure(doc, "reports/images/screenshot_part3_monthly_runs.png", "Figure 7: Airflow Web UI DAG Run Grid History Showing Successful Execution Across Monthly Batch Loads", width_inches=5.2)

    add_callout_box(
        doc,
        "Part 3 Verification Audit:",
        [
            "• Sequential Ingestion: All 12 monthly CSVs processed chronologically without pipeline interruption.",
            "• Deterministic SCD2 Accumulation: Snapshots expanded progressively from month 1 (37,562 rows) to month 12 (49,072 property and 34,610 host versions).",
            "• Fact Integrity: Across all 12 months, 100% of fact records (412,122 rows) match their corresponding SCD2 dimension records with 0 active-flag mismatches."
        ]
    )

    doc.add_page_break()

    # 6. PART 4: Ad-Hoc Analytical Queries
    h6 = doc.add_heading(level=1)
    r = h6.add_run("6. PART 4: Ad-Hoc Analytical Queries (SQL Analytics & Findings)")
    r.font.size = Pt(13)
    r.bold = True
    r.font.color.rgb = RGBColor(0, 80, 160)

    add_figure(doc, "reports/images/screenshot_part4_sql_results.png", "Figure 8: Terminal psql Execution Output of Analytical Queries in part_4.sql (PostgreSQL 18.6)", width_inches=5.2)

    # QUESTION A
    add_summary_box(
        doc,
        "Part 4 — Question A: Demographic Differences (Top 3 vs Lowest 3 LGAs)",
        ["Identify the demographic differences (e.g., age group distribution, household size, income) between the top 3 performing and "
         "lowest 3 performing LGAs based on estimated revenue per active listing over the last 12 months."]
    )

    doc.add_paragraph(
        "Question A evaluated 12-month average estimated revenue per active listing across Sydney LGAs (>50 active listings). "
        "Cohorts were ranked via DENSE_RANK() and linked to ABS Census tables G01 and G02 to examine demographic and economic divides."
    )

    p_tbl_title = doc.add_paragraph()
    r = p_tbl_title.add_run("Table 3: Demographic & Economic Comparison: Top 3 vs Bottom 3 Performing LGAs")
    r.bold = True
    r.font.size = Pt(8)

    tbl_qa = doc.add_table(rows=1, cols=8)
    format_table(
        tbl_qa,
        [0.9, 1.4, 0.9, 0.7, 0.7, 0.8, 0.8, 0.8],
        ["Cohort", "LGA Name", "Avg Revenue", "Household", "Median Age", "Weekly Inc", "% Age 25-54", "% Age 55+"],
        [
            ["Top 3", "Mosman", "$9,326.52", "2.4", "42.0", "$2,522", "41.4%", "31.1%"],
            ["Top 3", "Northern Beaches", "$7,591.13", "2.7", "40.0", "$2,178", "41.6%", "28.0%"],
            ["Top 3", "Woollahra", "$6,887.47", "2.3", "39.0", "$2,687", "44.8%", "29.4%"],
            ["Bottom 3", "Canterbury-Bankstown", "$1,495.72", "3.0", "35.0", "$1,298", "41.5%", "24.6%"],
            ["Bottom 3", "Blacktown", "$1,310.99", "3.2", "33.0", "$1,711", "43.2%", "20.3%"],
            ["Bottom 3", "Fairfield", "$1,298.32", "3.3", "36.0", "$1,222", "39.7%", "26.3%"]
        ]
    )

    add_figure(doc, "reports/images/chart_q1_top_bottom_lgas.png", "Figure 9: Question A: Comparative Performance & Socioeconomic Indicators (Top 3 vs Bottom 3 LGAs)", width_inches=5.0)

    add_callout_box(
        doc,
        "Question A Direct Findings & Demographic Insights:",
        [
            "• Revenue Disparity: Top 3 LGAs (Mosman: $9,327, Northern Beaches: $7,591, Woollahra: $6,887) average $7,935/listing — 5.8x higher than Bottom 3 LGAs (Canterbury-Bankstown: $1,496, Blacktown: $1,311, Fairfield: $1,298 averaging $1,368).",
            "• Household Size Inversion: Top LGAs average smaller households (2.3–2.7) vs outer suburban LGAs (3.0–3.3 persons).",
            "• Income Gap: Median weekly household income in Mosman ($2,522) and Woollahra ($2,687) is over double that of Fairfield ($1,222) and Canterbury-Bankstown ($1,298), while Northern Beaches ($2,178) is approximately 1.7–1.8× higher.",
            "• Mature Demographics: Top LGAs feature significantly older populations (median age 39.0–42.0 vs 33.0–36.0 in Bottom 3)."
        ]
    )

    doc.add_page_break()

    # QUESTION B
    add_summary_box(
        doc,
        "Part 4 — Question B Specification Summary: Correlation Analysis",
        ["Evaluate the correlation between the median age of an LGA and estimated revenue per active listing over the last 12 months. "
         "Calculate Pearson's correlation coefficient r across all Greater Sydney LGAs and provide statistical and business interpretation."]
    )

    doc.add_paragraph(
        "Question B calculates Pearson's correlation coefficient r between LGA median age (census_g02) and 12-month average estimated "
        "revenue per active listing (gold.fact_listings) across all N = 29 Sydney LGAs using: r = Σ((x - x̄)(y - ȳ)) / sqrt(Σ(x - x̄)² * Σ(y - ȳ)²)."
    )

    p_tbl_title = doc.add_paragraph()
    r = p_tbl_title.add_run("Table 4: Pearson Correlation Statistical Summary")
    r.bold = True
    r.font.size = Pt(8)

    tbl_qb = doc.add_table(rows=1, cols=4)
    format_table(
        tbl_qb,
        [1.8, 1.5, 1.5, 1.7],
        ["Metric", "Sample Size (LGAs)", "Mean Value", "Statistical Result"],
        [
            ["Pearson Correlation (r)", "29 LGAs", "N/A", "+0.6554 (Strong Positive Correlation)"],
            ["t-statistic / Significance", "29 LGAs", "t ≈ 4.51", "p < 0.001 (Statistically Significant)"],
            ["Average Revenue per Listing", "29 LGAs", "$3,480.13", "Range: $1,298.32 - $9,326.52"],
            ["Median Age of Population", "29 LGAs", "35.9 Years", "Range: 32.0 - 42.0 Years"]
        ]
    )

    add_figure(doc, "reports/images/chart_q2_median_age_vs_revenue.png", "Figure 10: Question B: Correlation Scatter Plot & Trendline (Median Age vs Revenue, r = +0.6554)", width_inches=5.0)

    add_callout_box(
        doc,
        "Question B Direct Findings & Statistical Verdict:",
        [
            "• Correlation Coefficient: Pearson r = +0.6554 confirms a strong, statistically significant positive linear relationship (t ≈ 4.51, p < 0.001).",
            "• Coefficient of Determination: R² = 0.4295 indicates that approximately 43% of the variation in STR revenue is explained by LGA age differences.",
            "• Demographic Explanation: Older LGAs (Mosman: 42 yrs, Northern Beaches: 40 yrs, Woollahra: 39 yrs) represent affluent harbourside and coastal enclaves commanding premium nightly rates ($189–$237).",
            "• Younger Enclaves: Younger LGAs (Blacktown: 33 yrs, Canterbury-Bankstown: 35 yrs, Strathfield: 32 yrs) feature family/student clusters and lower yields ($1,311–$1,496)."
        ]
    )

    doc.add_page_break()

    # QUESTION C
    add_summary_box(
        doc,
        "Part 4 — Question C Specification Summary: Optimal Property Configuration",
        ["Determine the optimal listing configuration (property type, room type, accommodates) for the top 5 listing neighbourhoods "
         "ranked by average estimated revenue per active listing to achieve the highest number of stays over the 12-month period."]
    )

    doc.add_paragraph(
        "Question C identified Sydney's Top 5 revenue-generating neighbourhoods and determined the specific property configuration "
        "(property_type × room_type × accommodates) that maximized the total number of guest stays recorded over the 12-month period."
    )

    p_tbl_title = doc.add_paragraph()
    r = p_tbl_title.add_run("Table 5: Optimal Property Configuration for Most Stays in Top 5 Highest-Revenue Neighbourhoods")
    r.bold = True
    r.font.size = Pt(8)

    tbl_qc = doc.add_table(rows=1, cols=8)
    format_table(
        tbl_qc,
        [1.3, 1.0, 1.2, 1.1, 0.6, 1.0, 0.9, 0.9],
        ["Neighbourhood", "Avg Rev", "Best Property Type", "Room Type", "Acc.", "Total Stays", "Avg Stays", "Avg Price"],
        [
            ["Mosman", "$9,326.52", "Entire apartment", "Entire home/apt", "2", "26,476", "24.77", "$189.43"],
            ["Northern Beaches", "$7,591.13", "Entire apartment", "Entire home/apt", "4", "176,680", "23.63", "$237.16"],
            ["Woollahra", "$6,887.47", "Entire apartment", "Entire home/apt", "2", "76,641", "24.87", "$158.24"],
            ["Hunters Hill", "$5,903.32", "Entire apartment", "Entire home/apt", "4", "1,807", "27.80", "$157.46"],
            ["Waverley", "$5,650.55", "Entire apartment", "Entire home/apt", "2", "279,805", "25.57", "$170.24"]
        ]
    )

    add_figure(doc, "reports/images/chart_q3_top5_neighbourhoods_stays.png", "Figure 11: Question C: Optimal Property Configuration Stays in Top 5 Revenue Neighbourhoods", width_inches=5.0)

    add_callout_box(
        doc,
        "Question C Strategic Investment Recommendations:",
        [
            "• Entire Apartment Dominance: Across all Top 5 neighbourhoods, Entire apartment (Entire home/apt) drove the highest number of stays.",
            "• 2-Guest vs 4-Guest Capacity: Couples/solo travelers dominate urban coastal hubs (Waverley: 279,805 stays, Woollahra: 76,641 stays, Mosman: 26,476 stays in 2-guest units). Family-oriented destinations like Northern Beaches peak with 4-guest units (176,680 stays at $237.16/night).",
            "• Turnover Rate: High-revenue configurations average 23.6 to 27.8 stays per listing annually, demonstrating consistent short-term occupancy."
        ]
    )

    doc.add_page_break()

    # QUESTION D
    add_summary_box(
        doc,
        "Part 4 — Question D Specification Summary: Host Portfolio Concentration",
        ["For hosts operating multiple listings, evaluate whether their properties are concentrated within the same LGA "
         "or distributed across multiple LGAs across Greater Sydney."]
    )

    doc.add_paragraph(
        "Question D evaluates the geographic footprint of multi-listing hosts (n = 5,095 hosts with 2+ listings) across Local Government Areas "
        "using point-in-time dimension links between fact_listings, dim_property, and dim_suburb."
    )

    p_tbl_title = doc.add_paragraph()
    r = p_tbl_title.add_run("Table 6: Multi-Listing Host Geographic Distribution Pattern")
    r.bold = True
    r.font.size = Pt(8)

    tbl_qd = doc.add_table(rows=1, cols=3)
    format_table(
        tbl_qd,
        [3.0, 2.0, 2.0],
        ["Distribution Pattern", "Total Hosts", "Percentage of Multi-Listing Hosts"],
        [
            ["Concentrated (Same LGA)", "3,910", "76.74%"],
            ["Distributed (2+ LGAs)", "1,185", "23.26%"]
        ]
    )

    add_figure(doc, "reports/images/chart_q4_host_concentration.png", "Figure 12: Question D: Multi-Listing Host Portfolio Geographic Distribution Pattern", width_inches=3.8)

    add_callout_box(
        doc,
        "Question D Direct Findings & Strategic Implications:",
        [
            "• Localized Operations: Over three-quarters (76.74%, 3,910 hosts) of multi-listing operators concentrate all units within a single LGA, reflecting localized clustering and operational efficiencies in maintenance, cleaning contracts, and key management.",
            "• Distributed Operators: 23.26% (1,185 hosts) operate multi-LGA portfolios, representing commercial property management companies and institutional STR syndicates scaling across Greater Sydney."
        ]
    )

    doc.add_page_break()

    # QUESTION E
    add_summary_box(
        doc,
        "Part 4 — Question E Specification Summary: Mortgage Repayment Coverage",
        ["For single-listing hosts, assess whether 12-month estimated revenue covers annualised median mortgage repayments in their LGA. "
         "Identify which LGA achieves the highest percentage of hosts capable of covering mortgage costs."]
    )

    doc.add_paragraph(
        "Question E evaluates single-listing hosts by aggregating their 12-month estimated revenue and benchmarking against the annualised median mortgage "
        "repayment (median_mortgage_repay_monthly * 12) from Census G02 for each LGA."
    )

    p_tbl_title = doc.add_paragraph()
    r = p_tbl_title.add_run("Table 7: Single-Listing Hosts Covering Annualised Median Mortgage (Top LGAs)")
    r.bold = True
    r.font.size = Pt(8)

    tbl_qe = doc.add_table(rows=1, cols=6)
    format_table(
        tbl_qe,
        [1.6, 1.0, 1.0, 1.1, 1.2, 1.1],
        ["LGA Name", "Single Hosts", "Hosts Covering", "% Covering", "Avg Annual Rev", "Annual Mortgage"],
        [
            ["Northern Beaches", "4,223", "2,382", "56.41%", "$70,955.49", "$33,600.00"],
            ["Mosman", "340", "178", "52.35%", "$74,570.27", "$36,000.00"],
            ["Sutherland Shire", "492", "232", "47.15%", "$43,727.79", "$29,124.00"],
            ["Waverley", "4,119", "1,903", "46.20%", "$52,211.35", "$36,000.00"],
            ["Hunters Hill", "55", "25", "45.45%", "$47,992.33", "$36,396.00"],
            ["Sydney", "5,576", "2,487", "44.60%", "$36,123.32", "$29,988.00"],
            ["Randwick", "2,434", "1,085", "44.58%", "$42,329.13", "$31,200.00"],
            ["North Sydney", "958", "414", "43.22%", "$43,325.06", "$31,200.00"],
            ["Inner West", "1,888", "747", "39.57%", "$38,011.95", "$31,200.00"],
            ["Willoughby", "352", "130", "36.93%", "$53,688.10", "$34,524.00"],
            ["Woollahra", "1,262", "465", "36.85%", "$48,412.01", "$38,400.00"],
            ["Blacktown", "213", "27", "12.68%", "$14,905.41", "$25,800.00"]
        ]
    )

    add_figure(doc, "reports/images/chart_q5_mortgage_coverage.png", "Figure 13: Question E: Single-Listing Hosts Covering Annualised Median Mortgage by LGA", width_inches=5.0)

    add_callout_box(
        doc,
        "Question E Direct Findings & Economic Insights:",
        [
            "• Top Performing LGA: Northern Beaches ranks #1 in Greater Sydney, with 56.41% of single-listing hosts earning more than the annualised median mortgage ($33,600), generating an average of $70,955 in annual revenue.",
            "• Second Ranked: Mosman follows at 52.35% covering mortgage, averaging $74,570 in annual STR income against a $36,000 annual mortgage.",
            "• Third Ranked: Sutherland Shire achieves 47.15% coverage, averaging $43,728 revenue against a $29,124 mortgage.",
            "• Western Suburbs Gap: In outer Western Sydney (Blacktown: 12.68%, Campbelltown: 14.81%, Fairfield: 15.00%), fewer than 1 in 6 single-listing hosts generate enough revenue to cover the median mortgage."
        ]
    )

    doc.add_page_break()

    # 7. Issues, Bugs Faced and Engineering Resolutions
    h7 = doc.add_heading(level=1)
    r = h7.add_run("7. Issues, Bugs Faced and Engineering Resolutions")
    r.font.size = Pt(13)
    r.bold = True
    r.font.color.rgb = RGBColor(0, 80, 160)

    issues = [
        ("7.1 Cross-Platform POSIX Path Incompatibilities in Cloud Composer",
         "Cloud Composer mounts DAG assets via GCS FUSE to /home/airflow/gcs/data/, whereas local Docker binds to /opt/airflow/data/. Hardcoded paths triggered FileNotFoundError during cloud execution.",
         "Engineered get_file_content() to check Composer GCS mounts, native GCSHook blob streaming, and local container mounts progressively.",
         "Achieved zero-modification pipeline portability across local Docker and production Google Cloud Composer 2 clusters."),
        
        ("7.2 Custom Schema Name Macro Override in dbt",
         "dbt's default schema macro prefixed target schemas (e.g. public_silver, public_gold), violating project namespace specifications and breaking Part 4 analytical queries.",
         "Created dbt_bde/macros/generate_schema_name.sql to override default schema generation and return custom schema names cleanly.",
         "Schemas materialized cleanly as bronze, silver, and gold namespaces across development and production targets."),

        ("7.3 July Scrape Date Anomaly & September Double-Count Fix",
         "File 07_2020.csv contained 4,780 rows stamped with future scrape dates (2020-09-05). Naive pipelines deriving month from scrape date undercounted July (31,277) and inflated September (39,609 with duplicate listings).",
         "In silver.stg_listings, derived canonical month_year strictly from file_source and re-aligned out-of-month scrape dates to July's modal scrape date (2020-07-14).",
         "Restored exact monthly volume (July: 36,057, September: 34,829), eliminated 4,758 duplicate listings in September, and ensured flawless temporal joins."),

        ("7.4 Property Type Harmonization Across Longitudinal Batches",
         "Inside Airbnb modified taxonomy after August 2020. Pre-August files used generic categories (Apartment, House, Hotel) while post-August used specific names (Entire apartment, Private room in house), fracturing datamarts.",
         "Implemented standardized CASE mapping in silver.stg_listings matching room_type and property_type to post-August conventions across 100% of rows.",
         "Eliminated fragmented groupings across all 412,122 records in dm_property_type and Question C."),

        ("7.5 SCD Type 2 State-Start Snapshot Strategy",
         "Snapshots ordering by scraped_date ASC froze records at their first-seen version, ignoring subsequent attribute changes and causing active-flag mismatches against fact records.",
         "Re-architected snapshots to track state changes dynamically, setting updated_at to the timestamp when each distinct attribute state began.",
         "Generated 49,072 property versions (3,459 closed, 45,613 active) and 34,610 host versions (3,609 closed, 31,001 active) with 0 mismatches between fact availability flags and dimension records."),

        ("7.6 Point-in-Time Temporal Join Cardinality Control",
         "Joining transactional facts to SCD Type 2 dimensions purely on natural keys produces Cartesian fan-out because entities have multiple historical versions.",
         "Enforced strict validity interval predicates: fact.scraped_date >= dim.dbt_valid_from AND (fact.scraped_date < dim.dbt_valid_to OR dim.dbt_valid_to IS NULL).",
         "Maintained exact 1:1 cardinality matching all 412,122 fact rows across all 12 snapshot months.")
    ]

    for title, iss, res, out in issues:
        doc.add_heading(title, level=2)
        p = doc.add_paragraph()
        p.add_run("Issue: ").bold = True
        p.add_run(iss)
        
        p = doc.add_paragraph()
        p.add_run("Resolution: ").bold = True
        p.add_run(res)

        p = doc.add_paragraph()
        p.add_run("Outcome: ").bold = True
        p.add_run(out)

    doc.add_heading("7.7 Operational Replication Checklist for Peer Engineers", level=2)
    doc.add_paragraph("To reproduce the complete pipeline end-to-end on local Docker or GCP Cloud Composer, execute the following verified CLI sequence:")
    add_code_block(doc,
        "# 1. Launch local Docker infrastructure or connect to Cloud SQL\n"
        "docker compose up -d\n"
        "# 2. Initialize Bronze schemas & trigger Airflow ingestion\n"
        "psql -h <CLOUD_SQL_IP> -U postgres -d postgres -f sql/01_create_bronze_schema.sql  # or localhost for Docker\n"
        "airflow dags trigger load_airbnb_census_dag\n"
        "# 3. Execute dbt Silver staging views & SCD Type 2 snapshots\n"
        "dbt run --select stg_listings\n"
        "dbt snapshot\n"
        "# 4. Build Gold Star Schema, analytical datamarts & test assertions\n"
        "dbt run --select gold\n"
        "dbt test"
    )
    doc.add_paragraph("Audit accounting validated against automated assertions and database checks:")

    tbl_check = doc.add_table(rows=1, cols=4)
    format_table(
        tbl_check,
        [1.8, 1.8, 1.1, 1.8],
        ["Pipeline Component", "Target Output Metric", "Status", "Verification Method"],
        [
            ["Airflow Ingestion DAG", "4 Green Tasks (100% Success)", "CONFIRMED", "Airflow Grid View & Task Logs"],
            ["Bronze Data Ingestion", "412,122 Listings, 4,734 Ref Rows", "CONFIRMED", "PostgreSQL Row Count Assertions"],
            ["Silver Staging Cleansing", "Regex Currency / Date Parsing", "CONFIRMED", "dbt run --select stg_listings"],
            ["Silver SCD2 Snapshots", "3 Dimension Snapshots Active", "CONFIRMED", "dbt snapshot (PASS=3, WARN=0)"],
            ["Gold Star Schema", "fact_listings (IDs & Metrics)", "CONFIRMED", "dbt run --select gold (PASS=11)"],
            ["Analytical Datamarts", "3 Datamarts with MoM Metrics", "CONFIRMED", "Point-in-Time Join SQL Queries"],
            ["Part 4 Ad-Hoc Analytics", "Q(a) through Q(e) Empirical Findings", "CONFIRMED", "Deterministic SQL Executions"],
            ["Local Docker Reproducibility", "Single-command docker compose", "CONFIRMED", "Tested on Docker & Python 3.10"]
        ]
    )

    output_path = "reports/Assignment_3_Report_Aryan_Goel.docx"
    doc.save(output_path)
    print(f"Report successfully saved to {output_path}")

if __name__ == "__main__":
    generate_report()
