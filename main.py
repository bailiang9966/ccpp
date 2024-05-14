import yaml
import requests
import concurrent.futures
import time
import os
import pandas as pd


import socket

class HAHA():
    url_timeout = 2
    real_timeout = 2
    thread_max = 80
    blacklist_file = 'out/bl.txt'
    final_csv = 'out/final.csv'
    test_urls = [{
        'id':'binance',
        'url':"https://www.binance.com/api/v3/ping"
    },{
        'id':'upbit',
        'url':"https://upbit.com/robots.txt"
    },{
        'id':'okx',
        'url':"https://www.okx.com/api/v5/public/time"
    }]
    def __init__(self) :
        '''
        black_list只保存主机
        final_df 协议/主机/端口/可用性
        temp_df 协议/主机/端口
        '''
        self.black_list = self.get_blacklist()
        self.final_df = self.get_final_df()
        self.temp_df = []

    def get_blacklist(self):
        data_list = []
        
        if os.path.exists(self.blacklist_file):
            with open(self.blacklist_file, 'r') as file:
                for line in file:
                    data_list.append(line.strip())
            return data_list
        else:
            return []
    
    def get_final_df(self):
        if os.path.exists(self.final_csv):
            df = pd.read_csv(self.final_csv,header=0)
        else:
            column_names = ['protocol','host','port']
            for item in self.test_urls:
                column_names.append(item['id'])
            df = pd.DataFrame(columns = column_names)
        return df
    
    def read_yaml(self,yaml_file ):
        with open(yaml_file, 'r', encoding='utf-8') as file:
            yaml_cfg = yaml.safe_load(file)
        return yaml_cfg   
     
    def  get_all_proxy(self):

        proxy_source =self.read_yaml('proxy.yaml')
        
        df_all = []
        for proxy_cfg in proxy_source:
            df = pd.DataFrame()
            proxy_types = proxy_cfg['types'].split(',')
            for proxy_type in proxy_types:
                url = f"{proxy_cfg['main_url']}{proxy_type}.txt"
                print(url)
                try:
                    response = requests.get(url)
                    if response.status_code!=200:
                        print(f"{url} error ")

                    result = response.text.split('\n')
                    if result[-1] =='':
                        result.pop()
                    df =  pd.Series(result)
                    df = df.str.split(':', expand=True)
                    df.columns = ['host', 'port']
                    df['port'] = df['port'].astype(int)
                    df['protocol'] = proxy_type
                    df_all.append(df)
                    print(f"数据共:{len(df)}")
                except requests.exceptions.RequestException as e:
                    print(e)
        
        self.temp_df = pd.concat(df_all)
        self.temp_df = pd.merge(self.temp_df, self.final_df[['protocol', 'host', 'port']], on=['protocol', 'host', 'port'], how='left')

        self.temp_df.drop_duplicates(subset=['host', 'port'], inplace=True)

        print(f"总计:{len(self.temp_df)}条数据")
    def test_host(self,host, port):
        test_result =False
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.08)
            result = sock.connect_ex((host, port))
            if result == 0:
                test_result= True
        except Exception as e:
            print(f"{host}连接错误: {e}")
            pass
        finally:
            sock.close()
        return test_result
    def run(self):
        start = time.time()
        #获取所有地址最新代理列表
        self.get_all_proxy()

        #对代理进行测试
        self.proxy_filter()
        #写blacklist
        self.overwrite_file(self.blacklist_file,self.black_list)
        #写入可用的csv
        self.final_df.to_csv(self.final_csv,index=False,header=True)
        
        end = time.time()
        print(f'耗时总计：{end-start}秒')
    
    def proxy_filter(self):
        '''
        线程池去测试代理是否可用
        '''
        
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.thread_max)  
        # index = 0
        for row in self.temp_df.itertuples():
            executor.submit(self.test_proxy, row.protocol,row.host,row.port)
            # self.test_proxy( row.protocol,row.host,row.port)
            # index+=1
            # print(f"index{index}")
            # if index >100:
                
            #     break


    def overwrite_file(self,file_path, content):
        with open(file_path, 'w') as file:
            if isinstance(content, str):
                # 如果传入的是字符串，则将字符串写入文件
                file.write(content)
            elif isinstance(content, list):
                # 如果传入的是列表，则按行写入列表内容
                for line in content:
                    file.write(line + '\n')

    def test_proxy(self,protocol,host,port):
        '''
        主机连接失败直接放到blacklist
        test_urls全部超时也放到blacklist
        '''
        p = f"{protocol}://{host}:{port}"
        proxies = {
            'https': p,
            'http': p,
        }

        #如果主机连接失败 直接放到black_list

        if not self.test_host(host,port):
            self.black_list.append(host)
            return
        proxy_delays =[]
        proxy_final = [protocol,host,port]
        for test_url in self.test_urls:
        
            try:
                start = time.time()
                response = requests.get(test_url['url'],proxies=proxies, timeout=2)
                if response.status_code == 200:
                    end = time.time()
                    ts = end-start
                    proxy_delays.append(ts)
                    if ts<self.real_timeout:
                        print(f"代理 {p} 延迟:{ts} url:{test_url}")
                        
                        # return proxy
            except requests.exceptions.RequestException as e:
                proxy_delays.append(999)
        #延迟小于2的放入final_df
        if any(num < 1.5 for num in proxy_delays):
            proxy_final.extend(proxy_delays)
            self.final_df.loc[len(self.final_df)] = proxy_final
        #延迟全大于3的放入black_list
        elif not any(num < 3 for num in proxy_delays):
            self.black_list.append(host)




    
if __name__ == '__main__':
    hh = HAHA()
    hh.run()
