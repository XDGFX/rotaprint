import threading
import time


class websocket:
    # Class for interacting with front end GUI over websocket (to receive data)
    def __init__(self):
        # logging.info("Initialising websocket instance")
        # Create thread to run websocket.listen as a daemon (in background)
        listenThread = threading.Thread(target=self.listen)
        listenThread.daemon = False
        listenThread.start()
        # logging.info("Websocket initialised")

    def listen(self):
        # Listen always for messages over websocket
        import asyncio
        import websockets

        async def listener(websocket, path):
            hold = False
            buffer = list()
            while True:
                # Listen for new messages
                message = await websocket.recv()
                print(f'WSKT > {message}')

                if message == "BFH":
                    # Buffer hold condition
                    hold = True
                    buffer = list()
                elif message == "BFR":
                    # Buffer release condition
                    hold = False

                if hold:
                    buffer.append(message)
                else:
                    if buffer:
                        # Buffer has data
                        self.handler(buffer)

                        # threading.Thread(target=self.handler, args=(buffer, ))
                        # Clear buffer
                        buffer = list()
                    else:
                        # Normal message (convert to list)
                        self.handler([message])

                        # threading.Thread(target=self.handler, args=([message], ))

        asyncio.set_event_loop(asyncio.new_event_loop())
        server = websockets.serve(listener, 'localhost', 8765)

        asyncio.get_event_loop().run_until_complete(server)
        asyncio.get_event_loop().run_forever()

    def handler(self, message):
        def emergency_stop(self):
            print("EST")
            pass

        def buffer_hold(self):
            pass

        def buffer_release(self):
            pass

        def set_length(self, data):
            pass

        def set_batch(self, data):
            pass

        def set_radius(self, data):
            pass

        def set_port(self, data):
            pass

        def toggle_check_mode(self, data):
            pass

        def set_grbl_setting(self, data):
            pass

        def send_manual(self, data):
            pass

        switcher = {
            "EST": emergency_stop,
            "BFH": buffer_hold,
            "BFR": buffer_release,
            "LEN": set_length,
            "BAT": set_batch,
            "RAD": set_radius,
            "PRT": set_port,
            "CHK": toggle_check_mode,
            "SET": set_grbl_setting,
            "GRB": send_manual,
        }

        for item in message:
            # Separate command and data
            item = item.split("~")

            # Execute command
            if len(item) == 2:
                # Message has data
                switcher[item[0]](self, item[1])
            elif item[0] == "":
                # Blank message
                pass
            elif len(item) == 1:
                # Message has no data
                switcher[item[0]](self)


websocket()
