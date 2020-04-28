#!/usr/bin/env python
import asyncio
import websockets


async def listen(websocket, path):
    while True:
        need_update = await websocket.recv()
        print(f'< {need_update}')

start_server = websockets.serve(listen, 'localhost', 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
