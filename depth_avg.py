from concurrent.futures import ALL_COMPLETED, ThreadPoolExecutor,wait
import datetime
import json
import os
import random
import requests
import pandas as pd


# 从币安API获取深度信息
#每小时从币安获取深度信息快照，取30-98位的均值，再取多个小时的均值，作为深度的均值
class ORDER_DATA_GATHER():
    def __init__(self) -> None:

        self.symbols =  self.get_symbols().keys()
        # self.symbols =  ['BTC','ETH','TON']
        self.csv_dir = 'out'
        self.executor = ThreadPoolExecutor(max_workers=100)
        self.use_proxy = True
        pass
    def get_proxy_data(self):
        url = 'https://raw.githubusercontent.com/bailiang9966/ccpp/main/out/output.json'
        response = requests.get(url)
        data = json.loads(response.text)
        # result = data['bn_uf']+data['bn_spot']
        # result= list(set(result))
        return data

    def get_symbols(self):
        url = 'https://raw.githubusercontent.com/bailiang9966/wtf_work/main/out/data.json'
        data = requests.get(url).json()
        # data =  json.loads(response.text)
        return data
    
    def get_depth_avg(self,symbol ,market_type  ):
        if market_type == 'spot':
            depth_url = f'https://fapi.binance.com/fapi/v1/depth?symbol={symbol}USDT&limit=500'
        else:
            depth_url = f'https://api3.binance.com/api/v3/depth?symbol={symbol}USDT&limit=500'
        if self.use_proxy:
            # proxy = next(self.proxy_cycle)
            proxy_list = self.proxy_datas['bn_'+market_type]
            proxy = random.choice(proxy_list)
            proxies={
                'https':proxy,
                'http':proxy,
            }
            data =    requests.get(depth_url,proxies=proxies).json()
        else:
            data = requests.get(depth_url).json()
 
        # 将深度信息转换为DataFrame
        columns = ['price', 'quantity']
        bids = pd.DataFrame(data['bids'], columns=columns)
        asks = pd.DataFrame(data['asks'], columns=columns)

        # 计算买单和卖单的金额

        df = pd.concat([asks, bids])
        df[columns] = df[columns].astype(float)
        df_sorted = df.sort_values('quantity')
        num_rows = len(df_sorted)

        # 计算 50% 和 99% 位置的索引
        start_index = int(num_rows * 0.5)
        end_index = int(num_rows * 0.99)
        subset_df = df_sorted.iloc[start_index:end_index]
        average = subset_df['quantity'].mean()
        
        return average

    def update_row(self,symbol,col_name):
        depth_avg = self.get_depth_avg(symbol,'spot')
        self.spot_df.loc[self.spot_df['symbol'] == symbol, col_name] = depth_avg

        depth_avg = self.get_depth_avg(symbol,'uf')
        self.uf_df.loc[self.uf_df['symbol'] == symbol, col_name] = depth_avg

    def run(self):
        self.proxy_datas = self.get_proxy_data()
        # proxy_list = self.get_proxy_data()
        # print(f"可用代理:{len(proxy_list)}个")
        # self.proxy_cycle = cycle(proxy_list)
        now = datetime.datetime.now()
        fmthr = 'd_'+now.strftime("%m%d%H")
        if os.path.exists(self.csv_dir+'/spot.csv'):
            
            self.spot_df = pd.read_csv(self.csv_dir+'/spot.csv',header=0)
            self.uf_df = pd.read_csv(self.csv_dir+'/uf.csv',header=0)
            self.spot_df = self.spot_df[self.spot_df['symbol'].isin(self.symbols)]
            self.uf_df = self.uf_df[self.uf_df['symbol'].isin(self.symbols)]

            # 获取不在 df 中的 symbols
            add_symbols = [s for s in self.symbols if s not in self.spot_df['symbol'].values]
            if len(add_symbols)>0:
                self.spot_df = pd.concat([self.spot_df, add_symbols], ignore_index=True)
                self.uf_df = pd.concat([self.uf_df, add_symbols], ignore_index=True)


        else:
            self.spot_df = pd.DataFrame(data=self.symbols,columns=['symbol'])
            self.uf_df = pd.DataFrame(data=self.symbols,columns=['symbol'])

        self.spot_df[fmthr]=None
        self.uf_df[fmthr]=None
        

        futures = [self.executor.submit(self.update_row,s,fmthr) for s in self.symbols]
        wait(futures, return_when=ALL_COMPLETED)
           

        col_count = len(self.spot_df.columns)
        if col_count > 11:
            self.spot_df = self.spot_df.drop(self.spot_df.columns[1], axis=1)
            self.uf_df = self.uf_df.drop(self.uf_df.columns[1], axis=1)
        self.spot_df.to_csv(self.csv_dir+'/spot.csv',header=True,index=False)
        self.uf_df.to_csv(self.csv_dir+'/uf.csv',header=True,index=False)
        


if __name__ == '__main__':
    odg = ORDER_DATA_GATHER()
    odg.run()
