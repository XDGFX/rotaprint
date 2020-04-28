#!/usr/bin/env python
import asyncio
import websockets


class Socket:
    async def speak(self, data):
        async with websockets.connect('ws://localhost:8765') as websocket:
            await websocket.send(data)
            print(f'> {data}')

    async def listen(self, websocket, path):
        while True:
            need_update = await websocket.recv()
            print(f'< {need_update}')


start_server = websockets.serve(Socket().listen, 'localhost', 8765)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()

while True:
    message = input("... ")
    Socket().speak(message)

# import asyncio
# import websockets
# import time


# async def connect(websocket, path):
#     # asyncio.gather(receive(websocket), send(websocket))
#     await receive(websocket)


# async def receive(websocket):
#     async for message in websocket:
#         print(f"< {message}")


# async def send(websocket, data):
#     async with websockets.connect('ws://localhost:8765') as websocket:
#         while True:
#             try:
#                 # a = readValues() #read values from a function
#                 # insertdata(a) #function to write values to mysql
#                 await websocket.send(data)
#                 time.sleep(20)  # wait and then do it again
#             except Exception as e:
#                 print(e)


# start_server = websockets.serve(connect, "localhost", 8765)

# asyncio.get_event_loop().run_until_complete(start_server)
# asyncio.get_event_loop().run_forever()
