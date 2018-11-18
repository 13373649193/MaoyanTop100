import requests
import re
import os
import platform
import logging
import sys
import pymongo
from pyquery import PyQuery as pq

client = pymongo.MongoClient()
db = client['maoyan']
collection = db['Top100']
if collection in db.list_collection_names():
    collection.delete_many({})

logging_file = os.path.join(os.path.dirname(__file__),
                            os.path.basename(sys.argv[0]).split(".")[0] + '.log')
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s : %(levelname)s : %(message)s',
    filename=logging_file,
    filemode='w',
)


def get_page(url):
    headers = {
        'Host': 'maoyan.com',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36'
    }

    proxies = {
        'http': 'http://127.0.0.1:1087',
        'https': 'http://127.0.0.1:1087'
    }

    logging.debug('Begin get content from ' + url)

    try:
        response = requests.get(url=url, headers=headers, proxies=proxies)
        logging.debug('Successful to get data from ' + url)
        return response.text
    except requests.ConnectionError:
        logging.debug('Fail to get data from ' + url)
        return None


def parse_page(html):
    # 用pyquery去解析response
    doc = pq(html)
    items = doc('dd').items()
    for item in items:
        yield {
            'maonyan_rank': item('i.board-index').text(),
            'maoyan_image': item('a.image-link   img.board-img').attr('data-src'),
            'maoyan_title': item('p.name').text(),
            'maoyan_star': item('p.star').text().strip(),
            'maoyan_releasetime': item('p.releasetime').text(),
            'maoyan_score': item('i.integer').text() + item('i.fraction').text()
        }


    # --下面是用正则去解析response--
    # pattern = '<dd>.*?board-index.*?>(\d+)</i>.*?data-src="(.*?)".*?name"><a' \
    #           '.*?>(.*?)</a>.*?star">(.*?)</p>.*?releasetime">(.*?)</p>' \
    #           '.*?integer">(.*?)</i>.*?fraction">(.*?)</i>.*?</dd>'
    # items = re.findall(pattern, html, re.S)
    # for item in items:
    #     yield {
    #         'maoyan_rank': item[0],
    #         'maoyan_image': item[1],
    #         'maoyan_title': item[2],
    #         'maoyan_star': item[3],
    #         'maoyan_releasetime': item[4],
    #         'maoyan_score': item[5] + item[6]
    #     }

def save_to_mongo(item):
    if collection.insert(item):
        logging.debug('Successful to write data')
    else:
        logging.error('Fail to write data' + item)


def schedule(url):
    html = get_page(url)
    for item in parse_page(html):
        save_to_mongo(item)


if __name__ == '__main__':
    logging.debug('main begin')
    base_url = 'http://maoyan.com/board/4?offset='
    for i in range(0, 10):
        index = i * 10
        url = base_url + str(index)
        schedule(url)
    logging.debug('main end')
