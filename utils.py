import glob
import os
import pandas as pd
import streamlit as st
import random
import geopandas as gpd
import pyproj
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
import plotly.offline as offline
import plotly.express as px
import plotly.graph_objects as go
from matplotlib import cm
import numpy as np
from hydroeval import evaluator, nse, rmse, pbias
import base64
import datetime
from io import StringIO

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

    # NOTE: This is later when we are handling model with different time steps
    # # Check IPRINT option
    # if ptcode == 3 or ptcode == 4 or ptcode == 5:  # month
    #     self.dlg.comboBox_SD_timeStep.clear()
    #     self.dlg.comboBox_SD_timeStep.addItems(['Monthly', 'Annual'])
    #     self.dlg.radioButton_month.setChecked(1)
    #     self.dlg.radioButton_month.setEnabled(True)
    #     self.dlg.radioButton_day.setEnabled(False)
    #     self.dlg.radioButton_year.setEnabled(False)
    # elif ptcode == 6 or ptcode == 7 or ptcode == 8 or ptcode == 9:
    #     self.dlg.comboBox_SD_timeStep.clear()
    #     self.dlg.comboBox_SD_timeStep.addItems(['Daily', 'Monthly', 'Annual'])
    #     self.dlg.radioButton_day.setChecked(1)
    #     self.dlg.radioButton_day.setEnabled(True)
    #     self.dlg.radioButton_month.setEnabled(False)
    #     self.dlg.radioButton_year.setEnabled(False)
    # elif ptcode == 0 or ptcode == 1 or ptcode == 2:
    #     self.dlg.comboBox_SD_timeStep.clear()
    #     self.dlg.comboBox_SD_timeStep.addItems(['Annual'])
    #     self.dlg.radioButton_year.setChecked(1)
    #     self.dlg.radioButton_year.setEnabled(True)
    #     self.dlg.radioButton_day.setEnabled(False)
    #     self.dlg.radioButton_month.setEnabled(False)
    return stdate, eddate, start_year, end_year

@st.cache
def get_sims_rchids(sim_file):
    stf_df = pd.read_csv(
                    sim_file,
                    delim_whitespace=True,
                    skiprows=9,
                    usecols=[0, 1, 8],
                    names=['idx', 'rchid', 'sim'],
                    index_col=0)
    stf_df = stf_df.loc["REACH"]
    rchids = stf_df.rchid.unique()
    return stf_df, rchids

@st.cache
def get_obd_obs(obd_file):
    obd_df = pd.read_csv(
                        obd_file,
                        sep=r'\s+', index_col=0, header=0,
                        parse_dates=True, delimiter="\t",
                        na_values=[-999, ""]
                        )
    obsids = obd_df.columns
    return obd_df, obsids


def get_sim(stf_df, rchids, stdate, caldate, eddate):
    tot_sim = pd.DataFrame()
    for i in rchids:
        df2 = stf_df.loc[stf_df['rchid'] == int(i)]
        df2.index = pd.date_range(stdate, periods=len(df2.sim), freq='M')
        df2.rename(columns = {'sim':'sim_{:03d}'.format(int(i))}, inplace = True)
        tot_sim = pd.concat([tot_sim, df2.loc[:, 'sim_{:03d}'.format(int(i))]], axis=1,
            # sort=False
            )
    tot_sim = tot_sim[caldate:eddate]
    return tot_sim



def get_sim_obd2(stf_df, obd_df, rchids2, obsids2, stdate, caldate, eddate):
    obd_df = obd_df[obsids2]

    tot_sim = pd.DataFrame()
    for i in rchids2:
        df2 = stf_df.loc[stf_df['rchid'] == int(i)]
        df2.index = pd.date_range(stdate, periods=len(df2.sim), freq='M')
        df2.rename(columns = {'sim':'sim_{:03d}'.format(int(i))}, inplace = True)
        tot_sim = pd.concat([tot_sim, df2.loc[:, 'sim_{:03d}'.format(int(i))]], axis=1,
            # sort=False
            )
    tot_df = pd.concat([tot_sim, obd_df], axis=1)
    tot_df.index = pd.to_datetime(tot_df.index).normalize()
    tot_df = tot_df[caldate:eddate]
    return tot_df

