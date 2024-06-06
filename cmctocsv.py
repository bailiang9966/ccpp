import time

import pandas as pd


import requests

class TEST_CMC():
    
  
    def get_coin_data(self,limit=2000,return_list = False):
        '''
        max_supply >= total_supply 最大供应量大于等于当前总量\n
        total_supply = locked_supply + circulating_supply 当前总量=未解锁+流通
        '''
        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"

        headers = {
            "Accepts": "application/json",
            "X-CMC_PRO_API_KEY": "8fb4adae-866f-4a73-8926-9961ee1c0265"
        }

        params = {
            "limit": limit,  # 设置每页返回的最大数量，最多为5000
            "convert": "USD"
        }

        data = requests.get(url, headers=headers, params=params).json()
        coin_data_list =[]
        coin_data = {}
        for coin in data["data"]:

            circulating_supply = coin["circulating_supply"]
            market_cap = coin["quote"]["USD"]["market_cap"]
            total_supply = coin["total_supply"]
            if total_supply == 0:
                continue
            max_supply = coin['max_supply']
            if not max_supply or max_supply == 0:
                max_supply = total_supply
            locked_supply = coin.get("locked_supply", 0)
            

            coin_info = {
                'symbol':coin['symbol'],
                'cmc_rank':coin['cmc_rank'],
                'coin_name':coin['name'],
                'market_cap':market_cap,
                'max_supply':max_supply,
                'total_supply':total_supply,
                'circulating_supply':circulating_supply,
                'locked_supply':locked_supply,
                'released':round((circulating_supply / total_supply) ,2)
            }

            if coin['symbol'] not in coin_data:
                coin_data[coin['symbol']] = coin_info

            coin_data_list.append(coin_info)
        
        return coin_data_list if return_list else coin_data
    


        
    def get_uf_tiker24(self):
        url ='https://fapi.binance.com/fapi/v1/ticker/24hr'
        result = requests.get(url).json()
        data =  [ item['symbol'][:-4] for item in result if item['symbol'].endswith('USDT') and float(item['quoteVolume'])>2500000 ]
        return data

    def get_symbols(self):
        '''
        币安现货和合约都已经上线 且流通75%以上 近期没有超过3%的解锁
        '''
        bn_spot_symbols = self.get_bn_exchange('SPOT')
        bn_uf_symbols = self.get_bn_exchange('UF')

        # vol_filter_list = self.get_uf_tiker24()#根据近1天内交易量过滤交易量过低的 直接用会有被下架的币种
        # bn_symbols = list(set(bn_spot_symbols) & set(bn_uf_symbols)& set(vol_filter_list))

        bn_symbols = list(set(bn_spot_symbols).union(set(bn_uf_symbols)))
        coin_data = self.get_coin_data()
        data_list = []
        for s in reversed(bn_symbols):
            if s  in coin_data:
                data_list.append(coin_data[s])

            else:
                print(f"{s} not in coin_data")
        
        
        df= pd.DataFrame(data_list)

        cols = ['circulating_supply','total_supply','max_supply','locked_supply','market_cap']
        df[cols] = df[cols].astype(str)
        for i,row in df.iterrows():
            for col in cols:
                cell_value = float(row[col])
                if cell_value> 100000000:
                    df.at[i,col] =  "{:.2f}亿".format(cell_value / 100000000)
                elif cell_value> 10000:
                    df.at[i,col] =  "{:.1f}万".format(cell_value / 10000)
        df = df.sort_values(by=['released', 'cmc_rank'], ascending=[False, True])
        df['released'] = df['released'].apply(lambda x: format(x, '.2%'))
        
        new_column_names = {
            'symbol':'币种',
            'coin_name':'全称',
            'cmc_rank':'排序',
            'market_cap':'市值',
            'circulating_supply':'流通',
            
            'total_supply':'当前总供应',
            'max_supply':'最大供应',
            'locked_supply':'未解锁量',
            'released':'解锁量',
        }
        df = df.rename(columns=new_column_names)

        df.to_csv("out/cmc.csv",header=True,index=False)
        pass



    def get_bn_exchange(self,market_type ):
        if market_type == 'SPOT':
            url = 'https://api.binance.com/api/v3/exchangeInfo'
        else:
            url ='https://fapi.binance.com/fapi/v1/exchangeInfo'
        result = requests.get(url).json()
        symbols = result['symbols']
    
        data = []    
        for s in symbols:
            if s['quoteAsset'] == 'USDT' and s['status'] == 'TRADING' and "_" not in s['symbol']:# and s['isSpotTradingAllowed'] == True:
                
                data.append(s['baseAsset'])
        return data

        
if __name__ == '__main__':
    tw =    TEST_CMC()
    tw.get_symbols()

