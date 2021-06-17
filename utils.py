import glob
import os
import pandas as pd
import streamlit as st
import random
import geopandas as gpd
import pyproj
import plotly.offline as offline
import plotly.express as px
import plotly.graph_objects as go
from matplotlib import cm
import numpy as np
import base64
import datetime
from io import StringIO
import json

def define_sim_period2(cont_file):

    stringio = StringIO(cont_file.getvalue().decode("utf-8"))
    f = stringio.read().splitlines()

    # with open(cont_file, 'r') as f:
    data = [x.strip().split() for x in f if x.strip()]
    numyr = int(data[0][0])
    styr = int(data[0][1])
    stmon = int(data[0][2])
    stday = int(data[0][3])
    ptcode = int(data[0][4])
    edyr = styr + numyr -1
    stdate = datetime.datetime(styr, stmon, 1) + datetime.timedelta(stday - 1)
    eddate = datetime.datetime(edyr, 12, 31) 
    duration = (eddate - stdate).days

    ##### 
    start_month = stdate.strftime("%b")
    start_day = stdate.strftime("%d")
    start_year = stdate.strftime("%Y")
    end_month = eddate.strftime("%b")
    end_day = eddate.strftime("%d")
    end_year = eddate.strftime("%Y")

    return stdate, eddate, start_year, end_year



# def get_subnums(wd, rch_file)
def get_matplotlib_cmap(cmap_name, bins, alpha=1):
    if bins is None:
        bins = 10
    cmap = cm.get_cmap(cmap_name)
    h = 1.0 / bins
    contour_colour_list = []

    for k in range(bins):
        C = list(map(np.uint8, np.array(cmap(k * h)[:3]) * 255))
        contour_colour_list.append('rgba' + str((C[0], C[1], C[2], alpha)))

    C = list(map(np.uint8, np.array(cmap(bins * h)[:3]) * 255))
    contour_colour_list.append('rgba' + str((C[0], C[1], C[2], alpha)))
    return contour_colour_list


def read_subids(link_file):
    sub_link = pd.read_csv(link_file, sep='\s+')
    sub_link.rename({'pasture_name': 'Past_Name_'}, axis=1, inplace=True)
    return sub_link

@st.cache
def read_geojson(json_file):
    stringio = StringIO(json_file.getvalue().decode("utf-8"))
    f = stringio.read()
    obj = json.loads(f)
    # obj.crs
    crs_info = obj["crs"]["properties"]["name"].split(':')[-1]
    subdf = gpd.GeoDataFrame.from_features(obj["features"])
    shp_obj = gpd.GeoDataFrame(
        subdf,
        geometry=subdf.geometry,
        crs='EPSG:{}'.format(crs_info)
        )
    return shp_obj

@st.cache
def link_sub_json(shp_obj, link_file, df):
    sub_link = read_subids(link_file)
    subdf = shp_obj.merge(sub_link, on='Past_Name_')
    # subdf = subdf.merge(df, on='sub_ids')
    subdf = subdf.merge(df, on='sub_ids')
    subdf.to_crs(pyproj.CRS.from_epsg(4326), inplace=True)
    subdf.index = subdf.sub_ids 
    lon = subdf.centroid.iloc[0].x
    lat = subdf.centroid.iloc[0].y

    return subdf, lon, lat



def viz_biomap(subdf, dfmin, dfmax, sel_yr, zoom, lon_f, lat_f):
    
    # subdf = shp_obj.merge(dff, on='sub_ids')

    # subdf.to_crs(pyproj.CRS.from_epsg(4326), inplace=True)
    # subdf.index = subdf.sub_ids 
    # st.write(subdf.centroid.iloc[0].x)
    # st.write(subdf.centroid.iloc[0].y)
    mfig = px.choropleth_mapbox(subdf,
                    geojson=subdf.geometry,
                    locations=subdf.index,
                    color=sel_yr,
                    mapbox_style="open-street-map",
                    zoom=0.1*zoom, center = {"lon": lon_f, "lat": lat_f},
                    range_color=(dfmin, dfmax),
                    opacity=0.3,
                    )
    mfig.update_geos(fitbounds="locations", visible=False)
    mfig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=600)
    st.plotly_chart(mfig, use_container_width=True)


def filedownload(df):
    csv = df.to_csv(index=True)
    b64 = base64.b64encode(csv.encode()).decode()  # strings <-> bytes conversions
    href = f'<a href="data:file/csv;base64,{b64}" download="dataframe.csv">Download CSV File</a>'
    return href



def get_acy_agz(sim_file):
    df = pd.read_csv(
                sim_file,
                delim_whitespace=True,
                skiprows=8,
                header=0,
                )
    df_vars = df.columns[5:]
    return df, df_vars

@st.cache
def read_acy(df, var):
    acy_df = df.loc[:, ['SA#', 'YR', var]]
    subids = acy_df['SA#'].unique()
    dff = pd.DataFrame()
    for i in subids:
        sacy_df = acy_df.loc[acy_df['SA#'] == i]
        sacy_df = sacy_df.groupby('YR').sum()
        sacy_df.drop('SA#', axis=1, inplace=True)
        sacy_df.rename({var: i}, axis=1, inplace=True)
        # sacy_df.index = sacy_df['YR']
        dff = pd.concat([dff, sacy_df], axis=1)
    dff = dff.T
    dff.index.name = 'sub_ids'
    dfmin = dff.min().min()
    dfmax = dff.max().max()
    yrmin = dff.columns.min()
    yrmax = dff.columns.max()
    return dff, dfmin, dfmax, yrmin, yrmax


def get_corr_plot(df, v1s, v2s):
    fig = go.Figure()
    colors = (get_matplotlib_cmap('tab10', bins=8))
    # for i, j, k in zip(v1s, v2s, range(len(v1s))):
    v1_df = df.loc[:, v1s]
    v2_df = df.loc[:, v2s]
    fig.add_trace(go.Scatter(
        x=v1_df, y=v2_df, name='Reach {}'.format(v1s),
        mode='markers',
        marker=dict(color=colors[0]),
        # legendgroup='Reach {}'.format(i)
        ))
    fig.update_layout(
        # showlegend=False,
        plot_bgcolor='white',
        height=700,
        # width=1200
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray', title='{} on X-axis'.format(v1s))
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray', title='{} on Y-axis'.format(v2s))
    fig.update_layout(legend=dict(
        yanchor="top",
        y=1.0,
        xanchor="center",
        x=0.5,
        orientation="h",
        title='',
    ))
    fig.update_traces(marker=dict(size=10, opacity=0.5,
                                line=dict(width=1,
                                            color='white')
                                            ),
                    selector=dict(mode='markers'))    


    # if yscale == 'Logarithmic':
    #     fig.update_yaxes(type="log")
    return fig