def get_sim_obd(sim_file, obd_file, obds_list, sims_list, stdate, caldate, eddate):

    df = pd.read_csv(
                    sim_file,
                    delim_whitespace=True,
                    skiprows=9,
                    usecols=[0, 1, 8],
                    names=['idx', 'rchid', 'sim'],
                    index_col=0)
    df = df.loc["REACH"]
    str_obd = pd.read_csv(
                        obd_file,
                        sep=r'\s+', index_col=0, header=0,
                        parse_dates=True, delimiter="\t",
                        na_values=[-999, ""]
                        )
    str_obd = str_obd[obds_list]
    tot_sim = pd.DataFrame()
    for i in sims_list:
        df2 = df.loc[df['rchid'] == int(i)]
        df2.index = pd.date_range(stdate, periods=len(df2.sim), freq='M')
        df2.rename(columns = {'sim':'sim_{:03d}'.format(int(i))}, inplace = True)
        tot_sim = pd.concat([tot_sim, df2.loc[:, 'sim_{:03d}'.format(int(i))]], axis=1,
            # sort=False
            )
    tot_df = pd.concat([tot_sim, str_obd], axis=1)
    tot_df.index = pd.to_datetime(tot_df.index).normalize()
    tot_df = tot_df[caldate:eddate]
    return tot_df


def get_plot(df, sims):
    fig = go.Figure()
    colors = (get_matplotlib_cmap('tab10', bins=8))

    for i in range(len(sims)):
        fig.add_trace(go.Scatter(
            x=df.index, y=df.iloc[:, i], name='Reach {}'.format(sims[i]),
            line=dict(color=colors[i], width=2),
            legendgroup='Reach {}'.format(sims[i])
            ))
    for i in range(len(sims)):
        fig.add_trace(go.Scatter(
            x=df.index, y=df.iloc[:, i+len(sims)], mode='markers', name='Observed {}'.format(sims[i]),
            marker=dict(color=colors[i]),
            legendgroup='Reach {}'.format(sims[i]),
            showlegend=False
            ))
    # line_fig = px.line(df, height=500, width=1200)
    fig.update_layout(
        # showlegend=False,
        plot_bgcolor='white',
        height=600,
        # width=1200
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray', title='')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray', title='Stream Discharge (m<sup>3</sup>/s)')
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
    return fig


def get_sim_plot(df, sims):
    fig = go.Figure()
    colors = (get_matplotlib_cmap('tab10', bins=8))

    for i in range(len(sims)):
        fig.add_trace(go.Scatter(
            x=df.index, y=df.iloc[:, i], name='Reach {}'.format(sims[i]),
            line=dict(color=colors[i], width=2),
            legendgroup='Reach {}'.format(sims[i])
            ))
    # line_fig = px.line(df, height=500, width=1200)
    fig.update_layout(
        # showlegend=False,
        plot_bgcolor='white',
        height=600,
        # width=1200
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray', title='')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray', title='Stream Discharge (m<sup>3</sup>/s)')
    fig.update_layout(legend=dict(
        yanchor="top",
        y=1.0,
        xanchor="center",
        x=0.5,
        orientation="h",
        title='',
    ))
    return fig





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


def get_stats(df):
    df_stat = df.dropna()

    sim = df_stat.iloc[:, 0].to_numpy()
    obd = df_stat.iloc[:, 1].to_numpy()
    df_nse = evaluator(nse, sim, obd)[0]
    df_rmse = evaluator(rmse, sim, obd)[0]
    df_pibas = evaluator(pbias, sim, obd)[0]
    r_squared = (
        ((sum((obd - obd.mean())*(sim-sim.mean())))**2)/
        ((sum((obd - obd.mean())**2)* (sum((sim-sim.mean())**2))))
        )
    return df_nse, df_rmse, df_pibas, r_squared


def get_stats_df(df, sims):
    stats_df = pd.DataFrame()
    for i in range(len(sims)):
        exdf = df.iloc[:, [i, i+len(sims)]]
        df_list = get_stats(exdf)
        stat_series = pd.Series(['{:.3f}'.format(x) for x in df_list], name='Reach {}'.format(sims[i]))
        stats_df = pd.concat([stats_df, stat_series], axis=1)
    stats_df.index = ['NSE', 'RMSE', 'PBIAS', 'R-squared']
    return stats_df


