"""
USDA ERS County-Level Unemployment & Income Analysis (2000-2023)
===============================================================
Step 1: Data Exploration
Step 2: Indicator Construction
Step 3: Anomaly County Identification
Step 4: Visualization (Plotly)
Step 5: Generate HTML Report
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
import os

# ============================================================
# LOAD DATA
# ============================================================
print("Loading data...")
df_raw = pd.read_excel(
    'usda_unemployment_income_2000_2023.xlsx',
    sheet_name='Unemployment Med HH Income',
    header=4
)

# Remove trailing metadata rows (those with NaN FIPS_Code)
df_raw = df_raw[df_raw['FIPS_Code'].notna()].copy()
df_raw['FIPS_Code'] = df_raw['FIPS_Code'].astype(int).astype(str).str.zfill(5)  # zero-pad FIPS
print(f"Loaded {len(df_raw)} records, {len(df_raw.columns)} columns")

# ============================================================
# STEP 1: DATA EXPLORATION
# ============================================================
print("\n" + "="*60)
print("STEP 1: DATA EXPLORATION")
print("="*60)

# --- 1a: Identify record types ---
# Check if rows are counties, states, or national
df_raw['FIPS_len'] = df_raw['FIPS_Code'].str.len()
state_mask = df_raw['FIPS_Code'].str[2:] == '000'
us_mask = df_raw['FIPS_Code'] == '00000'
county_mask = (~state_mask) & (~us_mask)

n_counties = county_mask.sum()
n_states = state_mask.sum()
n_us = us_mask.sum()

print(f"\nRecords: US={n_us}, States={n_states}, Counties={n_counties}")

# --- 1b: Field Dictionary ---
print("\n--- Field Dictionary ---")
field_dict = {
    'identity': ['FIPS_Code', 'State', 'Area_Name'],
    'rural_class': ['Rural_Urban_Continuum_Code_2023', 'Urban_Influence_Code_2013', 'Metro_2023'],
    'labor_income': ['Median_Household_Income_2022', 'Med_HH_Income_Percent_of_State_Total_2022']
}
years = range(2000, 2024)
field_dict['annual'] = []
for y in years:
    field_dict['annual'].extend([
        f'Civilian_labor_force_{y}', f'Employed_{y}',
        f'Unemployed_{y}', f'Unemployment_rate_{y}'
    ])

for cat, cols in field_dict.items():
    print(f"  {cat}: {len(cols)} fields")
    if cat == 'annual':
        print(f"    Years: {min(years)}-{max(years)}, 4 vars/year × 24 years = 96 fields")

# --- 1c: Missing Rate Analysis ---
print("\n--- Missing Rate Analysis ---")
# Focus on county-level
df_cty = df_raw[county_mask].copy()

# Unemployment rate missing rates
unemp_cols = [f'Unemployment_rate_{y}' for y in years]
missing_unemp = df_cty[unemp_cols].isnull().mean() * 100
print("Unemployment rate missing rates (%):")
for y in range(2000, 2024):
    rate = missing_unemp[f'Unemployment_rate_{y}']
    flag = " <--" if rate > 5 else ""
    print(f"  {y}: {rate:.2f}%{flag}")

# Income missing rate
inc_missing = df_cty['Median_Household_Income_2022'].isnull().mean() * 100
print(f"\nMedian_Household_Income_2022 missing rate: {inc_missing:.2f}%")

# Rural classification missing
for col in field_dict['rural_class']:
    miss = df_cty[col].isnull().mean() * 100
    if miss > 0:
        print(f"  {col} missing: {miss:.2f}%")

# --- 1d: Time Span & Coverage ---
print(f"\n--- Time Span ---")
print(f"Years covered: 2000-2023 (24 years)")
print(f"Total county records: {n_counties}")
print(f"Unique states (with counties): {df_cty['State'].nunique()}")

# Check consistency: does each county have all 24 years?
print("\n--- County Completeness Check ---")
year_coverage = df_cty[unemp_cols].notnull().sum(axis=1)
complete_cty = (year_coverage == 24).sum()
partial_cty = (year_coverage > 0) & (year_coverage < 24)
zero_cty = (year_coverage == 0).sum()
print(f"Counties with all 24 years: {complete_cty}")
print(f"Counties with partial data: {partial_cty.sum()}")
print(f"Counties with no data: {zero_cty}")

# --- 1e: State/County identifier consistency ---
print("\n--- State/County Identifier Consistency ---")
# Check FIPS uniqueness
dup_fips = df_cty['FIPS_Code'].duplicated().sum()
print(f"Duplicate FIPS codes in counties: {dup_fips}")

# Check State + Area_Name uniqueness
dup_name = df_cty.duplicated(subset=['State', 'Area_Name']).sum()
print(f"Duplicate (State, Area_Name) combos: {dup_name}")

# Check that FIPS has consistent structure (state_cc + county_ccc)
print(f"FIPS format check: all 5-digit = {df_cty['FIPS_Code'].str.match(r'^\d{5}$').all()}")

# Print data types
print(f"\n--- Key Column Types ---")
for col in ['FIPS_Code', 'State', 'Area_Name', 'Metro_2023']:
    print(f"  {col}: {df_cty[col].dtype}")

# ============================================================
# STEP 2: INDICATOR CONSTRUCTION
# ============================================================
print("\n" + "="*60)
print("STEP 2: INDICATOR CONSTRUCTION")
print("="*60)

# --- 2a: Unemployment Rate: YoY, MoM not applicable (annual data), 3yr MA ---
print("\n--- 2a: Unemployment Rate Metrics ---")

# Ensure numeric
for y in years:
    df_cty[f'Unemployment_rate_{y}'] = pd.to_numeric(df_cty[f'Unemployment_rate_{y}'], errors='coerce')

# YoY change
for y in range(2001, 2024):
    df_cty[f'UR_YoY_{y}'] = df_cty[f'Unemployment_rate_{y}'] - df_cty[f'Unemployment_rate_{y-1}']

# 3-year moving average
for y in range(2002, 2024):
    df_cty[f'UR_MA3_{y}'] = df_cty[[f'Unemployment_rate_{y-2}', f'Unemployment_rate_{y-1}', f'Unemployment_rate_{y}']].mean(axis=1)

# 2020-2021 COVID shock magnitude
df_cty['UR_shock_2020'] = df_cty['Unemployment_rate_2020'] - df_cty['Unemployment_rate_2019']
df_cty['UR_shock_2020_2021'] = df_cty['Unemployment_rate_2020'] - df_cty['Unemployment_rate_2019']
df_cty['UR_recovery_2022'] = df_cty['Unemployment_rate_2022'] - df_cty['Unemployment_rate_2019']
df_cty['UR_recovery_2023'] = df_cty['Unemployment_rate_2023'] - df_cty['Unemployment_rate_2019']

print("Created YoY change: 2001-2023")
print("Created 3-year MA: 2002-2023")
print("Created COVID shock metrics")

# --- 2b: Household Income ---
print("\n--- 2b: Household Income Analysis ---")
print("LIMITATION: USDA dataset only provides Median_Household_Income for 2022 (single year).")
print("No CPI deflator available. All income analysis is nominal and cross-sectional for 2022.")

# Income statistics
inc_valid = df_cty['Median_Household_Income_2022'].dropna()
print(f"\nMedian Household Income 2022 (nominal, county-level):")
print(f"  N={len(inc_valid)} counties")
print(f"  Mean: ${inc_valid.mean():,.0f}")
print(f"  Median: ${inc_valid.median():,.0f}")
print(f"  Min: ${inc_valid.min():,.0f}")
print(f"  Max: ${inc_valid.max():,.0f}")
print(f"  Std: ${inc_valid.std():,.0f}")

# Income as % of state total
inc_pct_valid = df_cty['Med_HH_Income_Percent_of_State_Total_2022'].dropna()
print(f"\nIncome as % of State Total 2022:")
print(f"  N={len(inc_pct_valid)} counties")
print(f"  Mean: {inc_pct_valid.mean():.1f}%")
print(f"  Range: [{inc_pct_valid.min():.1f}%, {inc_pct_valid.max():.1f}%]")

# --- 2c: Regional Divergence ---
print("\n--- 2c: Regional Divergence Metrics ---")

# State-level unemployment rate aggregation
# Use only counties with data
state_ur = {}
for y in years:
    col = f'Unemployment_rate_{y}'
    grp = df_cty.groupby('State')[col].agg(['mean', 'std', 'min', 'max', 
        lambda x: x.quantile(0.25), lambda x: x.quantile(0.75),
        lambda x: x.quantile(0.1), lambda x: x.quantile(0.9)])
    grp.columns = ['mean', 'std', 'min', 'max', 'p25', 'p75', 'p10', 'p90']
    grp['iqr'] = grp['p75'] - grp['p25']
    grp['p90_p10'] = grp['p90'] - grp['p10']
    state_ur[y] = grp

# National cross-county Gini (simplified)
def gini_coefficient(values):
    """Calculate Gini coefficient"""
    values = np.sort(values.dropna())
    n = len(values)
    if n == 0:
        return np.nan
    index = np.arange(1, n + 1)
    return (2 * np.sum(index * values)) / (n * np.sum(values)) - (n + 1) / n

# National Gini of unemployment rate across counties
print("\nNational Gini Coefficient of County Unemployment Rate:")
gini_series = {}
for y in years:
    gini = gini_coefficient(df_cty[f'Unemployment_rate_{y}'])
    gini_series[y] = gini
    print(f"  {y}: {gini:.4f}")

# Theil index (simplified)
def theil_index(values):
    """Calculate Theil T index"""
    values = values.dropna()
    if len(values) == 0 or values.sum() == 0:
        return np.nan
    mean_val = values.mean()
    return np.mean((values / mean_val) * np.log(values / mean_val))

print("\nNational Theil Index of County Unemployment Rate:")
for y in years:
    t = theil_index(df_cty[f'Unemployment_rate_{y}'])
    print(f"  {y}: {t:.6f}")

# State internal divergence
print("\nState-level internal divergence (p90-p10 of unemployment rate):")
div_2023 = state_ur[2023]['p90_p10'].sort_values(ascending=False)
print("Top 5 most divergent states (2023):")
for state, val in div_2023.head(5).items():
    print(f"  {state}: {val:.1f}pp")
print("Bottom 5 least divergent states (2023):")
for state, val in div_2023.tail(5).items():
    print(f"  {state}: {val:.1f}pp")

# ============================================================
# STEP 3: ANOMALY COUNTY IDENTIFICATION
# ============================================================
print("\n" + "="*60)
print("STEP 3: ANOMALY COUNTY IDENTIFICATION")
print("="*60)

# --- 3a: COVID Shock Top N (2020 vs 2019) ---
print("\n--- 3a: COVID Shock Magnitude (2020 UR - 2019 UR) ---")
shock = df_cty[['FIPS_Code', 'State', 'Area_Name', 'UR_shock_2020',
                'Unemployment_rate_2019', 'Unemployment_rate_2020']].copy()
shock = shock.dropna(subset=['UR_shock_2020'])
shock = shock.sort_values('UR_shock_2020', ascending=False)

print("Top 20 counties by COVID shock magnitude:")
for i, (_, row) in enumerate(shock.head(20).iterrows()):
    print(f"  {i+1}. {row['Area_Name']}, {row['State']}: "
          f"{row['Unemployment_rate_2019']:.1f}% → {row['Unemployment_rate_2020']:.1f}% "
          f"(+{row['UR_shock_2020']:.1f}pp)")

# --- 3b: Recovery Slowest Top N ---
# Recovery indicator: 2023 UR still above 2019 UR by > X pp, 
# AND 2023 UR > national median 2023 UR
print("\n--- 3b: Recovery Metrics ---")
print("Recovery Indicator = (2023 UR - 2019 UR), filtered to counties with 2023 UR > national median")
median_ur_2023 = df_cty['Unemployment_rate_2023'].median()

# Compute recovery lag
recovery = df_cty[['FIPS_Code', 'State', 'Area_Name',
                   'Unemployment_rate_2019', 'Unemployment_rate_2020',
                   'Unemployment_rate_2021', 'Unemployment_rate_2022',
                   'Unemployment_rate_2023']].copy()
recovery['peak'] = recovery[['Unemployment_rate_2020', 'Unemployment_rate_2021']].max(axis=1)
recovery['recovery_lag'] = recovery['Unemployment_rate_2023'] - recovery['Unemployment_rate_2019']
recovery['shock_depth'] = recovery['peak'] - recovery['Unemployment_rate_2019']
recovery['recovery_pct'] = (
    (recovery['peak'] - recovery['Unemployment_rate_2023']) / 
    (recovery['peak'] - recovery['Unemployment_rate_2019']).clip(lower=0.01) * 100
)
# Filter: 2023 UR still above national median AND recovery_lag > 0
recovery_filtered = recovery[
    (recovery['Unemployment_rate_2023'] > median_ur_2023) &
    (recovery['recovery_lag'] > 0)
].dropna(subset=['recovery_lag']).sort_values('recovery_lag', ascending=False)

print(f"Counties still above 2019 UR with UR > national median ({median_ur_2023:.1f}%): {len(recovery_filtered)}")
print("\nTop 20 slowest-recovering counties:")
for i, (_, row) in enumerate(recovery_filtered.head(20).iterrows()):
    print(f"  {i+1}. {row['Area_Name']}, {row['State']}: "
          f"2019={row['Unemployment_rate_2019']:.1f}%, "
          f"Peak={row['peak']:.1f}%, "
          f"2023={row['Unemployment_rate_2023']:.1f}% "
          f"(lag={row['recovery_lag']:.1f}pp)")

# Additional recovery metric: % of peak reduction
print("\n--- Recovery % from Peak ---")
recovery_valid = recovery.dropna(subset=['recovery_pct'])
recovery_valid = recovery_valid[recovery_valid['shock_depth'] > 0.5]  # meaningful shock
recovery_slow = recovery_valid[
    (recovery_valid['Unemployment_rate_2023'] > median_ur_2023)
].sort_values('recovery_pct').head(20)

print("Top 20 counties with lowest % recovery from peak (still above median):")
for i, (_, row) in enumerate(recovery_slow.iterrows()):
    print(f"  {i+1}. {row['Area_Name']}, {row['State']}: "
          f"Peak={row['peak']:.1f}%, "
          f"2023={row['Unemployment_rate_2023']:.1f}%, "
          f"Recovery={row['recovery_pct']:.0f}%")

# 持续恶化型: 2023 > peak
worsened = recovery_valid[recovery_valid['Unemployment_rate_2023'] > recovery_valid['peak']]
print(f"\nCounties where 2023 UR EXCEEDS COVID peak: {len(worsened)}")

# ============================================================
# STEP 4: VISUALIZATIONS (Plotly)
# ============================================================
print("\n" + "="*60)
print("STEP 4: CREATING VISUALIZATIONS")
print("="*60)

# --- Color scheme ---
bg_color = '#1a1a2e'
plot_bg = '#16213e'
paper_bg = '#1a1a2e'
font_color = '#e0e0e0'
grid_color = '#2a2a4a'
accent = '#00d2ff'

# --- 4a: National Trend + Quantile Bands ---
print("Creating national trend chart...")
national_ur = {}
for y in years:
    col = f'Unemployment_rate_{y}'
    data = df_cty[col].dropna()
    national_ur[y] = {
        'median': data.median(),
        'mean': data.mean(),
        'p25': data.quantile(0.25),
        'p75': data.quantile(0.75),
        'p10': data.quantile(0.10),
        'p90': data.quantile(0.90),
        'min': data.min(),
        'max': data.max()
    }

df_nat = pd.DataFrame(national_ur).T
df_nat.index.name = 'year'

fig_trend = go.Figure()

# Shaded bands
fig_trend.add_trace(go.Scatter(
    x=list(years), y=df_nat['p10'],
    mode='lines', line=dict(width=0), showlegend=False,
    hoverinfo='skip'
))
fig_trend.add_trace(go.Scatter(
    x=list(years), y=df_nat['p90'],
    mode='lines', fill='tonexty',
    fillcolor='rgba(0, 210, 255, 0.08)',
    line=dict(width=0),
    name='P10-P90', showlegend=True
))

fig_trend.add_trace(go.Scatter(
    x=list(years), y=df_nat['p25'],
    mode='lines', line=dict(width=0), showlegend=False,
    hoverinfo='skip'
))
fig_trend.add_trace(go.Scatter(
    x=list(years), y=df_nat['p75'],
    mode='lines', fill='tonexty',
    fillcolor='rgba(0, 210, 255, 0.15)',
    line=dict(width=0),
    name='P25-P75', showlegend=True
))

# Median line
fig_trend.add_trace(go.Scatter(
    x=list(years), y=df_nat['median'],
    mode='lines+markers',
    line=dict(color='#00d2ff', width=3),
    marker=dict(size=6, color='#00d2ff'),
    name='National Median'
))

# Mean line
fig_trend.add_trace(go.Scatter(
    x=list(years), y=df_nat['mean'],
    mode='lines',
    line=dict(color='#ff6b6b', width=2, dash='dash'),
    name='National Mean'
))

# Vertical line for COVID
fig_trend.add_vline(x=2020, line_dash='dash', line_color='rgba(255,255,255,0.3)',
                     annotation_text='COVID-19', annotation_position='top left')

fig_trend.update_layout(
    title='US County-Level Unemployment Rate: National Trend & Quantile Bands (2000-2023)',
    xaxis=dict(title='Year', dtick=2, gridcolor=grid_color),
    yaxis=dict(title='Unemployment Rate (%)', gridcolor=grid_color),
    plot_bgcolor=plot_bg, paper_bgcolor=paper_bg,
    font=dict(color=font_color, size=12),
    legend=dict(orientation='h', yanchor='top', y=1.12, xanchor='center', x=0.5),
    hovermode='x unified'
)

fig_trend.write_html('chart_national_trend.html', include_plotlyjs='cdn')
print("  -> chart_national_trend.html")

# --- 4b: Gini Coefficient Over Time ---
print("Creating Gini trend chart...")
fig_gini = go.Figure()
fig_gini.add_trace(go.Scatter(
    x=list(years), y=[gini_series[y] for y in years],
    mode='lines+markers',
    line=dict(color='#00d2ff', width=3),
    marker=dict(size=8, color='#00d2ff'),
    name='Gini Coefficient'
))
fig_gini.add_vline(x=2020, line_dash='dash', line_color='rgba(255,255,255,0.3)')

fig_gini.update_layout(
    title='Cross-County Unemployment Rate Inequality (Gini Coefficient)',
    xaxis=dict(title='Year', dtick=2, gridcolor=grid_color),
    yaxis=dict(title='Gini Coefficient', gridcolor=grid_color),
    plot_bgcolor=plot_bg, paper_bgcolor=paper_bg,
    font=dict(color=font_color, size=12),
    hovermode='x unified'
)
fig_gini.write_html('chart_gini_trend.html', include_plotlyjs='cdn')
print("  -> chart_gini_trend.html")

# --- 4c: State-level Heatmap (Top 25 States, 2000-2023) ---
print("Creating state-level heatmap...")
state_mean_ur = pd.DataFrame()
for y in years:
    state_mean_ur[y] = state_ur[y]['mean']
# Sort by average UR
state_order = state_mean_ur.mean(axis=1).sort_values(ascending=False)
top_states = state_order.head(25)
state_matrix = state_mean_ur.loc[top_states.index]

fig_heatmap = px.imshow(
    state_matrix,
    labels=dict(x='Year', y='State', color='Unemployment Rate (%)'),
    x=list(years),
    y=state_matrix.index,
    color_continuous_scale='Blues',
    aspect='auto',
    title='State-Level Unemployment Rate Heatmap (Top 25 States, 2000-2023)'
)
fig_heatmap.update_layout(
    plot_bgcolor=plot_bg, paper_bgcolor=paper_bg,
    font=dict(color=font_color, size=11),
    xaxis=dict(dtick=2),
    coloraxis_colorbar=dict(title='UR %')
)
fig_heatmap.write_html('chart_state_heatmap.html', include_plotlyjs='cdn')
print("  -> chart_state_heatmap.html")

# --- 4d: Top 20 COVID Shock Counties Bar Chart ---
print("Creating COVID shock bar chart...")
top_shock_20 = shock.head(20).copy()
top_shock_20['label'] = top_shock_20['Area_Name'] + ', ' + top_shock_20['State']

fig_shock = go.Figure()
fig_shock.add_trace(go.Bar(
    y=top_shock_20['label'][::-1],
    x=top_shock_20['UR_shock_2020'][::-1],
    orientation='h',
    marker=dict(
        color=top_shock_20['UR_shock_2020'][::-1],
        colorscale='Reds',
        showscale=True,
        colorbar=dict(title='Shock (pp)')
    ),
    text=[f"+{v:.1f}pp" for v in top_shock_20['UR_shock_2020'][::-1]],
    textposition='outside',
    textfont=dict(color=font_color, size=11)
))
fig_shock.update_layout(
    title='Top 20 Counties: COVID Unemployment Shock (UR 2020 - UR 2019)',
    xaxis=dict(title='Unemployment Rate Increase (pp)', gridcolor=grid_color),
    plot_bgcolor=plot_bg, paper_bgcolor=paper_bg,
    font=dict(color=font_color, size=11),
    height=600, margin=dict(l=200)
)
fig_shock.write_html('chart_shock_top20.html', include_plotlyjs='cdn')
print("  -> chart_shock_top20.html")

# --- 4e: Slow Recovery Counties Bar Chart ---
print("Creating recovery chart...")
slow_20 = recovery_filtered.head(20).copy()
slow_20['label'] = slow_20['Area_Name'] + ', ' + slow_20['State']

fig_recovery = go.Figure()
fig_recovery.add_trace(go.Bar(
    y=slow_20['label'][::-1],
    x=slow_20['recovery_lag'][::-1],
    orientation='h',
    marker=dict(
        color=slow_20['recovery_lag'][::-1],
        colorscale='OrRd',
        showscale=True,
        colorbar=dict(title='Recovery Lag (pp)')
    ),
    text=[f"+{v:.1f}pp" for v in slow_20['recovery_lag'][::-1]],
    textposition='outside',
    textfont=dict(color=font_color, size=11)
))
fig_recovery.update_layout(
    title='Top 20 Slowest-Recovering Counties: 2023 UR Still Above 2019 (UR > National Median)',
    xaxis=dict(title='Recovery Lag (2023 UR - 2019 UR, pp)', gridcolor=grid_color),
    plot_bgcolor=plot_bg, paper_bgcolor=paper_bg,
    font=dict(color=font_color, size=11),
    height=600, margin=dict(l=200)
)
fig_recovery.write_html('chart_recovery_top20.html', include_plotlyjs='cdn')
print("  -> chart_recovery_top20.html")

# --- 4f: State Internal Divergence (p90-p10), 2023 ---
print("Creating state divergence chart...")
div_2023_sorted = div_2023.sort_values(ascending=False)
fig_div = go.Figure()
fig_div.add_trace(go.Bar(
    y=div_2023_sorted.index,
    x=div_2023_sorted.values,
    orientation='h',
    marker=dict(
        color=div_2023_sorted.values,
        colorscale='Viridis',
        showscale=True,
        colorbar=dict(title='P90-P10 (pp)')
    )
))
fig_div.update_layout(
    title='State Internal Unemployment Divergence: P90-P10 Spread (2023)',
    xaxis=dict(title='P90 - P10 (percentage points)', gridcolor=grid_color),
    yaxis=dict(title='State'),
    plot_bgcolor=plot_bg, paper_bgcolor=paper_bg,
    font=dict(color=font_color, size=11),
    height=900,
    margin=dict(l=50)
)
fig_div.write_html('chart_state_divergence.html', include_plotlyjs='cdn')
print("  -> chart_state_divergence.html")

# --- 4g: Income vs Unemployment Scatter (2022) ---
print("Creating income vs unemployment scatter...")
df_scatter = df_cty[['FIPS_Code', 'State', 'Area_Name', 
                      'Unemployment_rate_2022', 'Median_Household_Income_2022',
                      'Metro_2023']].dropna()
df_scatter['Metro_Label'] = df_scatter['Metro_2023'].map({0: 'Nonmetro', 1: 'Metro'}).fillna('Unknown')

fig_scatter = px.scatter(
    df_scatter, 
    x='Unemployment_rate_2022', 
    y='Median_Household_Income_2022',
    color='Metro_Label',
    color_discrete_map={'Metro': '#00d2ff', 'Nonmetro': '#ff6b6b', 'Unknown': '#888888'},
    hover_data=['State', 'Area_Name'],
    title='County-Level: Unemployment Rate vs Median Household Income (2022)',
    labels={
        'Unemployment_rate_2022': 'Unemployment Rate (%)',
        'Median_Household_Income_2022': 'Median Household Income ($)',
        'Metro_Label': 'Metro Status'
    },
    opacity=0.6
)
fig_scatter.update_layout(
    plot_bgcolor=plot_bg, paper_bgcolor=paper_bg,
    font=dict(color=font_color, size=12),
    xaxis=dict(gridcolor=grid_color),
    yaxis=dict(gridcolor=grid_color),
    height=600
)
fig_scatter.write_html('chart_income_vs_ur.html', include_plotlyjs='cdn')
print("  -> chart_income_vs_ur.html")

# --- 4h: Recovery Dashboard: Peak vs Current ---
print("Creating recovery overview chart...")
fig_recovery_overview = go.Figure()
# Add selected slow-recovery counties as arrows
for i, (_, row) in enumerate(slow_20.iterrows()):
    fig_recovery_overview.add_trace(go.Scatter(
        x=['2019', 'Peak', '2023'],
        y=[row['Unemployment_rate_2019'], row['peak'], row['Unemployment_rate_2023']],
        mode='lines+markers',
        name=row['label'],
        line=dict(width=1.5, color=px.colors.qualitative.Plotly[i % len(px.colors.qualitative.Plotly)]),
        marker=dict(size=6),
        showlegend=False
    ))

fig_recovery_overview.update_layout(
    title='Recovery Trajectory: 20 Slowest-Recovering Counties (2019 → Peak → 2023)',
    xaxis=dict(title='', gridcolor=grid_color),
    yaxis=dict(title='Unemployment Rate (%)', gridcolor=grid_color),
    plot_bgcolor=plot_bg, paper_bgcolor=paper_bg,
    font=dict(color=font_color, size=12),
    height=500
)
fig_recovery_overview.write_html('chart_recovery_trajectory.html', include_plotlyjs='cdn')
print("  -> chart_recovery_trajectory.html")

# ============================================================
# Save processed data for report
# ============================================================
# National trends
df_nat.to_csv('data_national_trends.csv')
# Gini
pd.Series(gini_series, name='Gini').to_csv('data_gini.csv')
# Top shock
top_shock_20.to_csv('data_top_shock.csv', index=False)
# Slow recovery
slow_20.to_csv('data_slow_recovery.csv', index=False)
# State divergence
div_2023_sorted.to_csv('data_state_divergence.csv')
# Shock & recovery
shock_stats = {
    'n_counties': int(n_counties),
    'median_ur_2023': float(median_ur_2023),
    'mean_ur_2023': float(df_nat.loc[2023, 'mean']),
    'p90_p10_2023': float(df_nat.loc[2023, 'p90'] - df_nat.loc[2023, 'p10']),
    'gini_2023': float(gini_series[2023]),
    'gini_2019': float(gini_series[2019]),
    'n_worsened': int(len(worsened)),
    'ur_shock_top5_mean': float(shock.head(5)['UR_shock_2020'].mean()),
    'income_median_2022': float(inc_valid.median()),
    'income_range_2022': [float(inc_valid.min()), float(inc_valid.max())],
    'metro_count': int(df_cty[df_cty['Metro_2023'] == 1].shape[0]),
    'nonmetro_count': int(df_cty[df_cty['Metro_2023'] == 0].shape[0]),
}
with open('data_summary_stats.json', 'w') as f:
    json.dump(shock_stats, f, indent=2)

print("\nAll charts and data exported. Ready for HTML report generation.")
print("Done with Steps 1-4.")
