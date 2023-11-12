import multiprocessing

from ws.resolve_msg import HandleMsg


class ws_recv_msg_op(multiprocessing.Process):
    def __init__(self, ws_send_msg_queue, ws_recv_msg_queue, pause_event,child_conn):
        super().__init__()
        self.ws_send_msg_queue = ws_send_msg_queue
        self.ws_recv_msg_queue = ws_recv_msg_queue
        self.handle_msg = HandleMsg(ws_send_msg_queue, pause_event,child_conn)
        self.pause_event = pause_event

    def run(self):
        while True:
            while self.ws_recv_msg_queue.qsize() > 0:
                data = self.ws_recv_msg_queue.get()
                self.handle_msg.resolve_msg(data)

