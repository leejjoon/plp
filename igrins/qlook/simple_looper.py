import logging


class SimpleWorker(object):
    def __init__(self):
        self.status = None

    def init(self):
        self.status = "init"
        return self.status

    def do_task(self, taskname, msg):
        print(taskname, msg)


class LooperBase(object):
    def __init__(self, quit_event,
                 on_task, on_init=None):

        self.quit_event = quit_event

        self.on_task = on_task
        self.on_init = on_init
        self.init_object = None

    def recv(self):
        raise RuntimeError("derived class should implement this method")

    def reply(self, r):
        pass

    def loop(self):
        last_msg = None
        do_loop = 5
        while do_loop:
            if self.quit_event.is_set():
                break

            logging.warn("starting loop")
            if self.on_init:
                self.init_object = self.on_init()

            try:
                while True:
                    if last_msg is not None:
                        msg = last_msg
                    else:
                        print("waiting rpc_queue")
                        msg = self.recv()

                    last_msg = msg.copy()

                    print("process msg")
                    if self.quit_event.is_set() or (msg["_task"] == "quit"):
                        do_loop = 0
                        self.reply(None)

                        break
                    else:
                        print("process task")
                        taskname = msg.pop("_task")
                        r = self.on_task(taskname, msg)
                        self.reply(r)

                    last_msg = None

            except:
                import traceback
                traceback.print_exc()
                do_loop -= 1

        logging.warn("out of loop")


class Looper(LooperBase):
    def __init__(self, rpc_queue, quit_event,
                 on_task, on_init=None):

        self.rpc_queue = rpc_queue

        LooperBase.__init__(self, quit_event,
                            on_task, on_init=on_init)

    def recv(self):
        return self.rpc_queue.get()


def test():
    from threading import Thread, Event
    from queue import Queue

    print("starting")
    rpc_queue = Queue()
    quit_event = Event()

    sftp_poller = SimpleWorker()
    looper = Looper(rpc_queue, quit_event,
                    on_task=sftp_poller.do_task, on_init=sftp_poller.init)
    t = Thread(target=looper.loop)

    t.start()

    import time
    print("sleeping")
    time.sleep(1)
    print("task")
    rpc_queue.put(dict(_task="upload"))

    print("sleeping")
    time.sleep(1)
    rpc_queue.put(dict(_task="quit"))
    print("quit")
    t.join()
    print("joined")


if __name__ == "__main__":
    test()
