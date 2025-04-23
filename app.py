from flask import Flask, render_template
import pandas as pd
import plotly.express as px
import plotly.io as pio
from io import StringIO

app = Flask(__name__)

@app.route('/')
def index():
    # Simulated CSV content
    mock_csv = StringIO("""country,year,capacity_mw,plant_lat,plant_lon
China,2005,1200,35.8617,104.1954
Brazil,2010,850,14.2350,-51.9253
Canada,1995,500,56.1304,-106.3468
Norway,2000,300,60.4720,8.4689
India,2015,950,20.5937,78.9629
USA,1980,1300,37.0902,-95.7129
""")

    # Read mock data into DataFrame
    df = pd.read_csv("https://raw.githubusercontent.com/wailywang/info301-dash-dashboard/refs/heads/main/GloHydroRes_vs1.csv")
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
