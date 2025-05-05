import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import pycountry
import streamlit as st

st.set_page_config(layout="wide", page_title="Hydropower Dashboard")
st.title("Hydropower Visualization Dashboard")
st.markdown("Explore global hydropower capacity, distribution, and trends with interactive charts and filters.")

# ===============================
# Load and preprocess data
# ===============================
@st.cache_data
def load_data():
    df = pd.read_csv("GloHydroRes_vs1.csv")
    df['year'] = pd.to_numeric(df['year'], errors='coerce')
    df['capacity_mw'] = pd.to_numeric(df['capacity_mw'], errors='coerce')
    df['res_vol_mcm'] = df['res_vol_km3'] * 1_000 if 'res_vol_km3' in df.columns else np.nan

    def iso3(country_name):
        try:
            return pycountry.countries.lookup(country_name).alpha_3
        except LookupError:
            return None

    df['Country_Iso3'] = df['country'].map(iso3)
    df = df.dropna(subset=['plant_lat', 'plant_lon'])
    return df

df = load_data()

# ===============================
# Sidebar controls
# ===============================
st.sidebar.header("Filters & Controls")

min_capacity = st.sidebar.slider(
    "Minimum Plant Capacity (MW)",
    min_value=0,
    max_value=int(df['capacity_mw'].max()),
    value=100,
    step=10
)

min_volume = st.sidebar.slider(
    "Minimum Reservoir Volume (Million m³)",
    min_value=0,
    max_value=int(df['res_vol_mcm'].max() / 1_000),
    value=100,
    step=10
) * 1_000  # Convert to m³

year_min = int(df['year'].min())
year_max = int(df['year'].max())
selected_year_range = st.sidebar.slider(
    "Year Range for Animated Map",
    min_value=year_min,
    max_value=year_max,
    value=(year_min, year_max),
    step=1
)

# ===============================
# Plot settings
# ===============================
layout_style = dict(
    template='plotly_white',
    font=dict(family="Arial", size=14),
    title_font=dict(size=22),
)

# ===============================
# 1. Choropleth Map
# ===============================
st.markdown("---")
st.subheader("1. Total Hydropower Capacity by Country")
st.markdown("This map displays the total installed hydropower capacity aggregated by country.")

country_cap = df.groupby('Country_Iso3', as_index=False)['capacity_mw'].sum()
fig1 = px.choropleth(
    country_cap,
    locations='Country_Iso3',
    color='capacity_mw',
    color_continuous_scale='Cividis',
    title='Total Hydropower Capacity by Country (MW)'
)
fig1.update_layout(**layout_style)
st.plotly_chart(fig1, use_container_width=True)

# ===============================
# 2. Bubble Map
# ===============================
st.markdown("---")
st.subheader("2. Hydropower Plants by Reservoir Volume")
st.markdown("This bubble map represents hydropower plants, with bubble size proportional to reservoir volume.")

df_bubble = df[
    (df['res_vol_mcm'] >= min_volume) &
    (df['capacity_mw'] >= min_capacity)
]

fig2 = px.scatter_geo(
    df_bubble,
    lat='plant_lat',
    lon='plant_lon',
    size=np.sqrt(df_bubble['res_vol_mcm'] + 1),
    hover_name='name',
    hover_data={'capacity_mw': ':,.0f', 'res_vol_mcm': ':,.0f'},
    projection='natural earth',
    title='Bubble Map of Hydropower Plants (size ∝ reservoir volume)'
)
fig2.update_layout(**layout_style)
st.plotly_chart(fig2, use_container_width=True)

# ===============================
# 3. Sunburst Chart
# ===============================
st.markdown("---")
st.subheader("3. Capacity Distribution by Country and Plant")
st.markdown("The sunburst chart shows the hierarchy of countries and their individual plants based on installed capacity.")

sun = df.groupby(['country', 'name'], as_index=False)['capacity_mw'].sum()
fig3 = px.sunburst(
    sun,
    path=['country','name'],
    values='capacity_mw',
    title='Sunburst Chart of Hydropower Capacity'
)
fig3.update_layout(**layout_style, height=800)  # Enlarged
st.plotly_chart(fig3, use_container_width=True)

# ===============================
# 4. Time Series
# ===============================
st.markdown("---")
st.subheader("4. Installed Capacity by Country Over Time")
st.markdown("Visualize how each selected country's hydropower capacity evolved over the years.")

df_ts = df.dropna(subset=['year', 'country', 'capacity_mw'])
yearly_country = df_ts.groupby(['country', 'year'], as_index=False)['capacity_mw'].sum()

available_countries = sorted(yearly_country['country'].dropna().unique())
default_candidates = ['China', 'United States']
default_countries = [c for c in default_candidates if c in available_countries]

countries = st.multiselect(
    "Select countries:",
    available_countries,
    default=default_countries
)

fig4 = go.Figure()
for country in countries:
    data = yearly_country[yearly_country['country'] == country]
    fig4.add_trace(go.Scatter(
        x=data['year'],
        y=data['capacity_mw'],
        mode='lines',
        name=country,
        hovertemplate='<b>%{text}</b><br>Year: %{x}<br>Capacity: %{y:.2f} MW',
        text=[country]*len(data),
    ))
fig4.update_layout(
    title='Installed Capacity by Country Over Time',
    xaxis_title='Year',
    yaxis_title='Installed Capacity (MW)',
    hovermode='x unified',
    **layout_style
)
st.plotly_chart(fig4, use_container_width=True)

# ===============================
# 5. Animated Map
# ===============================
st.markdown("---")
st.subheader("5. Evolution of Hydropower Facilities Over Time")
st.markdown("An animated map showing the spatial and temporal development of hydropower facilities worldwide.")

df_anim = df[
    (df['capacity_mw'] >= min_capacity) &
    (df['year'] >= selected_year_range[0]) &
    (df['year'] <= selected_year_range[1])
].dropna(subset=['year', 'plant_lat', 'plant_lon', 'capacity_mw'])

# Ensure year is integer and sorted
df_anim['year'] = df_anim['year'].astype(int)
df_anim = df_anim.sort_values('year')

fig5 = px.scatter_geo(
    df_anim,
    lat='plant_lat',
    lon='plant_lon',
    color='capacity_mw',
    size='capacity_mw',
    animation_frame='year',
    projection='natural earth',
    hover_name='name',
    title='Evolution of Hydropower Facilities Over Time',
    color_continuous_scale='Viridis'
)
fig5.update_layout(**layout_style)
st.plotly_chart(fig5, use_container_width=True)

# ===============================
# 6. Treemap
# ===============================
st.markdown("---")
st.subheader("6. Treemap of Hydropower Capacity")
st.markdown("The treemap illustrates the proportion of hydropower capacity by country and facility.")

fig6 = px.treemap(
    df,
    path=['country', 'name'],
    values='capacity_mw',
    title='Treemap of Hydropower Capacity by Country and Facility'
)
fig6.update_layout(**layout_style)
st.plotly_chart(fig6, use_container_width=True)
