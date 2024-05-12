import yaml
import requests
import concurrent.futures
import time
import random
import os  

url_timeout = os.environ.get('url_timeout', 2)
real_timeout = os.environ.get('real_timeout', 2)
thread_max = os.environ.get('thread_max', 50)

test_urls = ["https://www.google.com",
            "https://github.com",
            "https://stackoverflow.com",
            "https://www.python.org",
            "https://www.djangoproject.com",
            "https://pypi.org",
            "https://www.kaggle.com",
            "https://medium.com",
            "https://www.linkedin.com",
            "https://www.youtube.com",
            "https://www.amazon.com",
            "https://www.facebook.com",
            "https://www.twitter.com",
            "https://www.instagram.com",
            "https://www.netflix.com",
            "https://www.reddit.com",
            "https://www.quora.com",
            "https://www.udemy.com",
            "https://www.coursera.org",
            "https://www.wikipedia.org",
            "https://www.nytimes.com",
            "https://www.bbc.co.uk",
            "https://www.ebay.com",
            "https://www.oracle.com",
            "https://www.ibm.com",
            "https://www.microsoft.com",
            "https://www.apple.com",
            "https://www.adobe.com",
            "https://www.spotify.com",
            "https://www.twitch.tv",]

def read_yaml(yaml_file ):
    with open(yaml_file, 'r', encoding='utf-8') as file:
        yaml_cfg = yaml.safe_load(file)
    return yaml_cfg

def get_all_proxy():
    proxy_source =read_yaml('proxy.yaml')
    all_proxy_list = []
    unique_hosts = set()
    for proxy_cfg in proxy_source:
        proxy_types = proxy_cfg['types'].split(',')
        for proxy_type in proxy_types:
            url = f"{proxy_cfg['main_url']}{proxy_type}.txt"
            try:
                response = requests.get(url)
                if response.status_code!=200:
                    print(f"{url} error ")
                result = response.text.split('\n')
                for item in result:
                    host = item.split(":")[0]
                    if host not in unique_hosts:
                        unique_hosts.add(host)
                        all_proxy_list.append(f"{proxy_type}://{item}")
            except requests.exceptions.RequestException as e:
                print(e)

    print(f"总计:{len(all_proxy_list)}")
    return all_proxy_list



def proxy_filter(proxy):
    proxies = {
        'https': proxy,
        'http': proxy
    }
    url= random.choice(test_urls)
    try:
        start = time.time()
        response = requests.get(url,proxies=proxies, timeout=url_timeout)
        if response.status_code == 200:
            end = time.time()
            ts = end-start
            if ts<real_timeout:
                print(f"代理 {proxy} 延迟:{ts}")
                return proxy
    except requests.exceptions.RequestException as e:
        return None
def write_to_file(data_list, file_name):
    try:
        with open(file_name, 'w') as file:
            for data in data_list:
                file.write(str(data) + '\n')
        print('Data has been successfully written to the file!')
    except Exception as e:
        print('Error occurred while writing to the file:', str(e))
def test_proxy(proxy_list):
    available_proxies=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=thread_max) as executor:
        # 将测试任务提交到线程池
        futures = [executor.submit(proxy_filter, item) for item in proxy_list]

        # 获取测试结果
        available_proxies = [future.result() for future in concurrent.futures.as_completed(futures) if future.result()]
    return available_proxies

def main():
    start = time.time()
    proxy_list = get_all_proxy()
    available_proxies = test_proxy(proxy_list)
    print(f'过滤得到 {len(available_proxies)}条数据')
    file_to_delete = open("all.txt", 'w')
    file_to_delete.close()
    write_to_file(available_proxies,'all.txt')
    end = time.time()
    print(f'可用时总计：{end-start}秒')
if __name__ == '__main__':
    main()