import asyncio
import json

import httpx
from faker import Faker
from loguru import logger
import aioredis
from settings import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_KEY, PROXY_API
from get_url_info import GetUrlInfo
from pubcodes import pubcodes
from export_csv import Export


class Redis:
    _redis = None

    async def get_redis_pool(self, *args, **kwargs):
        if not self._redis:
            self._redis = await aioredis.create_redis_pool(*args, **kwargs)
        return self._redis

    async def close(self):
        if self._redis:
            self._redis.close()
            await self._redis.wait_closed()


class DeadlinkProcessing:
    def __init__(self):
        logger.info("deadlink_processing >> __init__")
        self.fake = Faker()
        self.SIZE = 100
        self.sem = asyncio.Semaphore(self.SIZE)
        self.known_error_status = ['403', '404', '500']
        self.sync_session = httpx.Client()

    def get_proxy(self):
        proxy = None
        try:
            async with session.get(PROXY_API) as response:
                proxy = await response.json()
                proxy = proxy.get('proxy', '')
        except Exception as e:
            logger.error(e)
        return proxy

    async def fetch_with_limit(self, queue, redis_conn):
        async with self.sem:
            await self.fetch(queue, redis_conn)

    async def fetch_test(self, queue, redis_conn):
        while True:
            try:
                url_info = queue.get_nowait()
            except asyncio.QueueEmpty:
                return
            url = url_info.get('url', '')
            pubcode = url_info.get('pubcode', '')
            result = {
                'pubcode': pubcode,
                'section': url_info.get('section', ''),
                'url': url,
                'status_code': '',
                'deadlink': False,
                'filename': url_info.get('filename', ''),
                'msg': ''
            }
            if url is None:
                return
            await redis_conn.lpush('test', 1)

    async def fetch(self, queue, redis_conn):
        while True:
            try:
                url_info = queue.get_nowait()
            except asyncio.QueueEmpty:
                return
            url = url_info.get('url', '')
            pubcode = url_info.get('pubcode', '')
            result = {
                'pubcode': pubcode,
                'section': url_info.get('section', ''),
                'url': url,
                'status_code': '',
                'deadlink': False,
                'filename': url_info.get('filename', ''),
                'msg': ''
            }
            if url is None:
                return
            try:
                proxy = await self.get_proxy(session)
                proxies = {
                    'http://': proxy,
                    'https://': proxy,
                }
                async with httpx.AsyncClient(http2=True) as session:
                    response = await session.get(
                            url,
                            proxies=proxies,
                            timeout=60,
                            headers={'user-agent': self.fake.chrome()}
                    )
                    status = str(response.status_code)
                    result['status_code'] = status
                    if status == 200:
                        html = response.text(encoding="utf-8")
                        size = round(len(html) / 1024, 2)
                        if size < 2:
                            result['deadlink'] = True
                            result['msg'] = "pageSize samller than 2kb"
                        elif '抱歉，指定的版块不存在' in html or '已删除' in html:
                            result['deadlink'] = True
                            result['msg'] = "page is deleted"
                    elif status in self.known_error_status:
                        result['deadlink'] = True
            except Exception as e:
                result['deadlink'] = True
                result['msg'] = str(e)
                logger.error(result)
                logger.error(e)
            finally:
                await redis_conn.lpush(REDIS_KEY, json.dumps(result).encode())
                logger.info(
                    f"pubcode:[{pubcode}],url:[{url}],status_code:[{result['status_code']}],msg:[{result['msg']}]")

    async def main(self, data):
        redis = Redis()
        redis_conn = await redis.get_redis_pool((REDIS_HOST, REDIS_PORT), db=REDIS_DB, encoding='utf-8')
        queue = asyncio.Queue()
        for pubcode in data:
            for file in pubcode:
                for url_info in file:
                    queue.put_nowait(url_info)
        logger.info(f'共有{queue.qsize()}条 url')
        task = []
        for _ in range(self.SIZE):
            task.append(asyncio.ensure_future(self.fetch_with_limit(queue, redis_conn)))
        await asyncio.gather(*task)

    def start(self, urllists):
        for urllist in urllists:
            asyncio.run(self.main(urllist))


if __name__ == '__main__':
    pubcodes = ['wm_chinanewscn']
    url = GetUrlInfo()
    data = url.pubcodes_processing(pubcodes)
    logger.info(f'共{len(data)}个 pubcode')
    deadlink = DeadlinkProcessing()
    asyncio.run(deadlink.main(data))
    Export(key=REDIS_KEY, filename=REDIS_KEY).export_to_csv()
