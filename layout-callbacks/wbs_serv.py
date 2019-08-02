#!/usr/bin/env python

import asyncio
import logging

import websockets

from reloader import listen as reloader
from config.const import *
from redis_handler import RWrapper

LOG_LEVEL = logging.DEBUG
logger = logging.getLogger('server')
logger.setLevel(LOG_LEVEL)

class Server(object):
    def __init__(self):
        self.ip, self.port = '0.0.0.0', TCPPORT
        self.w_ip, self.w_port = '0.0.0.0', WEBSOCKETPORT
        self.push = RWrapper().push_xml

    async def listen(self):
        # Listen for incoming requests
        await websockets.serve(self.echo, self.w_ip, self.w_port)
        asrv = await asyncio.start_server(self._handle_request, self.ip, int(self.port))
        print("Listening")
        await reloader()
        await asrv.serve_forever()


    async def echo(self, websocket, path):
        print('New websocket connection')
        async for message in websocket:
            if message == b'':
                break
            await self.push(message)

    async def _handle_request(self, reader, writer):
        addr = writer.get_extra_info('peername')
        print('handling', addr)
        gen = self._recv_data(reader, writer)
        async for msg in gen:
            await self.push(msg)
        # ...

    async def _recv_data(self, stream, writer):
        while True:
            try:
                msg = await asyncio.wait_for(stream.readuntil(separator=b'/>'), timeout=20)
                if msg == b'':
                    break
                msg = msg.decode('utf-8')
                yield msg
                await asyncio.sleep(0)
            except Exception as ex:
                print('closing connection', ex, ex.args)
                writer.close()
                yield False
                break



if __name__ == "__main__":
    srv = Server()
    asyncio.get_event_loop().run_until_complete(srv.listen())
