# !/usr/bin/env python
from threading import Lock

from flask import Flask, render_template, session, request, \
    copy_current_request_context
from flask_socketio import SocketIO, emit, disconnect

from redis_handler import RWrapper

import logging
LOG_LEVEL = logging.DEBUG
LOGFORMAT = "  %(log_color)s- %(name)s-%(levelname)-8s%(reset)s | %(log_color)s%(message)s%(reset)s"
from colorlog import ColoredFormatter
logging.root.setLevel(LOG_LEVEL)
formatter = ColoredFormatter(LOGFORMAT)
stream = logging.StreamHandler()
stream.setLevel(LOG_LEVEL)
stream.setFormatter(formatter)
logger = logging.getLogger('text-sender')
logger.setLevel(LOG_LEVEL)
logger.addHandler(stream)

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()
receivers = 0






class Worker(object):

    def __init__(self):
        self.socketio = socketio
        self.switch = True

    def background_thread(self):
        """Example of how to send server generated events to clients."""
        logger.info('stream started')
        self.switch = True
        count = 0
        name = 'S_0:Trajectory:Rlist'
        redis = RWrapper()
        size = redis.get_size(name)
        while self.switch:
            item = redis.get_item_str(name, size - 1)
            if item:
                count += 1
                self.socketio.emit('text_stream',
                                   {'data': item, 'count': count},
                                   namespace='/test')
                size += 1
            else:
                if redis.get_size(name) > size + 100:
                    size = redis.get_size(name)
                self.socketio.sleep(1)

    def stop(self):
        """
        stop the loop
        """
        self.switch = False


worker = Worker()


@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)


@socketio.on('disconnect_request', namespace='/test')
def disconnect_request():
    @copy_current_request_context
    def can_disconnect():
        disconnect()

    session['receive_count'] = session.get('receive_count', 0) + 1
    # for this emit we use a callback function
    # when the callback function is invoked we know that the message has been
    # received and it is safe to disconnect
    emit('my_response',
         {'data': 'Disconnected!', 'count': session['receive_count']},
         callback=can_disconnect)


@socketio.on('my_ping', namespace='/test')
def ping_pong():
    emit('my_pong')


@socketio.on('connect', namespace='/test')
def test_connect():
    global thread, receivers
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(worker.background_thread)
    receivers += 1
    emit('my_response', {'data': 'Connected', 'count': 0})


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    global thread, receivers
    logger.info('Client disconnected {}'.format(request.sid))
    receivers -= 1
    if receivers <= 0:
        logger.info('stopping stream')
        worker.stop()
        thread = None


if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=8060)
