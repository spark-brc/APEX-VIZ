import json
import logging
import plotly.express as px
from pyproj import crs
import streamlit as st
import os
import pandas as pd
import base64
import numpy as np
import glob
import datetime
import utils
from io import StringIO

pd.options.mode.chained_assignment = None

LINE = """<style>
.vl {
  border-left: 2px solid gray;
  height: 400px;
  position: absolute;
  left: 50%;
  margin-left: -3px;
  top: 0;
}
</style>
<div class="vl"></div>"""

st.set_page_config(
    layout="wide",
    initial_sidebar_state='collapsed',
    page_title='APEX Visualization',
    page_icon='icon2.png' 
    )
st.title('APEX Model - Biomass Analysis')
st.markdown("## User Inputs:")
col1, line, col2 = st.beta_columns([0.4,0.1,0.4])

with col1:
    sim_file = st.file_uploader("Provide *.ACY or AGZ file")
    json_file = st.file_uploader("Provide *.JSON file")
    link_file = st.file_uploader("Provide Sub linkage file")
### 
if sim_file:
    with line:
        st.markdown(LINE, unsafe_allow_html=True)
    file_df, df_vars = utils.get_acy_agz(sim_file)
    with col2:
        sel_var = st.selectbox("Select Output Variable:", df_vars)
    df, dfmin, dfmax, yrmin, yrmax = utils.read_acy(file_df, sel_var)

    with col2:

        tdf01 = st.beta_expander('{} Dataframe from {} output'.format(sel_var, sim_file.name))
        with tdf01:
            st.dataframe(df, height=500)
            st.markdown(utils.filedownload(df), unsafe_allow_html=True)    


if json_file:
    shp_obj =  utils.read_geojson(json_file)
    with col2:
        zoom = st.slider("zoom out/in:", 1, 200, 100)
    # st.write(shp_obj)
if link_file:
    # sub_link = utils.read_subids(link_file)
    # shp_obj = shp_obj.merge(sub_link, on='Past_Name_')
    
    subdf, lon, lat = utils.link_sub_json(shp_obj, link_file, df)
    with col2:
        lon_f = st.slider("Longitude", lon-(abs(lon)*0.01), lon+(abs(lon)*0.01), lon)
        lat_f = st.slider("Latitude", lat-(lat*0.01), lat+(lat*0.01), lat)




def main(dfmin, dfmax, yrmin, yrmax):
    sel_yr = st.slider(
        "Select Time:", int(yrmin), int(yrmax))
    
    utils.viz_biomap(subdf, dfmin, dfmax, sel_yr, zoom, lon_f, lat_f)

    st.write('## Check correlation between variables')
    # st.write(df_vars)
    
    vcol1, vcol2 = st.beta_columns([0.5, 0.5])
    with vcol1:
        v1 = st.selectbox('Select Reach Vars on X-axis:', df_vars)
    with vcol2:
        v2 = st.selectbox('Select Reach Vars on Y-axis:', df_vars)
    st.plotly_chart(utils.get_corr_plot(file_df, v1, v2), use_container_width=True)





if __name__ == '__main__':
    logging.basicConfig(level=logging.CRITICAL)
    # if rchids2 and obsids2 and wnam:
    if sim_file and json_file and link_file:

        main(dfmin, dfmax, yrmin, yrmax)