def viz_biomap():

    subdf = gpd.read_file("./resources/subs1.shp")
    subdf.to_crs(pyproj.CRS.from_epsg(4326), inplace=True)
    subdf = subdf[['Subbasin', 'geometry']]
    subdf['geometry'] = subdf['geometry'].convex_hull
    tt = gpd.GeoDataFrame()
    for i in subdf.index:
        df = gpd.GeoDataFrame()
        df['time']= [str(x)[:-9] for x in pd.date_range('1/1/2000', periods=12, freq='M')]
        # df['time'] = [str(x) for x in range(2000, 2012)]
        df['Subbasin'] = 'Sub{:03d}'.format(i+1)
        df['geometry'] = subdf.loc[i, 'geometry']
        df['value'] = [random.randint(0,12) for i in range(12)]
        tt = pd.concat([tt, df], axis=0)   
    tt.index = tt.Subbasin 
    mfig = px.choropleth(tt,
                    geojson=tt.geometry,
                    locations=tt.index,
                    color="value",
                    #    projection="mercator"
                    animation_frame="time",
                    range_color=(0, 12),
                    )
    mfig.update_geos(fitbounds="locations", visible=False)
    mfig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    offline.plot(mfig, auto_open=True, image = 'png', image_filename="map_us_crime_slider" ,image_width=2000, image_height=1000, 
                filename='tt.html', validate=True)

    st.plotly_chart(mfig, use_container_width=True)



def get_variables(wd, rch_file):
    columns = pd.read_csv(
                        os.path.join(wd, rch_file),
                        delim_whitespace=True,
                        skiprows=8,
                        nrows=1,
                        header=None
                        )

    col_lst = columns.iloc[0].tolist()
    col_lst.insert(2, 'YEAR')
    col_dic = dict((i, j) for i, j in enumerate(col_lst))
    keys = [x for x in range(0, 39)]
    col_dic_f = {k: col_dic[k] for k in keys}
    rch_vars = list(col_dic_f.values())
    rch_vars = list(col_dic_f.values())
    return rch_vars



def filedownload(df):
    csv = df.to_csv(index=True)
    b64 = base64.b64encode(csv.encode()).decode()  # strings <-> bytes conversions
    href = f'<a href="data:file/csv;base64,{b64}" download="dataframe.csv">Download CSV File</a>'
    return href


def get_fdcplot(df, sims, yscale):
    fig = go.Figure()
    colors = (get_matplotlib_cmap('tab10', bins=8))
    for i in range(len(sims)):
        sort = np.sort(df.iloc[:, i])[::-1]
        exceedence = np.arange(1.,len(sort)+1) / len(sort)

        fig.add_trace(go.Scatter(
            x=exceedence*100, y=sort, name='Reach {}'.format(sims[i]),
            line=dict(color=colors[i], width=2),
            legendgroup='Reach {}'.format(sims[i])
            ))

    for i in range(len(sims)):
        sort = np.sort(df.iloc[:, i+len(sims)])[::-1]
        exceedence = np.arange(1.,len(sort)+1) / len(sort)
        fig.add_trace(go.Scatter(
            x=exceedence*100, y=sort, mode='markers', name='Observed {}'.format(sims[i]),
            marker=dict(color=colors[i]),
            legendgroup='Reach {}'.format(sims[i]),
            showlegend=False
            ))
    fig.update_layout(
        # showlegend=False,
        plot_bgcolor='white',
        height=700,
        # width=1200
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray', title='Exceedance Probability (%)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray', title='Monthly Average Stream Discharge (m<sup>3</sup>/s)')
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
    if yscale == 'Logarithmic':
        fig.update_yaxes(type="log")
    return fig


def get_sim_fdcplot(df, sims, yscale):
    fig = go.Figure()
    colors = (get_matplotlib_cmap('tab10', bins=8))
    for i in range(len(sims)):
        sort = np.sort(df.iloc[:, i])[::-1]
        exceedence = np.arange(1.,len(sort)+1) / len(sort)
        fig.add_trace(go.Scatter(
            x=exceedence*100, y=sort, name='Reach {}'.format(sims[i]),
            line=dict(color=colors[i], width=2),
            legendgroup='Reach {}'.format(sims[i])
            ))
    fig.update_layout(
        # showlegend=False,
        plot_bgcolor='white',
        height=700,
        # width=1200
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray', title='Exceedance Probability (%)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray', title='Monthly Average Stream Discharge (m<sup>3</sup>/s)')
    fig.update_layout(legend=dict(
        yanchor="top",
        y=1.0,
        xanchor="center",
        x=0.5,
        orientation="h",
        title='',
    ))
    if yscale == 'Logarithmic':
        fig.update_yaxes(type="log")
    return fig