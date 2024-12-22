from multiprocess import Pool
import time
from utils.city import *
pd.options.mode.chained_assignment = None

DATE_COLUMN = 'timestamp'
DATA_PATH = '../assets/temperature_data.csv'

def load_data(data_path):
    data = pd.read_csv(data_path)
    lowercase = lambda x: str(x).lower()
    data.rename(lowercase, axis='columns', inplace=True)
    data[DATE_COLUMN] = pd.to_datetime(data[DATE_COLUMN])
    data = data.set_index(DATE_COLUMN)
    return data

data = load_data(DATA_PATH)

city_list = data['city'].value_counts().index.tolist()

def qualityMAPE(x,y):
    qlt = ((x-y).abs()/x.abs()).replace([np.inf, -np.inf], np.nan)
    return qlt.mean() , qlt


data_list = []
def worker(city):
    return city_data_processing(data, city, 30)

def main():
    #n_worker = 4
    data_list_P = []

    start = time.time()
    with Pool() as pool:
        for result in pool.imap(worker, city_list):
            data_list_P.append(result[0])
            #print(f'{result[2]} long term trend: ', result[1])
        #result = pool.map_async(worker, city_list)
        #for value in result.get():
            #data_list_P.append(value[0])
            #print(f'{value[2]} long term trend: ', value[1])

    end = time.time()
    multi_pool = end - start
    return multi_pool

if __name__ == '__main__':
    multi_pool = main()
    data_list = []
    start = time.time()
    for city in city_list:
        results = city_data_processing(data, city, window=30)
        data_list.append(results[0])
        print(f'{results[2]} longterm trend: ', results[1])
    processed_data = pd.concat(data_list)
    end = time.time()
    single_proc = end - start
    print("_"*20)
    print(f'multiprocessing: {"%.2f" %multi_pool}s')
    print(f'single: {"%.2f" %single_proc}s')
    if single_proc > multi_pool:
        print(f'Multi {"%.1f" % (single_proc/multi_pool)}x times faster')
    else:
        print(f'Single {"%.1f" %(multi_pool/single_proc)}x times faster')