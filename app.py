import dash
from dash import dcc, html
import plotly.express as px
import pandas as pd
import geopandas as gpd
import folium
from dash.dependencies import Input, Output

# Load datasets
file_path = "data/treecover_loss__ha.csv"
df = pd.read_csv(file_path)

# Load world map shapefile
shapefile_path = "data/ne_110m_admin_0_countries.shp"
world = gpd.read_file(shapefile_path)

# Merge deforestation data with world shapefile using ISO country codes
merged_data = world.merge(df, how="left", left_on="SOV_A3", right_on="iso")

# Initialize Dash app
app = dash.Dash(__name__)

# App layout
app.layout = html.Div([
    html.H1("Global Deforestation Analysis", style={'textAlign': 'center'}),

    dcc.Graph(id="deforestation-bar-chart"),
    dcc.Graph(id="deforestation-line-chart"),
    dcc.Graph(id="co2-deforestation-scatter"),

    html.Div([
        html.Label("Select Year:"),
        dcc.Slider(
            id="year-slider",
            min=df["umd_tree_cover_loss__year"].min(),
            max=df["umd_tree_cover_loss__year"].max(),
            value=df["umd_tree_cover_loss__year"].min(),
            marks={str(year): str(year) for year in df["umd_tree_cover_loss__year"].unique()},
            step=None
        ),
    ], style={'width': '80%', 'margin': 'auto'}),

    html.Div(id="map", children=[]),
])

# Callback to update graphs
@app.callback(
    [Output("deforestation-bar-chart", "figure"),
     Output("deforestation-line-chart", "figure"),
     Output("co2-deforestation-scatter", "figure"),
     Output("map", "children")],
    [Input("year-slider", "value")]
)
def update_graphs(selected_year):
    filtered_df = df[df["umd_tree_cover_loss__year"] == selected_year]

    # Bar chart: Deforestation by country
    fig1 = px.bar(
        filtered_df,
        x="iso",  # Use country ISO codes
        y="umd_tree_cover_loss__ha",
        title=f"Deforestation in {selected_year}",
        labels={"umd_tree_cover_loss__ha": "Tree Cover Loss (ha)", "iso": "Country"}
    )

    # Line chart: Deforestation trends over years
    fig2 = px.line(
        df,
        x="umd_tree_cover_loss__year",
        y="umd_tree_cover_loss__ha",
        title="Deforestation Trends Over Time",
        labels={"umd_tree_cover_loss__year": "Year", "umd_tree_cover_loss__ha": "Tree Cover Loss (ha)"},
        color="iso"
    )

    # Scatter plot: CO2 emissions vs. deforestation
    fig3 = px.scatter(
        filtered_df,
        x="umd_tree_cover_loss__ha",
        y="gfw_gross_emissions_co2e_all_gases__Mg",
        title="CO2 Emissions vs. Tree Cover Loss",
        labels={"umd_tree_cover_loss__ha": "Tree Cover Loss (ha)", "gfw_gross_emissions_co2e_all_gases__Mg": "CO2 Emissions (Mg)"},
        color="iso"
    )

    # Generate folium map
    deforestation_map = folium.Map(location=[0, 0], zoom_start=2)
    for _, row in merged_data.iterrows():
        if not pd.isna(row["umd_tree_cover_loss__ha"]):
            folium.CircleMarker(
                location=[row["geometry"].centroid.y, row["geometry"].centroid.x],
                radius=row["umd_tree_cover_loss__ha"] / 1000000,  # Scale the radius
                color="red",
                fill=True,
                fill_color="red",
                fill_opacity=0.5,
                popup=f"{row['SOVEREIGNT']}: {row['umd_tree_cover_loss__ha']} ha lost"
            ).add_to(deforestation_map)

    return fig1, fig2, fig3, [html.Iframe(srcDoc=deforestation_map._repr_html_(), width="100%", height="500px")]

# Run app
if __name__ == "__main__":
    app.run_server(debug=True)
