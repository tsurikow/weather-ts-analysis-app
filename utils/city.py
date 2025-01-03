import statsmodels.api as sm
import pandas as pd
import numpy as np

def trend_sarimax(data, city, steps=12):
    # SARIMAX для прогноза долгосрочного тренда
    city_ts = data[data['city'] == city]['temperature']
    city_ts_M = pd.DataFrame(city_ts.resample('ME').mean())
    city_M_sarimax = sm.tsa.SARIMAX(endog=city_ts_M, order=[1,1,0], seasonal_order=[1,1,1,12], simple_differencing=True).fit(maxiter=200, method='bfgs', disp=False)
    forecast = city_M_sarimax.forecast(steps=steps)
    city_ts_final = pd.DataFrame(city_ts_M).merge(
        pd.DataFrame(forecast).rename(columns = {'predicted_mean':'forecast'}),
        how = 'outer', left_index = True, right_index = True)
    future_mean = city_ts_final['forecast'].iloc[-steps:].mean()
    past_mean = city_ts_final['temperature'].iloc[-steps*2:-steps].mean()
    future_last_mean = city_ts_final['forecast'].iloc[-12:].mean()
    trend = 'Unknown'
    if past_mean > future_mean > future_last_mean:
        trend = 'Decreasing mean temp'
    elif past_mean < future_mean < future_last_mean:
        trend = 'Increasing mean temp'
    elif future_mean < future_last_mean:
        trend = 'Probably increasing mean temp'
    elif future_mean > future_last_mean:
        trend = 'Probably decreasing mean temp'
    return trend

def city_data_processing(data, city, window=30, steps=36):
    city_data = data[data['city'] == city]
    city_data['smoothed'] = np.convolve(city_data['temperature'], np.ones(window)/window, 'same')
    city_data['season_mean'] = city_data.groupby(['season'])['temperature'].transform('mean')
    city_data['std'] = city_data.groupby(['season'])['temperature'].transform('std')
    city_data['max'] = city_data['smoothed'] + 2*city_data['std']
    city_data['min'] = city_data['smoothed'] - 2*city_data['std']
    city_data['anomaly'] = np.where(
        (city_data['temperature'] < city_data['max'])
        & (city_data['temperature'] > city_data['min']),
        np.nan,
        city_data['temperature'])
    trend = trend_sarimax(data, city, steps)

    return city_data, trend, city