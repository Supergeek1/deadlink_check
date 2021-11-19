import asyncio
import json
import random
import time

import aiohttp
from faker import Faker
from loguru import logger
import aioredis
from settings import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_KEY, PROXY_API, SEM, MAX_RETRY_TIME, MAX_WORKER
from get_url_info import GetUrlInfo
from pubcodes import pubcodes
from export_csv import Export
import ssl
from concurrent.futures import ProcessPoolExecutor
from tools.ja3 import SSLFactory
from tools.redis import Redis


class DeadlinkProcessing:
    def __init__(self):
        logger.info("deadlink_processing >> __init__")
        self.fake = Faker()
        self.sem = asyncio.Semaphore(SEM)
        self.known_error_status = [0, 204, 400, 401, 403, 404, 493, 500, 502, 503, 504, 600]
        self.deadlink_keys = ['版块不存在', '版块已删除', '页面已删除', '页面不存在', '网页不存在', '网页已删除',
                              '内容不存在', '内容已删除', '网站不存在', '网站已关闭', '网站被关闭', '内容已转移',
                              '帖子已删除', '帖子不存在', '域名过期或出售', '空间被关闭', '信息已过期',
                              '暂不能显示，看看其他内容吧', '交易已关闭']
        self.timeout = aiohttp.ClientTimeout(total=60)
        self.sslgen = SSLFactory()

    async def get_proxy(self, session):
        proxy = None
        try:
            async with session.get(PROXY_API) as response:
                proxy = await response.json()
                proxy = proxy.get('proxy', '')
        except Exception as e:
            logger.error(e)
        return proxy

    async def fetch_with_limit(self, session, redis_conn):
        async with self.sem:
            await self.fetch(session, redis_conn)

    async def retry(self, url_info, msg, redis_conn, status=''):
        if url_info['retry_times'] >= MAX_RETRY_TIME:
            result = {
                'pubcode': url_info.get('pubcode', ''),
                'section': url_info.get('section', ''),
                'url': url_info.get('url', ''),
                'status_code': status,
                'deadlink': True,
                'filename': url_info.get('filename', ''),
                'msg': f'{msg} and Retry more than {MAX_RETRY_TIME} times'
            }
            await redis_conn.lpush(REDIS_KEY, json.dumps(result).encode())
            logger.warning(f"pubcode:[{url_info.get('pubcode', '')}],url:[{url_info.get('url', '')}],"
                           f"status_code:[{status}],msg:[{msg} and Retry more than {MAX_RETRY_TIME} times]")
        else:
            url_info['retry_times'] += 1
            await redis_conn.sadd('url_infos', json.dumps(url_info))
            logger.warning(
                f"retry_times:[{url_info['retry_times']}],pubcode:[{url_info['pubcode']}],url:[{url_info['url']}],"
                f"Because: {msg}"
            )

    async def fetch(self, session, redis_conn):
        while True:
            try:
                await asyncio.sleep(random.randint(1, 5))
                url_info = await redis_conn.spop('url_infos')
            except Exception as e:
                logger.error(e)
                await asyncio.sleep(2)
                continue
            if not url_info:
                return
            url_info = json.loads(url_info)
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
                async with session.get(
                        url,
                        proxy=proxy,
                        timeout=self.timeout,
                        headers={'user-agent': self.fake.chrome()},
                        ssl=self.sslgen()
                ) as response:
                    status = response.status
                    result['status_code'] = status
                    if status == 200:
                        html = await response.text()
                        size = round(len(html) / 1024, 2)
                        if size < 2:
                            result['deadlink'] = True
                            result['msg'] = "pageSize smaller than 2kb"
                        elif any(ext in html for ext in self.deadlink_keys):
                            result['deadlink'] = True
                            result['msg'] = "page is deleted"
                    await redis_conn.lpush(REDIS_KEY, json.dumps(result).encode())
                    logger.info(
                        f"pubcode:[{pubcode}],url:[{url}],status_code:[{result['status_code']}],msg:[{result['msg']}]")
            except UnicodeDecodeError:
                result['msg'] = "can't decode source"
                await redis_conn.lpush(REDIS_KEY, json.dumps(result).encode())
                logger.info(
                    f"pubcode:[{pubcode}],url:[{url}],status_code:[{result['status_code']}],msg:[{result['msg']}]")
            except asyncio.exceptions.TimeoutError:
                await self.retry(url_info, f"Request timeout", redis_conn)
            except aiohttp.ClientResponseError as response_error:
                status = response_error.status
                if status in self.known_error_status:
                    result['deadlink'] = True
                    result['status_code'] = status
                    await redis_conn.lpush(REDIS_KEY, json.dumps(result).encode())
                    logger.info(
                        f"pubcode:[{pubcode}],url:[{url}],status_code:[{status}],msg:[Error status]")
                else:
                    await self.retry(url_info, f"status_code is [{status}]", redis_conn, status)
            except (aiohttp.ClientProxyConnectionError, aiohttp.ClientHttpProxyError):
                await self.retry(url_info, f"Proxy error", redis_conn)
            except aiohttp.ServerDisconnectedError:
                await self.retry(url_info, f"ServerDisconnectedError", redis_conn)
            except Exception as e:
                await self.retry(url_info, f"{str(e)}", redis_conn)

    async def main(self):
        r = Redis()
        redis_conn = await r.get_redis_pool((REDIS_HOST, REDIS_PORT), db=REDIS_DB, encoding='utf-8')
        conn = aiohttp.TCPConnector(verify_ssl=False, limit=SEM)
        async with aiohttp.ClientSession(
                connector=conn,
                raise_for_status=True,
                # trust_env=True,
        ) as session:
            task = []
            for _ in range(SEM):
                task.append(asyncio.ensure_future(self.fetch_with_limit(session, redis_conn)))
            await asyncio.gather(*task)


def start(pid):
    logger.info(f'pid: {pid} start')
    deadlink = DeadlinkProcessing()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(deadlink.main())
    loop.run_until_complete(asyncio.sleep(0))
    # asyncio.run(deadlink.main())


if __name__ == '__main__':
    # pubcodes = ['forum_doubancn']
    url = GetUrlInfo()
    data = url.pubcodes_processing(pubcodes)
    url.write_url_info_to_redis(data)
    logger.info(f'共{len(data)}个 pubcode')
    time.sleep(5)
    with ProcessPoolExecutor(max_workers=MAX_WORKER) as executor:
        executor.map(start, [pid for pid in range(MAX_WORKER)])
    Export(key=REDIS_KEY, filename=REDIS_KEY).export_to_csv()
