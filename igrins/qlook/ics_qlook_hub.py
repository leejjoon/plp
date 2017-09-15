import os
import signal
import curio
from curio.zmq import ZMQSelector
# from curio import run
import curio.zmq as zmq
from ics_port import get_connect_url
import json

import threading
from upload2fb import FailSafeUploader, get_firebase_default


async def loop_zmq(msg_queue):
    ctx = zmq.Context()
    sock = ctx.socket(zmq.SUB)

    sub_url = get_connect_url("sub")
    sock.connect(sub_url)
    sock.subscribe("obs-log")

    while True:
        print("waiting")
        _ = await sock.recv()
        topic, messagedata = _.split(b"\x00")

        if messagedata == b'exit':
            break

        r = json.loads(json.loads(messagedata)["msg"])

        await msg_queue.put(r)
        # print('Got:', json.loads(msg))

    # to communicate with fb uploader


# Entry point for curio
async def mainloop():

    msg_queue = curio.UniversalQueue()
    quit_event = curio.UniversalEvent()

    parent = "NextTarget"
    uploader = FailSafeUploader(msg_queue, quit_event,
                                get_firebase_default)
    uploader_thread = threading.Thread(target=uploader.upload,
                                       args=(parent,))

    uploader_thread.start()

    zmqloop = await curio.spawn(loop_zmq(msg_queue))

    goodbye = curio.SignalEvent(signal.SIGINT, signal.SIGTERM)
    await goodbye.wait()

    print("stopping fb uploader")

    await quit_event.set()
    await msg_queue.put(dict(_task="quit"))

    await curio.run_in_thread(uploader_thread.join)

    try:
        await zmqloop.cancel()

    except:
        import traceback
        traceback.print_exc()


def main():
    curio.run(mainloop(), selector=ZMQSelector())


if __name__ == "__main__":
    watchroot = "./watched"
    db_parent = "PROCESSED_test"
    main()
