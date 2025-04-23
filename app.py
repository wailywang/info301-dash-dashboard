from flask import Flask, render_template
import pandas as pd
import plotly.express as px
import plotly.io as pio
import os

app = Flask(__name__)

@app.route('/')
def index():
    # Load and preprocess data
    df = pd.read_csv('GloHydroRes_vs1.csv')
    df = df.assign(
        year=lambda d: pd.to_numeric(d['year'], errors='coerce'),
        capacity_mw=lambda d: pd.to_numeric(d['capacity_mw'], errors='coerce'),
        lat=lambda d: pd.to_numeric(d['plant_lat'], errors='coerce'),
        lon=lambda d: pd.to_numeric(d['plant_lon'], errors='coerce')
    ).dropna(subset=['country','year','capacity_mw','lat','lon'])

    # Create plotly mapbox figure
    fig = px.scatter_mapbox(
        df, lat='lat', lon='lon',
        size='capacity_mw', color='capacity_mw',
        color_continuous_scale='Viridis',
        size_max=15, zoom=1,
        mapbox_style='carto-positron',
        title='Hydropower Facilities by Location and Capacity',
        labels={'capacity_mw':'Capacity (MW)'}
    )

    # Generate HTML for the figure
    graph_html = pio.to_html(fig, full_html=False)
    return render_template('index.html', plot=graph_html)

if __name__ == '__main__':
    app.run(debug=True)
