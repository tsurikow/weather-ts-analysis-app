import streamlit as st
import pandas as pd
import time
from multiprocess import Pool
import asyncio
import plotly.graph_objects as go
from utils.city import city_data_processing
from utils.requests import get_temperature
st.set_page_config(
    layout="wide",
    page_title="Weather Analysis App",
    page_icon="🌤"
)
pd.options.mode.chained_assignment = None

st.title('Weather time series app')

# global variables
date_column = 'timestamp'
data_path = 'assets/temperature_data.csv'
api_key = 'fe7023c956d70b4d16831206ceeeacf5' # very bad decision
st.session_state.city_list = []
today = pd.to_datetime('today')
month = today.month
day = today.day

# historical data loader
@st.cache_data
def load_data(data_file):
    loaded_df = pd.read_csv(data_file)
    lowercase = lambda x: str(x).lower()
    loaded_df.rename(lowercase, axis='columns', inplace=True)
    loaded_df[date_column] = pd.to_datetime(loaded_df[date_column])
    loaded_df = loaded_df.set_index(date_column)
    return loaded_df

data_load_state = st.text('Loading data...')
data = load_data(data_path)
data_load_state.success('Data successfully loaded')

uploaded_file = st.file_uploader("Choose a csv file")
if uploaded_file is not None:
    data = load_data(uploaded_file)

st.session_state.city_list = data['city'].value_counts().index.tolist()

#if st.checkbox('Show raw data'):
    #st.subheader('Raw data')
    #st.write(data)




st.subheader('City historical and current temperature analysis')

# worker for multiprocess
@st.cache_data
def worker(city):
    return city_data_processing(data, city, 30)

# main multiprocess func
@st.cache_data
def main():
    #n_worker = 2 # streamlit 2 processes
    cities_data = {}
    cities_trends= {}
    start = time.time()

    with Pool() as pool:
        for result in pool.imap(worker, st.session_state.city_list):
            cities_data[result[2]] = result[0]
            cities_trends[result[2]] = result[1]

    end = time.time()
    multi_pool = end - start
    return multi_pool, cities_data, cities_trends

if __name__ == '__main__':
    if uploaded_file is not None or 'cities_data' not in st.session_state:
        multi_pool, cities_data, cities_trends = main()
        st.session_state.cities_data = cities_data
        st.session_state.cities_trends = cities_trends
        st.success(f'All historical data successfully processed in {"%.1f" %multi_pool} seconds')

# input other API key
api_input = st.text_input("OpenWeather API key", f"{api_key}")

@st.cache_data
def get_current_temperature(cities, api):
    try:
        temp_request = asyncio.run(get_temperature(cities, api))
        temp_dict = {}
        for request in temp_request:
            name = request['name']
            temp = request['main']['temp']
            temp_dict[name] = temp
        return temp_dict
    except Exception as e:
        st.error(e)

if api_input:
    api_key = api_input
    cities_temp = get_current_temperature(st.session_state.city_list, api_key)

city_name = st.selectbox(
    "Select city",
    st.session_state.city_list
)

city_data = st.session_state.cities_data[city_name]
city_trend = st.session_state.cities_trends[city_name]

# seasonal profile for today date
city_same_day = city_data[(city_data.index.month == month) & (city_data.index.day == day)]
city_today_min = city_same_day['min'].mean()
city_today_max = city_same_day['max'].mean()

st.subheader(city_name)

fig = go.Figure(
    [
        go.Scatter(
            x=city_data.index,
            y=city_data['max'],
            fill=None,
            mode="lines",
            opacity=.2,
            name="Max"
        ),
        go.Scatter(
            x=city_data.index,
            y=city_data['min'],
            fill="tonexty",
            mode="lines",
            fillgradient=dict(
                type="vertical",
                colorscale= [[0,'rgba(31,119,180,1)'],[0.5,'rgba(31,119,180,0.5)'], [1,'rgba(31,119,180,0)']]
            ),
            opacity=.2,
            name="Min",
            line_color="lightblue"
        ),
        go.Scatter(
            x=city_data.index,
            y=city_data['temperature'],
            fill=None,
            mode="lines",
            opacity=.7,
            name="Temperature"
        ),
        go.Scatter(
            x=city_data.index,
            y=city_data['anomaly'],
            fill=None,
            mode="markers",
            opacity=.5,
            name="Anomaly"
        )
    ]
)
fig.update_layout(
    height=600,
    xaxis=dict(
        title=dict(
            text="Date"
        )
    ),
    yaxis=dict(
        title=dict(
            text="Temperature"
        )
    ),
    legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01
    )
)
event = st.plotly_chart(fig, key="some", on_select="rerun")

#if st.checkbox('Show temperature data'):
    #st.subheader('City temperature data')
    #st.write(city_data)

#st.write(f"{city_name} long term trend:", city_trend)



if cities_temp is not None:
    #st.write(cities_temp)
    if city_name in cities_temp.keys():
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric(label="Current temperature", value=f"{cities_temp[city_name]} °C", border=True)

        with col2:
            st.metric(label="Season profile min", value=f"{"%.1f" %city_today_min} °C", border=True)

        with col3:
            st.metric(label="Season profile max", value=f"{"%.1f" %city_today_max} °C", border=True)

        with col4:
            if city_today_min < cities_temp[city_name] < city_today_max:
                st.metric(label="Anomaly", value="No", border=True)
            else:
                st.metric(label="Anomaly", value="Yes", border=True)
        with col5:
            if city_trend == 'Decreasing mean temp' or city_trend == 'Probably decreasing mean temp':
                st.metric(label="Long term trend", value="Decreasing", border=True)
            elif city_trend == 'Increasing mean temp' or city_trend == 'Probably increasing mean temp':
                st.metric(label="Long term trend", value="Increasing", border=True)
            else:
                st.metric(label="Long term trend", value="Unknown", border=True)
else:
    st.error(f'{city_name}: unable to get current temperature')