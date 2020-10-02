from aiohttp import ClientSession
from json import load

def get_lang():
    with open("tools/lang.json", "r") as file:
        return load(file)

async def get_json(link, headers=None):
    async with ClientSession() as s:
        async with s.get(link, headers=headers) as resp:
            return await resp.json()