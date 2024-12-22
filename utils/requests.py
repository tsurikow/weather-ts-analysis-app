import aiohttp
import asyncio

async def get_response(session, url):
    async with session.get(url) as resp:
        status = resp.status
        response = await resp.json()
        if status == 200:
            return response
        else:
            message = await resp.json()
            raise Exception(message)

async def get_temperature(cities, api_key):
    async with aiohttp.ClientSession() as session:

        temp_tasks = []

        for city in cities:
            url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&lang=en&appid={api_key}'
            temp_tasks.append(asyncio.ensure_future(get_response(session, url)))

        temp_responses = await asyncio.gather(*temp_tasks)

        return temp_responses
