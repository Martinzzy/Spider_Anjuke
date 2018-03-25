import requests
import chardet
import pymongo
from pyquery import PyQuery as pq
from requests.exceptions import ConnectionError

client = pymongo.MongoClient('localhost')
db = client['anjuke']
MAX_COUNT = 5
proxy = None
headers = {'user-agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.27 Safari/537.36'}

def get_proxy():
    try:
        response = requests.get('http://127.0.0.1:5555/random')
        if response.status_code == 200:
            return response.text
        return None
    except ConnectionError:
        print('获取代理失败')
        return None

def get_one_page(url,count=1):
    print('正在爬取:', url)
    print('尝试的次数:', count)
    global proxy
    if count >= MAX_COUNT:
        print('Tried Too Many Counts')
        return None
    try:
        if proxy:
            proxy = {'http':'http://'+proxy}
            response = requests.get(url,headers=headers,proxies=proxy)
        else:
            response = requests.get(url,headers=headers)
        if response.status_code == 200:
            response.encoding = chardet.detect(response.content)['encoding']
            if '访问验证-安居客' in response.text:
                proxy = get_proxy()
                return get_one_page(url)
            else:
                return response.text
        if response.status_code == 302:
            print('请求的状态码是:',response.status_code)
            proxy = get_proxy()
            if proxy:
                return get_one_page(url)
            else:
                print('获取代理失败')
                return None
    except Exception as e:
        print('Error Occurred', e.args)
        proxy = get_proxy()
        count += 1
        return get_one_page(url, count)


def parse_one_page(html):
    doc = pq(html)
    items = doc('#houselist-mod-new li').items()
    for item in items:
        house_title = item.find('.house-title .houseListTitle').text()
        house_quality = item.find('.house-title .guarantee_icon1').text()
        house_img = item.find('.item-img img').attr.src
        address = item.find('.comm-address').text().replace('\xa0\xa0','')
        brokername = item.find('.details-item .brokername').text().replace('\ue147','')
        info = item.find('.details-item').text().split('\ue147')[0]
        tags = item.find('.tags-bottom').text()
        house_total_price = item.find('.pro-price .price-det').text()
        house_unit_price = item.find('.unit-price').text()
        data = {
            'house_title':house_title,
            'house_quality':house_quality,
            'house_img':house_img,
            'house_address':address,
            'house_broker':brokername,
            'house_info':info,
            'house_advantages':tags,
            'house_total_price':house_total_price,
            'house_unit_price':house_unit_price
        }
        save_to_mongo(data)


def save_to_mongo(data):
    if db['house'].insert(data):
        print('存储到MongoDB数据库成功',data)
    else:
        print('存储到MongoDB数据库失败',data)


def main(page):
    url = 'https://beijing.anjuke.com/sale/p{}/'.format(page)
    html = get_one_page(url)
    parse_one_page(html)


if __name__ == '__main__':
    for page in range(1,20):
        main(page)

