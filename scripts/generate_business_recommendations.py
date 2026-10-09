#!/usr/bin/env python3
import matplotlib.pyplot as plt
import numpy as np

# Set figure size and clean modern styling
fig, (ax_chart, ax_text) = plt.subplots(1, 2, figsize=(15.5, 8.8), dpi=300, gridspec_kw={'width_ratios': [1.35, 0.95]})
fig.patch.set_facecolor('#FFFFFF')
ax_chart.set_facecolor('#FAFAFC')

# Data for key representative LGAs
lgas = [
    {'name': 'Mosman', 'coverage': 52.35, 'revenue': 9326.52, 'listings': 298, 'color': '#0284C7'},
    {'name': 'Northern Beaches', 'coverage': 56.41, 'revenue': 7591.13, 'listings': 2280, 'color': '#0284C7'},
    {'name': 'Woollahra', 'coverage': 36.85, 'revenue': 6887.47, 'listings': 1262, 'color': '#EA580C'},
    {'name': 'Waverley', 'coverage': 44.50, 'revenue': 6420.15, 'listings': 3100, 'color': '#EA580C'},
    {'name': 'City of Sydney', 'coverage': 44.60, 'revenue': 4250.80, 'listings': 5576, 'color': '#DC2626'},
    {'name': 'Randwick', 'coverage': 44.58, 'revenue': 4180.20, 'listings': 2434, 'color': '#0284C7'},
    {'name': 'North Sydney', 'coverage': 43.22, 'revenue': 4550.00, 'listings': 958, 'color': '#0284C7'},
    {'name': 'Inner West', 'coverage': 39.57, 'revenue': 3120.40, 'listings': 1888, 'color': '#64748B'},
    {'name': 'Sutherland Shire', 'coverage': 47.15, 'revenue': 3640.00, 'listings': 620, 'color': '#10B981'},
    {'name': 'Parramatta', 'coverage': 22.40, 'revenue': 1850.00, 'listings': 510, 'color': '#94A3B8'},
    {'name': 'Canterbury-Bankstown', 'coverage': 18.20, 'revenue': 1495.72, 'listings': 340, 'color': '#94A3B8'},
    {'name': 'Blacktown', 'coverage': 12.68, 'revenue': 1310.99, 'listings': 213, 'color': '#94A3B8'},
    {'name': 'Fairfield', 'coverage': 15.00, 'revenue': 1298.32, 'listings': 185, 'color': '#94A3B8'}
]

# Quadrant background shading
ax_chart.axhspan(4000, 10400, xmin=0.5, xmax=1.0, color='#E0F2FE', alpha=0.35)
ax_chart.axhspan(4000, 10400, xmin=0.0, xmax=0.5, color='#FFEDD5', alpha=0.35)
ax_chart.axhspan(600, 4000, xmin=0.0, xmax=0.5, color='#F1F5F9', alpha=0.5)
ax_chart.axhspan(600, 4000, xmin=0.5, xmax=1.0, color='#ECFDF5', alpha=0.35)

# Benchmarks / Crosshairs
ax_chart.axvline(40, color='#94A3B8', linestyle='--', linewidth=1.2, zorder=2)
ax_chart.axhline(4000, color='#94A3B8', linestyle='--', linewidth=1.2, zorder=2)

ax_chart.text(40.5, 9800, 'Mortgage Coverage Baseline (40%)', fontsize=7.5, color='#64748B', rotation=90, va='top')
ax_chart.text(10, 4150, 'Metropolitan Avg Revenue (AUD 4,000/mo)', fontsize=7.5, color='#64748B')

# Plot Bubbles
for item in lgas:
    sz = np.sqrt(item['listings']) * 15
    ax_chart.scatter(item['coverage'], item['revenue'], s=sz, color=item['color'], alpha=0.85, edgecolors='#0F172A', linewidth=0.8, zorder=4)

# Dedicated label offsets to prevent overlap completely
offsets = {
    'Mosman': (12, -4),
    'Northern Beaches': (12, -10),
    'Woollahra': (-20, 14),
    'Waverley': (12, 12),
    'North Sydney': (-32, 14),
    'City of Sydney': (12, 14),
    'Randwick': (-26, -16),
    'Sutherland Shire': (12, -14),
    'Inner West': (-25, -14),
    'Parramatta': (8, 8),
    'Canterbury-Bankstown': (-38, 14),
    'Fairfield': (8, 12),
    'Blacktown': (-22, -14)
}

for item in lgas:
    dx, dy = offsets.get(item['name'], (5, 5))
    ax_chart.annotate(
        item['name'], 
        (item['coverage'], item['revenue']),
        xytext=(dx, dy), 
        textcoords='offset points',
        fontsize=8.2, 
        fontweight='bold',
        color='#1E293B',
        zorder=5
    )

