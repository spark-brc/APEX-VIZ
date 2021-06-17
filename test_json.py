import geopandas as gpd
import os
import pyproj
import pandas as pd
import random
import plotly.express as px
import streamlit as st
import json
import xmltodict
from io import StringIO

json_file = st.file_uploader("Provide 'APEXCONT.DAT' file")

# def read_geojson(json_file):
#     xml = json_file.read()
#     file1_data = json.loads(json.dumps(xmltodict.parse(xml)))
#     # grid = json.load(xml)
#     st.write(xml)

def read_geojson(json_file):
    stringio = StringIO(json_file.getvalue().decode("utf-8"))
    f = stringio.read()
    obj = json.loads(f)
    # obj.crs
    st.write(obj["crs"]["properties"]["name"])
    subdf = gpd.GeoDataFrame.from_features(obj["features"])
    subdf = gpd.GeoDataFrame(
        subdf,
        geometry=subdf.geometry,
        crs='EPSG:32613'
        )
    st.dataframe(subdf.columns)
    subdf.to_crs(pyproj.CRS.from_epsg(4326), inplace=True)
    subdf.index = subdf.OBJECTID 
    mfig = px.choropleth_mapbox(subdf,
                    geojson=subdf.geometry,
                    locations=subdf.index,
    #                 color=sel_yr,
                    mapbox_style="open-street-map",
                    zoom=10, center={"lat": 40.807340, "lon": -104.727871},
    #                 range_color=(dfmin, dfmax),
    #                 opacity=0.3,
                    )
    mfig.update_geos(fitbounds="locations", visible=False)
    mfig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=600)
    # st.plotly_chart(mfig, use_container_width=True)
    st.plotly_chart(mfig, use_container_width=True)

# TODO: change to single variable for correlation plot
if __name__ == '__main__':
    if json_file:
        read_geojson(json_file)