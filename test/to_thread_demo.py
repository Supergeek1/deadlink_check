import asyncio
import requests
import time
import aiohttp


def req(*args):
    session, url = args
    response = session.get(url)
    return response


async def down(session):
    response = await asyncio.to_thread(req, session, 'http://httpbin.org/ip')
    print(response.json())
    # try:
    #     async with session.get('http://httpbin.org/ip') as response:
    #         html = await response.json()
    #         print(html)
    # except Exception as e:
    #     print(e)


async def main():
    session = requests.session()
    # async with aiohttp.ClientSession() as session:
    await asyncio.gather(*[down(session) for _ in range(100)])


if __name__ == '__main__':
    start_time = time.time()
    asyncio.run(main())
    print(f'use {time.time() - start_time}')
