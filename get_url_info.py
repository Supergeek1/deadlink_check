import json
import os
from xml.etree import ElementTree

import redis
from loguru import logger
from settings import FILEPATH, REDIS_HOST, REDIS_PORT, REDIS_DB


class GetUrlInfo:
    def __init__(self):
        logger.info("get_url_info >> __init__")

    def read_xml(self, pubcode):
        for xml_ in os.listdir(FILEPATH):
            filename = xml_.split('.')[0]
            if pubcode in filename:
                url_list = []
                try:
                    element_tree = ElementTree.parse(FILEPATH + xml_)
                    element_root = element_tree.getroot()
                except Exception as e:
                    logger.error(f'{FILEPATH + xml_} has error, error: {e}')
                    continue

                base_url = element_root.get('url')
                data = {
                    "pubcode": pubcode,
                    "url": base_url,
                    "section": 'site',
                    "filename": xml_,
                    "retry_times": 0
                }
                url_list.append(data)
                try:
                    if element_root.findall('listings'):
                        listings = element_root.findall('listings')
                    elif element_root.findall('feeds'):
                        listings = element_root.findall('feeds')
                    else:
                        listings = []

                    for url_ in listings[0]:
                        data = {
                            "pubcode": pubcode,
                            "url": url_.text,
                            "section": url_.get('section'),
                            "filename": xml_,
                            "retry_times": 0
                        }
                        url_list.append(data)
                except Exception as e:
                    logger.error(f'{FILEPATH + xml_} error: {e}')
                yield url_list

    def pubcodes_processing(self, pubcodes):
        if pubcodes:
            url_lists = []
            for pubcode in pubcodes:
                url_list = self.read_xml(pubcode)
                url_lists.append(url_list)
            return url_lists

    @staticmethod
    def write_url_info_to_redis(data):
        pool = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
        r_conn = redis.Redis(connection_pool=pool)
        if r_conn.llen('url_infos') > 0:
            r_conn.delete('url_infos')
        r_pipeline = r_conn.pipeline()
        for pubcode in data:
            for file in pubcode:
                for url_info in file:
                    r_pipeline.sadd("url_infos", json.dumps(url_info))
            r_pipeline.execute()


if __name__ == '__main__':
    pubcodes = [
        # 'forum_tieba_baiducn',
        # 'wm_thecovercn',
        'wm_chinanewscn',
        # 'wm_secutimescn'
    ]

    deadlink = GetUrlInfo()
    url_lists = deadlink.pubcodes_processing(pubcodes)

    # url_list为一个pubcode下的文件
    for url_list in url_lists:
        # urls为一个文件下的所有url数据
        for urls in url_list:
            # print(f'urls: {urls}')
            for url in urls:
                print(url)
