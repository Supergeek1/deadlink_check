import random

import aiohttp
import asyncio
from loguru import logger
from settings import PROXY_API
import requests
from faker import Faker
import httpx
from tools.ja3 import SSLFactory

sslgen = SSLFactory()
fake = Faker()
timeout = aiohttp.ClientTimeout(total=100)
sem = asyncio.Semaphore(100)


async def get_proxy(session):
    proxy = ''
    try:
        async with session.get(PROXY_API) as response:
            proxy = await response.json()
            proxy = proxy.get('proxy', '')
    except Exception as e:
        logger.error(e)
    return proxy


async def ah(session, sem, url):
    proxy = await get_proxy(session)
    async with sem:
        try:
            await asyncio.sleep(random.randint(1, 5))
            async with session.get(
                    url,
                    proxy=None,
                    timeout=timeout,
                    headers={'user-agent': fake.chrome()},
                    ssl=sslgen()
            ) as response:
                # logger.info(f'url: [{url}], status_code: [{response.status}]')
                html = await response.json()
                ua = html.get('headers').get('User-Agent')
                logger.info(ua)
        except Exception as e:
            logger.error(f'url: [{url}], error msg: [{e}]')


async def main(urls):
    connector = aiohttp.TCPConnector(limit=100, ssl=False, force_close=True)
    async with aiohttp.ClientSession(
            connector=connector,
            trust_env=True
    ) as session:
        await asyncio.gather(*[ah(session, sem, url) for url in urls])


async def hx(session, sem, url):
    async with sem:
        proxy = await get_proxy(session)
        proxy = {'http://': proxy, 'https://': proxy}
        try:
            async with httpx.AsyncClient(follow_redirects=True, verify=False, proxies=proxy) as client:
                response = await client.get(url, headers={'user-agent': fake.chrome()})
                logger.info(f'url: [{url}], status_code: [{response.status_code}]')
        except Exception as e:
            logger.error(f'url: [{url}], error msg: [{e}]')


def rq(url):
    response = requests.request(method='GET', url=url, headers={'user-agent': fake.chrome()}, verify=False,
                                allow_redirects=True)
    logger.info(response.status_code)
    if response.history:
        for history in response.history:
            print(history.url)
            print(history.status_code)
            print(history.text)
    html = response.text
    size = round(len(html) / 1024, 2)
    logger.info(size)


