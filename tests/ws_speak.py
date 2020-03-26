#!/usr/bin/env python
import asyncio
import websockets


async def speak(data):
    async with websockets.connect('ws://localhost:8765') as websocket:
        await websocket.send(data)
        print(f'> {data}')


asyncio.get_event_loop().run_until_complete(speak(input("? ")))
