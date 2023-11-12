import json
import time

from layers.index import GenerateImg


class HandleMsg(GenerateImg):
    def __init__(self, send_queue, pause_event, child_conn):
        super().__init__()
        self.data = ''
        self.preview_img_loading_start = False
        self.send_queue = send_queue
        self.pause_event = pause_event
        self.child_conn = child_conn

    def resolve_msg(self, data):
        self.data = json.loads(data)
        if 'opType' in self.data.keys():
            op_type = self.data['opType']
            view_type = self.data['type']
            if op_type == 'window':
                x = self.data['x']
                y = self.data['y']
                self.handle_adjust_window(view_type, x, y)
            elif op_type == 'pan':
                x = self.data['x']
                y = self.data['y']
                self.handle_pan(view_type, x, y)
            elif op_type == 'getImg':
                self.load_img(view_type)
            elif op_type == 'zoom':
                zoom = self.data['zoom']
                self.handle_zoom(view_type, zoom)
            elif op_type == 'move_scroll':
                x = self.data['x']
                y = self.data['y']
                self.handle_move_scroll(view_type, x, y)
            elif op_type == 'scroll':
                scroll = self.data['scroll']
                self.handle_scroll(view_type, scroll)
            elif op_type == 'draw':
                sub_op_type = self.data['subOpType']
                x = self.data['x']
                y = self.data['y']
                action_type = self.data['actionType']
                self.handle_draw(view_type, sub_op_type, (x, y), action_type)
            elif op_type == 'clearLine':
                self.clearOneLine(view_type)
            elif op_type == 'clearAllLine':
                self.clearAllLine(view_type)
            elif op_type == 'clearAllRotate':
                self.clearAllRotate(view_type)
            elif op_type == 'reset':
                view_type = self.data['type']
                self.reset(view_type)
            elif op_type == 'resize':
                view_type = self.data['type']
                self.resize(view_type)
            elif op_type == 'mouseover':
                view_type = self.data['type']
                self.calc_current_posi(view_type)
            elif op_type == 'play':
                self.play()
            elif op_type == 'hor flip':
                self.hor_flip()
            elif op_type == 'ver flip':
                self.ver_flip()
            elif op_type == 'counterClockwise90':
                self.rotate(90)
            elif op_type == 'clockwise90':
                self.rotate(-90)
            elif op_type == 'bw':
                self.pseudo_color(view_type, 'bw')
            elif op_type == 'rainbow':
                self.pseudo_color(view_type, 'rainbow')
            elif op_type == 'get_3d':
                self.get_3d()

    def load_img(self, view_type):
        if view_type == 'preview':
            self.load_preview()
        elif view_type == 'sag' or view_type == 'ax' or view_type == 'cor':
            self.load_mpr_single(view_type)
        elif view_type == 'mpr':
            self.load_mpr()

    def load_preview(self):
        msg = self.get_preview_img(self.data)
        self.send_msg(msg)
        self.preview_img_loading_start = True

    def load_mpr(self):
        msg = self.init_mpr(self.data['size'])
        self.send_msg(msg)

    def load_mpr_single(self, view_type):
        pass

    def handle_adjust_window(self, view_type, x, y):
        if view_type == 'preview':
            msg = self.adjust_window_single(x, y)
        else:
            msg = self.adjust_window_multi(x, y)
        self.send_msg(msg)

    def handle_pan(self, view_type, x, y):
        msg = self.pan_img(view_type, x, y)
        self.send_msg(msg)

    def handle_zoom(self, view_type, zoom):
        msg = self.zoom_img(view_type, zoom)
        self.send_msg(msg)

    def handle_scroll(self, view_type, scroll):
        msg = self.scroll_img(view_type, scroll)
        self.send_msg(msg)

    # mpr移动十字线
    def handle_move_scroll(self, view_type, x, y):
        msg = self.move_scroll_img(view_type, x, y)
        self.send_msg(msg)

    def handle_draw(self, view_type, sub_op_type, position, action_type):
        msg = self.draw_various_img(view_type, sub_op_type, position, action_type)
        self.send_msg(msg)

    def clearOneLine(self, view_type):
        msg = self.clear_choosing_img(view_type)
        self.send_msg(msg)

    def clearAllLine(self, view_type):
        msg = self.clear_all_draw_img(view_type)
        self.send_msg(msg)

    def clearAllRotate(self, view_type):
        msg = self.clear_all_rotate(view_type)
        self.send_msg(msg)

    def reset(self, view_type):
        msg = self.reset_img(view_type)
        self.send_msg(msg)

    def resize(self, view_type):
        if view_type == 'mpr':
            msg = self.resize_multi_view()
        else:
            msg = self.resize_single_view(view_type, self.data['size'])
        if msg is not None:
            self.send_msg(msg)

    def calc_current_posi(self, view_type):
        if not self.preview_img_loading_start:
            return
        x = self.data['x']
        y = self.data['y']
        msg = self.calc_current_position(view_type, x, y)
        if msg is not None:
            self.send_msg(msg)

    def play(self):
        view_type = self.data['type']
        interval = int(self.data['interval']) / 1000
        self.pause_event.clear()
        while True:
            if self.pause_event.is_set():
                break
            self.timer_play(view_type)
            time.sleep(interval)

    def timer_play(self, view_type):
        msg = self.loop_play(view_type)
        self.send_msg(msg)

    def send_msg(self, msg):
        if msg is not None:
            str = json.dumps(msg)
            self.send_queue.put(str)

    def hor_flip(self):
        view_type = self.data['type']
        msg = self.flip_img(view_type, 'hor')
        self.send_msg(msg)

    def ver_flip(self):
        view_type = self.data['type']
        msg = self.flip_img(view_type, 'ver')
        self.send_msg(msg)

    def rotate(self, angle):
        view_type = self.data['type']
        msg = self.rotate_img(view_type, angle)
        self.send_msg(msg)

    def pseudo_color(self, view_type, pseudo_color_type):
        view_type = self.data['type']
        if view_type == 'preview':
            view_type = 'preview'
        else:
            view_type = 'mpr'
        msg = self.change_color_space(view_type, pseudo_color_type)
        self.send_msg(msg)

    def get_3d(self):
        ans = self.get_3d_vti()
        self.child_conn.send(ans)
