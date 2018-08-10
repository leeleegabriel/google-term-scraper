import asyncio
import aiohttp

from proxybroker import Broker

async def show(proxies, p):
    while True:
        proxy = await proxies.get()
        if proxy is None: break
        p.append('http://%s:%s'% (proxy.host, proxy.port))

def getProxies(P_count):
    p = []
    proxies = asyncio.Queue()
    broker = Broker(proxies)
    tasks = asyncio.gather(
        broker.find(types=['HTTP'], limit=P_count),
        show(proxies, p))

    loop = asyncio.get_event_loop()
    loop.run_until_complete(tasks)
    return p

if __name__ == '__main__':
    print(getProxies(10))