if __name__ == '__main__':
#     urls = '''https://www.douban.com/group/search?cat=1013&q=%E5%8D%8E%E4%B8%BA%20%E4%BD%BF%E5%91%BD%E5%8F%AC%E5%94%A4%20%E9%97%B9%E5%83%B5&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E7%94%B7%E5%AD%A9%20%E6%9D%80%E6%AD%BB%20%E6%B1%9F%E8%A5%BF&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E5%B7%B4%E5%AE%9D%E8%8E%89%20%E5%8F%8D%E5%8D%8E%20tx&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E4%BC%81%E9%B9%85+%E7%A7%A6%E6%97%B6&sort=time
# https://www.douban.com/
# https://www.douban.com/group/search?cat=1013&q=%E4%BA%AC%E4%B8%9C&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E5%90%83%E9%B8%A1%20%E4%B8%89%E5%AD%A3%E5%BA%A6%20%E8%90%A5%E6%94%B6&sort=time
# https://www.douban.com/group/185733/
# https://www.douban.com/group/search?cat=1013&q=%E9%A6%99%E6%B8%AF%E8%A7%80%E5%85%89&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E8%85%BE%E8%AE%AF%20%E5%8E%9F%E7%A5%9E%20%E5%8E%9F%E5%88%9B&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E5%B0%91%E5%B9%B4%20%E8%85%BE%E8%AE%AF%20%E7%88%B7%E7%88%B7&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E5%8D%8E%E6%99%A8%E5%AE%87%20%E6%AD%8C%20%E6%94%B9%E5%8A%A8&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E5%85%AD%E5%9B%9B%E5%BC%80+%E8%85%BE%E8%AE%AF&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E9%80%9A%E4%BF%A1%E7%AE%A1%E7%90%86%E5%B1%80+%E6%95%B4%E6%94%B9+%E5%A4%A9%E5%A4%A9%E8%B1%A1%E6%A3%8B&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E5%92%8C%E5%B9%B3%E7%B2%BE%E8%8B%B1%20%E4%B8%96%E7%95%8C%E8%B5%9B&sort=time
# https://www.douban.com/group/search?cat=1013&q=burberry%20%E6%96%B0%E7%96%86%20%E4%BC%81%E9%B9%85&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E5%84%BF%E7%AB%A5%20%E6%B2%89%E8%BF%B7%20%E6%B1%9F%E8%A5%BF&sort=time
# https://www.douban.com/group/search?cat=1013&q=ieg%20%E8%B4%AA%E6%B1%A1&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E9%A3%9E%E8%A1%8C%E6%8C%87%E6%8C%A5%E5%AE%B6%20%E6%94%B9%E5%8A%A8&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E5%B7%B4%E5%AE%9D%E8%8E%89%20%E5%8F%8D%E5%8D%8E%20lol&sort=time
# http://www.douban.com/
# https://www.douban.com/group/search?cat=1013&q=%E8%8A%B1%E7%B2%89%20%E5%92%8C%E5%B9%B3%E7%B2%BE%E8%8B%B1%20%E6%9A%82%E5%81%9C&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E5%B0%8F%E9%A9%AC+%E5%8F%91+%E8%82%A1%E7%A5%A8&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E5%85%AC%E5%AD%AB%E9%9B%A2+%E7%89%9B%E5%B9%B4+%E7%9A%AE%E8%86%9A&sort=time
# https://www.douban.com/group/search?cat=1013&q=burberry%20%E5%9B%BD%E5%AE%B6%20%E5%A4%A9%E7%BE%8E&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E5%8D%81%E5%9B%9B%E5%B2%81%20%E6%9D%80%E5%AE%B3%20%E6%B8%B8%E6%88%8F&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E5%85%AD%E7%B3%BB+%E7%8E%8B%E8%80%85%E8%8D%A3%E8%80%80&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E7%8E%8B%E8%80%85%E8%8D%A3%E8%80%80%20%E4%B8%89%E5%AD%A3%E5%BA%A6%20%E6%94%B6%E5%85%A5&sort=time
# https://movie.douban.com/review/latest/
# https://www.douban.com/group/search?cat=1013&q=tx%20%E5%8D%97%E5%B1%B1%E5%8C%BA%E6%B3%95%E9%99%A2%20%E6%8A%96%E9%9F%B3&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E5%85%A8%E5%A2%83%E5%B0%81%E9%94%81+%E9%B9%85%E5%8E%82&sort=time
# https://www.douban.com/group/search?cat=1013&q=tx%20%E5%8E%9F%E7%A5%9E%20WeTest&sort=time
# https://www.douban.com/group/search?cat=1013&q=IEG+%E5%A5%96%E9%87%91+%E9%BA%93%E6%B9%96&sort=time
# https://www.douban.com/group/search?cat=1013&q=burberry%20%E5%8F%8D%E5%8D%8E%20%E5%A4%A9%E7%BE%8E&sort=time
# https://www.douban.com/group/search?cat=1013&q=gm%20%E9%80%AE%E6%8D%95&sort=time
# https://www.douban.com/group/search?cat=1013&q=h%26m%20%E5%8D%96%E5%9B%BD%20%E8%85%BE%E8%AE%AF&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E5%8D%8E%E4%B8%BA%20%E4%BD%BF%E5%91%BD%E5%8F%AC%E5%94%A4%20%E5%8F%98%E6%9B%B4&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E5%A5%BD%E6%95%85%E4%BA%8B%E7%94%9F%E7%94%9F%E4%B8%8D%E6%81%AF&sort=time
# https://www.douban.com/group/search?cat=1013&q=Hm%20%E5%A4%AE%E8%A7%86%20%E7%8E%8B%E8%80%85&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E5%85%AD%E7%B3%BB+%E8%B5%9B%E5%88%B6&sort=time
# https://www.douban.com/group/search?cat=1013&q=Hm%20%E5%A4%AE%E8%A7%86%20tx&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E5%B0%91%E5%B9%B4%C2%A0%E7%88%B7%E7%88%B7%C2%A0%E6%89%8B%E6%9C%BA&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E8%8B%B1%E9%9B%84%E8%81%94%E7%9B%9F+%E6%89%8B%E6%9C%BA%E7%89%88+%E5%9B%BD%E6%9C%8D&sort=time
# https://www.douban.com/group/search?cat=1013&q=tx%20%E5%BD%92%E5%B1%9E%20%E7%9F%AD%E8%A7%86%E9%A2%91&sort=time
# https://www.douban.com/group/search?cat=1013&q=hcy%20%E4%B8%BB%E9%A2%98%E6%9B%B2%20%E5%80%9F%E9%89%B4&sort=time
# https://www.douban.com/group/search?cat=1013&q=lol+%E6%89%8B%E6%9C%BA%E7%89%88+%E6%89%B9%E5%87%86&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E6%A2%81%E6%9F%B1%20%E7%A6%BB%E4%BB%BB&sort=time
# https://www.douban.com/group/tods/discussion?start=0
# https://www.douban.com/group/search?cat=1013&q=%E6%B5%B7%E8%B4%BC%E7%8E%8B%20%E8%83%8E%E6%AF%92&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E5%8D%8E%E4%B8%BA%20%E9%B9%85%E5%8E%82%20%E4%B8%8B%E6%9E%B6&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E5%A4%A9%E5%88%80%20%E6%97%B6%E8%A3%85%20%E6%A8%A1%E4%BB%BF&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E5%84%BF%E7%AB%A5%20%E6%B2%89%E8%BF%B7%20%E5%8D%97%E6%98%8C&sort=time
# https://www.douban.com/group/search?cat=1013&q=burberry%20%E5%85%B1%E9%9D%92%E5%9B%A2%20%E8%85%BE%E8%AE%AF&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E7%8E%8B%E8%80%85+%E7%9A%AE%E8%82%A4+%E7%97%9B%E9%AA%82&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E6%A9%99%E6%AD%A6+%E4%B8%89%E7%99%BE+%E6%BC%AB%E6%94%B9&sort=time
# https://www.douban.com/group/search?cat=1013&q=bbr%20xj%20%E8%85%BE%E8%AE%AF&sort=time
# https://www.douban.com/group/search?cat=1013&q=Lolm+%E5%BC%80%E5%90%AF&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E5%8F%B6%E5%8A%B2%E5%B3%B0
# https://www.douban.com/group/search?cat=1013&q=lol+%E6%89%8B%E6%B8%B8+%E5%AE%A1%E6%89%B9&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E8%AB%B8%E8%91%9B%E4%BA%AE+%E7%89%9B%E5%B9%B4+%E7%9A%AE%E8%86%9A&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E5%BD%AD%E8%BF%A6%E4%BF%A1%20%E8%B0%83%E5%B2%97&sort=time
# https://www.douban.com/group/search?cat=1013&q=Hm%20%E6%96%B0%E7%96%86%20%E7%91%B6&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E5%B7%B4%E5%AE%9D%E8%8E%89%20bci%20%E9%A9%AC%E5%8C%96%E8%85%BE&sort=time
# https://www.douban.com/group/search?cat=1013&q=Hm+%E8%BE%B1%E5%8D%8E+tencent&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E5%81%83%E5%B8%88%20%E4%B8%80%E6%A0%B7&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E5%8D%8E%E4%B8%BA%20%E7%8E%8B%E8%80%85%E8%8D%A3%E8%80%80%20%E6%89%93%E5%8E%8B&sort=time
# https://www.douban.com/group/search?cat=1013&q=Hm%20%E6%96%B0%E7%96%86%20%E4%BC%81%E9%B9%85&sort=time
# https://www.douban.com/group/search?cat=1013&q=bbr%20%E5%8F%8D%E5%8D%8E%20%E7%8E%8B%E8%80%85&sort=time
# https://www.douban.com/group/search?cat=1013&q=h%26m%20%E5%9B%BD%E5%AE%B6%20tx&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E7%94%B7%E5%AD%A9%20%E8%85%BE%E8%AE%AF%20%E5%8D%97%E6%98%8C&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E5%88%91%E4%BA%8B%E6%8B%98%E7%95%99%20%E7%8E%8B%E8%80%85%2030%E5%B2%81&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E8%85%BE%E8%AE%AF%20%E5%BD%92%E5%B1%9E%20%E6%8A%96%E9%9F%B3&sort=time
# https://www.douban.com/group/search?cat=1013&q=雅思%20WC&sort=time
# https://www.douban.com/group/search?cat=1013&q=burberry%20%E5%9B%BD%E5%AE%B6%20%E8%85%BE%E8%AE%AF&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E5%8D%8E%E4%B8%BA%20%E8%85%BE%E8%AE%AF%20%E8%A7%A3%E7%BA%A6&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E5%85%89%E5%A4%9C&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E8%85%BE%E8%AE%AF%20%E5%88%A4%E5%86%B3%20dy&sort=time
# https://www.douban.com/group/search?cat=1013&q=bbr%20xj%20lol&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E7%8E%8B%E8%80%85+%E5%B9%B4%E9%99%90&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E5%A4%A9%E6%B6%AF%E6%98%8E%E6%9C%88%E5%88%80%20%E6%97%B6%E8%A3%85%20%E6%8A%84%E8%A2%AD&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E8%8A%B1%E7%B2%89%20%E8%85%BE%E8%AE%AF%20%E5%9E%84%E6%96%AD&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E6%8A%B5%E5%88%B6%20%E5%8F%8D%E5%8D%8E%20%E9%A9%AC%E5%8C%96%E8%85%BE&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E8%8B%B1%E9%9B%84%E8%81%94%E7%9B%9F%20Q3%20%E5%87%80%E5%88%A9%E6%B6%A6&sort=time
# https://www.douban.com/group/search?cat=1013&q=h%26m%20%E4%B8%AD%E5%9B%BD%20tx&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E5%91%82%E5%B8%83+%E5%B9%B4%E9%99%90+%E7%9A%AE%E8%86%9A&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E5%86%9C%E8%8D%AF+%E7%9A%AE%E8%82%A4+%E6%B2%A1%E4%B8%8A%E5%BF%83&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E8%8A%82%E5%A5%8F%E5%A4%A7%E5%B8%88+%E5%81%9C%E8%BF%90&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E5%B7%B4%E5%AE%9D%E8%8E%89%20%E6%96%B0%E7%96%86%20%E8%8B%B1%E9%9B%84%E8%81%94%E7%9B%9F&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E5%B7%A5%E4%BD%9C%E5%AE%A4%E6%80%BB%E8%A3%81%20%E8%B0%83%E5%B2%97&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E6%8A%B5%E5%88%B6%20%E5%8D%96%E5%9B%BD%20%E9%A9%AC%E5%8C%96%E8%85%BE&sort=time
# https://www.douban.com/group/search?cat=1013&q=h%26m%20%E5%8F%8D%E5%8D%8E%20tencent&sort=time
# https://www.douban.com/group/search?cat=1013&q=lol+%E6%89%8B%E6%9C%BA%E7%89%88+%E7%89%88%E5%8F%B7&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E9%B9%85%E5%8E%82+%E5%8F%91+100%E8%82%A1&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E5%B7%B4%E5%AE%9D%E8%8E%89%20bci%20%E4%BC%81%E9%B9%85&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E5%8D%81%E5%9B%9B%E5%B2%81%20%E9%B9%85%E5%8E%82%20%E5%AE%89%E4%B9%89%E5%8E%BF&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E5%A4%A9%E5%88%80%20%E6%8A%BD%E5%A5%96%20%E7%BB%B4%E6%9D%83&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E5%81%83%E5%B8%88%20%E6%A8%A1%E4%BB%BF&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E9%80%9A%E4%BF%A1%E7%AE%A1%E7%90%86%E5%B1%80+%E5%85%B3%E5%81%9C+%E6%89%8B%E6%B8%B8%E5%AE%9D&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E4%BD%BF%E5%91%BD%E5%8F%AC%E5%94%A4%20%E6%89%AF%E7%9A%AE&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E7%94%B7%E5%AD%A9%C2%A0%E6%9D%80%E5%AE%B3%C2%A0%E8%85%BE%E8%AE%AF&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E8%8B%B1%E9%9B%84%E8%81%94%E7%9B%9F+%E6%89%8B%E6%9C%BA%E7%89%88+%E8%BF%87%E5%AE%A1&sort=time
# https://www.douban.com/group/search?cat=1013&q=%E8%8A%B1%E7%B2%89%20%E5%92%8C%E5%B9%B3%E7%B2%BE%E8%8B%B1%20%E8%A7%A3%E7%BA%A6&sort=time
# https://www.douban.com/group/search?cat=1013&q=cyys&sort=time'''.splitlines()
    urls = ['http://httpbin.org/ip' for _ in range(50)]
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(urls))
    loop.run_until_complete(asyncio.sleep(0))
    # rq(url)
