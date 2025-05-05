import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import pycountry
import streamlit as st

st.set_page_config(layout="wide", page_title="Hydropower Dashboard")
st.title("Hydropower Visualization Dashboard")

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

layout_style = dict(
    template='plotly_white',
    font=dict(family="Arial", size=14),
    title_font_size=20,
)

# ===============================
# 1. Choropleth Map
# ===============================
st.subheader("1. Total Hydropower Capacity by Country")
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
st.subheader("2. Hydropower Plants by Reservoir Volume")
df_bubble = df.dropna(subset=['res_vol_mcm'])
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
st.subheader("3. Capacity Distribution by Country and Plant")
sun = df.groupby(['country', 'name'], as_index=False)['capacity_mw'].sum()
fig3 = px.sunburst(
    sun,
    path=['country','name'],
    values='capacity_mw',
    title='Sunburst Chart of Hydropower Capacity'
)
fig3.update_layout(**layout_style)
st.plotly_chart(fig3, use_container_width=True)

# ===============================
# 4. Time Series
# ===============================
st.subheader("4. Installed Capacity by Country Over Time")
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
st.subheader("5. Evolution of Hydropower Facilities Over Time")
fig5 = px.scatter_geo(
    df,
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
st.subheader("6. Treemap of Hydropower Capacity")
fig6 = px.treemap(
    df,
    path=['country', 'name'],
    values='capacity_mw',
    title='Treemap of Hydropower Capacity by Country and Facility'
)
fig6.update_layout(**layout_style)
st.plotly_chart(fig6, use_container_width=True)
