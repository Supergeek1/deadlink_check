import json
import redis
import pandas
from settings import REDIS_DB, REDIS_HOST, REDIS_PORT
from loguru import logger


class Export:
    def __init__(self, key, filename):
        logger.info("export >> __init__")
        self.key = key
        self.filename = filename
        self.conn = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

    def export_to_csv(self):
        url_info_list = self.conn.lrange(self.key, 0, -1)
        pubcodes = []
        sections = []
        urls = []
        status_codes = []
        deadlinks = []
        msgs = []
        filenames = []
        for url_info in url_info_list:
            url_info = json.loads(str(url_info, encoding="utf-8"))
            pubcodes.append(url_info.get('pubcode', ''))
            sections.append(url_info.get('section', ''))
            urls.append(url_info.get('url', ''))
            status_codes.append(url_info.get('status_code', ''))
            if url_info.get('deadlink'):
                deadlinks.append('Dead Link')
            else:
                deadlinks.append('Normal')
            msgs.append(url_info.get('msg', ''))
            filenames.append(url_info.get('filename', ''))
        dataframe = pandas.DataFrame({
            'Pubcode': pubcodes,
            'Config XML': filenames,
            'Result': deadlinks,
            'Response Code': status_codes,
            'Link Type': sections,
            'URL': urls,
            'MSG': msgs
        })
        dataframe.to_csv(f"{self.filename}.csv", index=False, sep=',', encoding='utf_8_sig')
        logger.info(f'导出到{self.filename}.csv')

    def test(self):
        url_info_list = self.conn.lrange('deadlink', 0, 2)
        for url_info in url_info_list:
            url_info = json.loads(str(url_info, encoding="utf-8"))
            print(url_info)


if __name__ == '__main__':
    pubcodes = [
        # 'forum_tieba_baiducn',
        # 'wm_thecovercn',
        'wm_chinanewscn',
        # 'wm_secutimescn'
    ]

    deadlink = Export(key='deadlink2', filename='result')
    deadlink.export_to_csv()
    # deadlink.test()
