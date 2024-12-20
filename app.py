import streamlit as st
import pandas as pd
import numpy as np
from utils.city import trend_sarimax, city_data_processing


st.title('Weather time series analysis')

DATE_COLUMN = 'timestamp'
DATA_PATH = 'assets/temperature_data.csv'

@st.cache_data
def load_data(data_url):
    data = pd.read_csv(data_url)
    lowercase = lambda x: str(x).lower()
    data.rename(lowercase, axis='columns', inplace=True)
    data[DATE_COLUMN] = pd.to_datetime(data[DATE_COLUMN])
    data = data.set_index(DATE_COLUMN)
    return data

data_load_state = st.text('Loading data...')
data = load_data(DATA_PATH)
data_load_state.text("Done! (using st.cache_data)")

if st.checkbox('Show raw data'):
    st.subheader('Raw data')
    st.write(data)


st.subheader('Group by city')
city_list = data['city'].value_counts().index.tolist()
options = st.multiselect(
    "Select cities",
    city_list
)

st.write("You selected:", options)