ax_chart.set_xlim(8, 62)
ax_chart.set_ylim(600, 10400)
ax_chart.set_xlabel('Mortgage Repayment Coverage by Single Hosts (%)', fontsize=10, fontweight='bold', color='#1E293B', labelpad=10)
ax_chart.set_ylabel('Average Estimated Revenue per Active Listing (AUD)', fontsize=10, fontweight='bold', color='#1E293B', labelpad=10)
ax_chart.set_title('Strategic Opportunity vs Regulatory Risk Matrix', fontsize=13, fontweight='bold', color='#0F172A', pad=14)

ax_chart.grid(True, linestyle=':', alpha=0.5, color='#CBD5E1')
ax_chart.spines['top'].set_visible(False)
ax_chart.spines['right'].set_visible(False)
ax_chart.spines['left'].set_color('#CBD5E1')
ax_chart.spines['bottom'].set_color('#CBD5E1')

# Quadrant labels
ax_chart.text(60, 10100, 'ZONE 1: HIGH YIELD\n(Investor Priority)', ha='right', va='top', fontsize=8.2, fontweight='bold', color='#0369A1')
ax_chart.text(10, 10100, 'ZONE 2: HIGH REGULATORY WATCH\n(Commercial Density)', ha='left', va='top', fontsize=8.2, fontweight='bold', color='#C2410C')
ax_chart.text(10, 2400, 'ZONE 3: RESIDENTIAL LOW YIELD\n(Light Touch Policy)', ha='left', va='top', fontsize=8.2, fontweight='bold', color='#64748B')
ax_chart.text(60, 800, 'ZONE 4: SUBURBAN STABLE\n(Domestic Tourism)', ha='right', va='bottom', fontsize=8.2, fontweight='bold', color='#15803D')

# RIGHT PANEL: Clean Recommendations
ax_text.axis('off')
ax_text.text(0.04, 0.96, 'Executive Business Recommendations', fontsize=13, fontweight='bold', color='#0F172A')
ax_text.text(0.04, 0.92, 'Synthesized from 412,122 Records & ABS Census', fontsize=8.8, color='#64748B')

recs = [
    {
        'title': '1. Commercial STR Investors',
        'color': '#0284C7',
        'lines': [
            ('Target Harbourside & Beach Enclaves:', 'Mosman (AUD 9,327/mo) & Northern Beaches offer top yield.'),
            ('Deploy Entire Home / Apt (2–4 Guests):', 'Generates maximum stay volume (176k in NB, 26k in Mosman).'),
            ('Mortgage Viability:', 'Over 52%–56% of single-listing hosts cover their full mortgage.')
        ]
    },
    {
        'title': '2. Housing Councils & Regulators',
        'color': '#DC2626',
        'lines': [
            ('Enforce 180-Day STR Night Caps in CBD & East:', 'High commercial multi-host concentration (64.9% in Sydney LGA).'),
            ('License Multi-Listing Operators:', 'Close commercial loophole on operators managing 3+ properties.'),
            ('Differentiate Policy:', 'Outer Western LGAs show low pressure; keep light-touch rules.')
        ]
    },
    {
        'title': '3. Destination NSW (Tourism)',
        'color': '#059669',
        'lines': [
            ('Capitalize on Coastal Domestic Staycations:', 'Harbour & beach demand remained highly resilient across 12 months.'),
            ('Incentivize Western Tourism Dispersal:', 'Promote cultural corridors to bridge 5.8x revenue gap with the West.')
        ]
    }
]

y_pos = 0.86
card_heights = [0.26, 0.26, 0.21]

for idx, r in enumerate(recs):
    h = card_heights[idx]
    # Card background
    rect = plt.Rectangle((0.02, y_pos - h), 0.96, h, facecolor='#F8FAFC', edgecolor=r['color'], linewidth=1.4, transform=ax_text.transAxes)
    ax_text.add_patch(rect)
    
    # Title badge
    ax_text.text(0.05, y_pos - 0.032, r['title'], fontsize=10, fontweight='bold', color=r['color'], transform=ax_text.transAxes)
    
    # Bullets
    cur_y = y_pos - 0.070
    for bold_text, sub_text in r['lines']:
        ax_text.text(0.05, cur_y, '• ' + bold_text, fontsize=8.2, fontweight='bold', color='#1E293B', transform=ax_text.transAxes)
        ax_text.text(0.08, cur_y - 0.030, sub_text, fontsize=7.8, color='#475569', transform=ax_text.transAxes)
        cur_y -= 0.060
    
    y_pos -= (h + 0.045)

plt.tight_layout()
plt.savefig('reports/images/business_recommendation_matrix.png', bbox_inches='tight', facecolor=fig.get_facecolor(), dpi=300)
print('Successfully generated clean reports/images/business_recommendation_matrix.png')
