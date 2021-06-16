import logging
import plotly.express as px
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
# t, v = st.beta_columns([0.8,0.2])
# with t:
#     st.title('APEX Model - Streamflow Analysis')
# with v:
#     st.markdown('#### 1.1')
st.title('APEX Model - Streamflow Analysis')
st.markdown("## 1. Connect your APEX-CUTE project")
wd = st.text_input("Enter Project Path:")


if wd:
    st.write(wd)

col1, line, col2 = st.beta_columns([0.4,0.1,0.4])

with col1:
    cont_file = st.file_uploader("Provide 'APEXCONT.DAT' file")
    sim_file = st.file_uploader("Provide *.RCH file")
    obd_file = st.file_uploader("Provide 'stf_mon.obd' file")

### 
if cont_file:
    stdate, eddate, start_year, end_year = utils.define_sim_period2(cont_file)
    with line:
        st.markdown(LINE, unsafe_allow_html=True)
    with col2:
        stdate = st.date_input(
            "Simulation Start Day",
            stdate
            )
        val_range = st.slider(
            "Set Analysis Period:",
            min_value=int(start_year),
            max_value=int(end_year), value=(int(start_year),int(end_year)))
    caldate = datetime.datetime(val_range[0], 1, 1)
    eddate = datetime.datetime(val_range[1], 12, 31)
###
wnam = None
rchids2 = None
obsids = []
if sim_file:
    stf_df, rchids = utils.get_sims_rchids(sim_file)
    with col2:
        rchids2 = st.multiselect('Select Reach IDs:', rchids)
    if (rchids2 is not None) and (obd_file is None):
        with col2:
            obsids2 = st.multiselect('Select Observation Column Names:', obsids)
            wnam = st.text_input('Enter Watershed Name:')
    elif rchids2 and obd_file:
        obd_df, obsids = utils.get_obd_obs(obd_file)
        with col2:
            obsids2 = st.multiselect('Select Observation Column Names:', obsids)
            wnam = st.text_input('Enter Watershed Name:')



def main(df, sims_list):

    with st.beta_expander('{} Dataframe for Simulated and Observed Stream Discharge'.format(wnam)):
        st.dataframe(df, height=500)
        st.markdown(utils.filedownload(df), unsafe_allow_html=True)

    if obd_file:
        stats_df = utils.get_stats_df(df, sims_list)
        with col2:
            st.markdown(
                """
                ### Objective Functions
                """)
            st.dataframe(stats_df.T)
        st.markdown("## Hydrographs for stream discharge")
        st.plotly_chart(utils.get_plot(df, sims_list), use_container_width=True)
        tcol1, tcol2 = st.beta_columns([0.55, 0.45])
        with tcol1:
            st.markdown("## Flow Duration Curve")
        pcol1, pcol2= st.beta_columns([0.1, 0.9])
        with pcol1:
            yscale = st.radio("Select Y-axis scale", ["Linear", "Logarithmic"])
        with pcol2:
            st.plotly_chart(utils.get_fdcplot(df, sims_list, yscale), use_container_width=True)
    elif obd_file is None:
        st.markdown("## Hydrographs for stream discharge")
        st.plotly_chart(utils.get_sim_plot(df, sims_list), use_container_width=True)
        tcol1, tcol2 = st.beta_columns([0.55, 0.45])
        with tcol1:
            st.markdown("## Flow Duration Curve")
        pcol1, pcol2= st.beta_columns([0.1, 0.9])
        with pcol1:
            yscale = st.radio("Select Y-axis scale", ["Linear", "Logarithmic"])
        with pcol2:
            st.plotly_chart(utils.get_sim_fdcplot(df, sims_list, yscale), use_container_width=True)



@st.cache
def load_data():
    if obd_file is None:
        df = utils.get_sim(stf_df, rchids2, stdate, caldate, eddate)
    elif obd_file:
        df = utils.get_sim_obd2(stf_df, obd_df, rchids2, obsids2, stdate, caldate, eddate)
    return df, rchids2


if __name__ == '__main__':
    logging.basicConfig(level=logging.CRITICAL)
    # if rchids2 and obsids2 and wnam:
    if wnam and rchids2:
        df, sims_list = load_data()
        main(df, sims_list)
