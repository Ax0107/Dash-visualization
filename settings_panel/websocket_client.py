"""'''<Trajectory PacketNumber="0" Time="0.1" X="44.2" Y="0.2" Z="0" Vx="444.28" Vy="1.87" Vz="0.03" Ax="42.915" Ay="-9.6" Az="0.061" Teta="0.033" Psi="0.004" Gamma="0"/>'''


'''async def hello():
    async with websockets.connect(
            'ws://localhost:5679') as websocket:
        while True:
            response = await websocket.recv()
            df = pd.read_json(response)
            print(f"< {df}")

asyncio.get_event_loop().run_until_complete(hello())
asyncio.get_event_loop().run_forever()

async def hello():
    msg = '<Trajectory PacketNumber="0" Time="0.1" X="44.2" Y="0.2" Z="0" Vx="444.28" Vy="1.87" Vz="0.03" Ax="42.915" Ay="-9.6" Az="0.061" Teta="0.033" Psi="0.004" Gamma="0"/>'
    async with websockets.connect(
            'ws://localhost:5679') as websocket:
        #websocket.handshake('ws://192.168.1.210:5678')
        while True:
            await asyncio.sleep(0.5)
            await websocket.send(msg)
            '''response = await websocket.recv()
            print(response,'bbb')'''


asyncio.get_event_loop().run_until_complete(hello())
asyncio.get_event_loop().run_forever()

'''"""
import asyncio
from datetime import datetime
from random import random

import math

NUM_MSGS = 10000000


async def tcp_echo_client(loop):
    try:
        reader, writer = await asyncio.open_connection('localhost', 5678,
                                                       loop=loop)
        pn = 0
        import time
        print(time.time())
        t = time.time()
        x = 1000
        while True:
            x = math.sin(datetime.now().timestamp() * x) * (random() + x)
            y = math.cos(datetime.now().timestamp() * 0.1) * (random() + 10)
            z = math.sin(datetime.now().timestamp() * 0.001) * (random() + 1)
            x2 = math.sin(datetime.now().timestamp() * x) * (random() + x)
            y2 = math.cos(datetime.now().timestamp() * 0.1) * (random() + 10)
            z2 = math.sin(datetime.now().timestamp() * 0.001) * (random() + 1)

            # print(x,y,z)
            s = '<Trajectory PacketNumber="%s" Time="%s" Y="%s" X="%s" Z="%s" Y2="%s" X2="%s" Z2="%s"/>' % (
                pn, time.time() - t, x, y, -z, x2, y2, z2)
            pn+=1
            message = s.encode()
            # print('Send: %r' % message)
            writer.write(message)
            print('.', end='')
            await asyncio.sleep(0.1)
            #print('Close the socket')

    except Exception as e:
        try:
            writer.close()
        except:
            pass
        print(e)
        await asyncio.sleep(10)
        pass


async def msg_controller(loop):
    await tcp_echo_client(loop)


async def myrange(start, stop=None, step=1):
    if stop:
        range_ = range(start, stop, step)
    else:
        range_ = range(start)
    for i in range_:
        yield i
        await asyncio.sleep(0.2)


loop = asyncio.get_event_loop()
loop.run_until_complete(tcp_echo_client(loop))
loop.close()
