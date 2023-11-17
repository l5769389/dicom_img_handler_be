import copy
import math

import numpy as np

from config import config
from helper.draw_helper import draw_helper
from PIL import Image, ImageDraw


class MeasureLayer(draw_helper):
    def __init__(self, base_info, view_type):
        self.transfer = {
            'offset_x': 0,
            'offset_y': 0,
            'zoom': 1,
            'rotate': 0,
            'flip': []
        }
        self.transfer_matrix = None
        self.draw_image = None
        self.drawer = None
        # measure的信息，已经完成的
        self.measure_info = {}
        # 正在绘制中的
        self.measuring_info = self.get_init_measuring_info()
        # 绘图层采用的坐标系.默认情况下是：右向是x的正方向， 下向是y轴的正方向。
        # self.coordinate_direction = {
        #     "x": 1,
        #     "y": 2
        # }
        self.base_info = base_info
        self.view_type = view_type

    def update_transfer(self, new_dict):
        self.transfer.update(new_dict)
        self.update_measure_img_after_transfer()

    # dicom影像发生了视图的翻转后。调转绘制测量图层的坐标系。
    # def update_coordinate(self, new_coordinate):
    #     self.coordinate_direction = new_coordinate

    def update_measure_img_after_transfer(self):
        current_slice = self.get_current_slice_by_view_type()
        measures = self.measure_info.get(current_slice, [])
        x_y_switch, sign_x, sign_y = self.get_coord()

        current_offset_x = -self.transfer['offset_x'] / self.transfer['zoom']
        current_offset_y = -self.transfer['offset_y'] / self.transfer['zoom']

        current_matrix_offset_x = sign_x * current_offset_x if x_y_switch is False else sign_y * current_offset_y
        current_matrix_offset_y = sign_y * current_offset_y if x_y_switch is False else sign_x * current_offset_x
        current_zoom = 1 / self.transfer['zoom']
        current_flip = self.transfer['flip']
        current_rotate = self.transfer['rotate']
        width, height = self.get_bg_size()
        c0 = int(width // 2)
        c1 = int(height // 2)
        for measure in measures:
            points = measure['points']
            pre_offset_x = measure['offset_x']
            pre_offset_y = measure['offset_y']
            pre_matrix_offset_x = sign_x * pre_offset_x if x_y_switch is False else sign_y * pre_offset_y
            pre_matrix_offset_y = sign_y * pre_offset_y if x_y_switch is False else sign_x * pre_offset_x
            pre_zoom = measure['zoom']
            pre_flip = measure['flip']
            pre_rotate = measure['rotate']
            arr = []
            pre_matrix = [
                [pre_zoom, 0, c0 * (1 - pre_zoom) - pre_matrix_offset_x],
                [0, pre_zoom, c1 * (1 - pre_zoom) - pre_matrix_offset_y],
                [0, 0, 1]
            ]
            m1 = np.linalg.inv(pre_matrix)
            m2 = [
                [current_zoom, 0, c0 * (1 - current_zoom) - current_matrix_offset_x],
                [0, current_zoom, c1 * (1 - current_zoom) - current_matrix_offset_y],
                [0, 0, 1]
            ]
            m = np.dot(m2, m1)
            for each_point in points:
                x0 = each_point[0]
                y0 = each_point[1]
                # 先变换回原来的坐标，再变换为最新的坐标。
                x_after, y_after, _ = np.dot(m, np.array([x0, y0, 1]))
                if ('hor' in current_flip) ^ ('hor' in pre_flip):
                    x_after = 2 * c0 - x_after
                elif ('ver' in current_flip) ^ ('ver' in pre_flip):
                    y_after = 2 * c1 - y_after
                rotate_angle_rad = math.radians(current_rotate - pre_rotate)
                if rotate_angle_rad != 0:
                    c, s = np.cos(rotate_angle_rad), np.sin(rotate_angle_rad)
                    rotate_matrix = np.array(((c, s), (-s, c)))
                    new_point = np.array([[x_after - c0], [y_after - c1]])
                    new_point = rotate_matrix.dot(new_point)
                    x_after = new_point[0][0] + c0
                    y_after = new_point[1][0] + c1
                arr.append((x_after, y_after))
            measure.update({
                'points': arr,
                'offset_x': current_offset_x,
                'offset_y': current_offset_y,
                'zoom': current_zoom,
                'flip': copy.deepcopy(current_flip),
                'rotate': current_rotate
            })

    def get_coord(self):
        sign_x = 1
        sign_y = 1
        x_y_switch = False
        coord = self.base_info.coordinate_direction[self.view_type]
        print(coord)
        if coord['x'] == 0:
            x_y_switch = True
            sign_x = -1
        elif coord['x'] == 1:
            sign_x = 1
        elif coord['x'] == 2:
            x_y_switch = True
            sign_x = 1
        elif coord['x'] == 3:
            sign_x = -1

        if coord['y'] == 0:
            sign_y = -1
        elif coord['y'] == 1:
            x_y_switch = True
            sign_y = 1
        elif coord['y'] == 2:
            sign_y = 1
        elif coord['y'] == 3:
            x_y_switch = True
            sign_y = -1
        return x_y_switch, sign_x, sign_y

    def get_bg_size(self):
        target_w = self.base_info.bg[self.view_type]['width']
        target_h = self.base_info.bg[self.view_type]['height']
        return target_w, target_h

    def create_layer(self):
        width, height = self.get_bg_size()
        self.draw_image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        self.drawer = ImageDraw.Draw(self.draw_image)

    def get_drew_img(self):
        self.create_layer()
        self.draw_measure(self.drawer)
        return self.draw_image

    def draw_img(self, action_type, position, sub_op_type):
        drawing = self.measuring_info
        status = drawing['status']
        drawing_type = drawing['type']
        if action_type == 'down':
            print('down')
            return
        elif action_type == 'move':
            print('move')
            return
        elif action_type == 'drag':
            print('drag')
            self.editing_or_creating_point(drawing, position, sub_op_type, status)
        elif action_type == 'up':
            self.check_finish_draw(drawing_type, drawing, position)
        elif action_type == 'click':
            print('click')
            self.check_click_which(position)

    def draw_measure(self, drawer):
        measuring = self.measuring_info
        current_slice = self.get_current_slice_by_view_type()
        measures = self.measure_info.get(current_slice, [])
        # 绘制已经完成的点
        drawer.rectangle((0, 0, self.draw_image.width, self.draw_image.height), fill=(0, 0, 0, 0))
        if len(measures) > 0:
            for measure in measures:
                self.draw_shapes(drawer, measure, 'finish')
        # 绘制未完成的点
        self.draw_shapes(drawer, measuring, measuring['status'])

    def editing_or_creating_point(self, drawing, position, sub_op_type, status):
        drawing_points = drawing['points']
        editing_index = drawing['editing_index']
        drawing_type = drawing['type']
        if status == 'creating':
            self.check_need_update_last_point(drawing, position, sub_op_type)
        elif status == 'editing':
            # 判断drag发生在哪个区域
            if editing_index == -2:
                self.check_down_in_which_point(drawing, position)
            # drag的区域为：整体拖动
            elif editing_index == -1:
                self.move_editing_img(drawing, position, drawing_type)
            # drag的区域为：拖动拐点
            else:
                self.update_editing_point(drawing, position)
                desc = self.calc_desc(drawing_points, drawing_type)
                drawing['desc'] = desc

    def check_finish_draw(self, sub_op_type, drawing, position):
        drawing_points = drawing['points']
        drawing['editing_index'] = -2
        self.pre_move_position = None
        # 异常状态，直接重置
        if len(drawing_points) == 1:
            self.reset_drawing_points()
            return
        if sub_op_type == 'line':
            # 两个点说明完成了线段
            if len(drawing_points) == 2:
                print('finish line')
                self.move_measuring_to_measured()
        elif sub_op_type == 'angle':
            if len(drawing_points) == 3:
                print('finish angle')
                self.move_measuring_to_measured()
            else:
                self.add_new_point_to_drawing(drawing_points, position, sub_op_type)
        elif sub_op_type == 'rectangle' or sub_op_type == 'ellipse':
            if len(drawing_points) == 5:
                print('finish rect/ ellipse')
                self.move_measuring_to_measured()

    def check_need_update_last_point(self, drawing, position, sub_op_type):
        drawing_points = drawing['points']
        if len(drawing_points) == 0:
            drawing_points = drawing_points + [position]
        else:
            if sub_op_type == 'line':
                if len(drawing_points) == 0:
                    return False
                if len(drawing_points) == 1:
                    drawing_points = drawing_points + [position]
                else:
                    drawing_points = drawing_points[:-1] + [position]
            elif sub_op_type == 'angle':
                if len(drawing_points) <= 1:
                    drawing_points = drawing_points + [position]
                else:
                    drawing_points = drawing_points[:-1] + [position]
            elif sub_op_type == 'rectangle' or sub_op_type == 'ellipse':
                if len(drawing_points) == 0:
                    drawing_points = drawing_points + [position]
                else:
                    x0 = drawing_points[0][0]
                    y0 = drawing_points[0][1]
                    x = position[0]
                    y = position[1]
                    point0 = (x0, y0)
                    point1 = (x, y0)
                    point2 = (x, y)
                    point3 = (x0, y)
                    if len(drawing_points) == 1:
                        # 添加整个矩形
                        drawing_points = drawing_points + [point1, point2, point3, point0]
                    else:
                        # 更新后四个
                        drawing_points = drawing_points[:-4] + [point1, point2, point3, point0]
        desc = self.calc_desc(drawing_points, sub_op_type)
        self.update_drawing_points({
            "type": sub_op_type,
            "points": drawing_points,
            "desc": desc,
            "status": 'creating',
            'zoom': 1 / self.transfer['zoom'],
            'offset_x': -self.transfer['offset_x'] / self.transfer['zoom'],
            'offset_y': -self.transfer['offset_y'] / self.transfer['zoom'],
            'flip': copy.deepcopy(self.transfer['flip']),
            'rotate': self.transfer['rotate']
        })

    def calc_desc(self, drawing_points, sub_op_type):
        desc = ''
        try:
            if sub_op_type == 'line':
                desc = self.calc_distance()
            elif sub_op_type == 'angle' and len(drawing_points) == 3:
                desc = self.calc_angle()
            elif sub_op_type == 'rectangle' or sub_op_type == 'ellipse':
                desc = self.calc_shape_info(sub_op_type)
        except Exception as e:
            print(e)
        return desc

    def check_click_which(self, position):
        drawing = self.measuring_info
        current_slice = self.get_current_slice_by_view_type()
        measures = self.measure_info.get(current_slice, [])
        hit_flag = self.check_down_in_which(position, drawing, measures)
        if not hit_flag:
            self.move_measuring_to_measured()

    def check_down_in_which_point(self, drawing, position):
        drawing_points = drawing['points']
        dragging_index = -1
        for index, each_point in enumerate(drawing_points):
            delta_x = position[0] - each_point[0]
            delta_y = position[1] - each_point[1]
            distance = math.sqrt(delta_x ** 2 + delta_y ** 2)
            if distance <= config.judge_click_which_point_radius:
                dragging_index = index
                break
        drawing['editing_index'] = dragging_index

    def move_editing_img(self, drawing, position, sub_op_type):
        # 如果坐标，在编辑点，那么是拖动四角
        # 如果不在编辑点， 那么整体移动
        drawing_points = drawing['points']
        if self.pre_move_position is not None:
            offset_x = position[0] - self.pre_move_position[0]
            offset_y = position[1] - self.pre_move_position[1]
            ans = []
            for point in drawing_points:
                list_point = list(point)
                list_point[0] = list_point[0] + offset_x
                list_point[1] = list_point[1] + offset_y
                ans.append(tuple(list_point))
            drawing_points = ans
            desc = drawing['desc']
            self.update_drawing_points({
                "type": sub_op_type,
                "points": drawing_points,
                "desc": desc,
                "status": 'editing'
            })
        self.pre_move_position = position

    def update_drawing_points(self, new_dict):
        self.measuring_info.update(new_dict)

    def get_init_measuring_info(self):
        return {
            "type": '',
            "points": [],
            "desc": '',
            "status": 'creating',  # creating, editing, finish
            "editing_index": -2,  # 如果是在editing状态，来记录当前正在移动的是哪个边界点. -2表示初始状态 -1 表示移动整体， 0~ 表示具体哪个点
            "offset_x": 0,
            "offset_y": 0,
            "zoom": 1,
            'flip': [],
            'rotate': 0
        }

    def reset_drawing_points(self):
        self.measuring_info = self.get_init_measuring_info()

    def reset_measures(self):
        current_slice = self.get_current_slice_by_view_type()
        self.measure_info[current_slice] = []

    def update_editing_point(self, drawing, position):
        editing_index = drawing['editing_index']
        drawing_type = drawing['type']
        if self.pre_move_position is not None:
            offset_x = position[0] - self.pre_move_position[0]
            offset_y = position[1] - self.pre_move_position[1]
            if drawing_type == 'line' or drawing_type == 'angle':
                editing_point = drawing['points'][editing_index]
                drawing['points'][editing_index] = (editing_point[0] + offset_x, editing_point[1] + offset_y)
            elif drawing_type == 'rectangle' or drawing_type == 'ellipse':
                editing_point = drawing['points'][editing_index]
                drawing['points'][editing_index] = (editing_point[0] + offset_x, editing_point[1] + offset_y)
                if editing_index == 0:
                    drawing['points'][1] = (drawing['points'][1][0], drawing['points'][1][1] + offset_y)
                    drawing['points'][3] = (drawing['points'][3][0] + offset_x, drawing['points'][3][1])
                    drawing['points'][4] = drawing['points'][editing_index]
                elif editing_index == 1:
                    drawing['points'][0] = (drawing['points'][0][0], drawing['points'][0][1] + offset_y)
                    drawing['points'][2] = (drawing['points'][2][0] + offset_x, drawing['points'][2][1])
                    drawing['points'][4] = drawing['points'][0]
                elif editing_index == 2:
                    drawing['points'][1] = (drawing['points'][1][0] + offset_x, drawing['points'][1][1])
                    drawing['points'][3] = (drawing['points'][3][0], drawing['points'][3][1] + + offset_y)
                elif editing_index == 3:
                    drawing['points'][0] = (drawing['points'][0][0] + offset_x, drawing['points'][0][1])
                    drawing['points'][4] = drawing['points'][0]
                    drawing['points'][2] = (drawing['points'][2][0], drawing['points'][2][1] + offset_y)
        self.pre_move_position = position

    def move_measuring_to_measured(self):
        if len(self.measuring_info['points']) == 0:
            return
        current_index = self.get_current_slice_by_view_type()
        measured_info = self.measure_info.setdefault(current_index, [])
        self.measure_info[current_index] = measured_info + [
            copy.deepcopy(self.measuring_info)]
        self.reset_drawing_points()

    def get_current_slice_by_view_type(self):
        return self.base_info.latest_op_img_info[self.view_type]['slice']

    def add_new_point_to_drawing(self, drawing_points, position, sub_op_type):
        if sub_op_type == 'line' or sub_op_type == 'angle':
            drawing_points = drawing_points + [position]
        elif sub_op_type == 'rectangle' or sub_op_type == 'ellipse':
            if len(drawing_points) == 0:
                drawing_points = drawing_points + [position]
            else:
                x0 = drawing_points[0][0]
                y0 = drawing_points[0][1]
                x = position[0]
                y = position[1]
                point0 = (x0, y0)
                point1 = (x, y0)
                point2 = (x, y)
                point3 = (x0, y)
                drawing_points = drawing_points + [point1, point2, point3, point0]
        self.update_drawing_points({
            "type": sub_op_type,
            "points": drawing_points
        })

    def calc_distance(self):
        drawing = self.measuring_info
        drawing_points = drawing['points']
        if len(drawing_points) < 2:
            return
        return str(self.get_distance_by_two_points(drawing_points[0], drawing_points[1])) + 'CM'

    def get_distance_by_two_points(self, point0, point1):
        delta_x = abs(point0[0] - point1[0])
        delta_y = abs(point0[1] - point1[1])
        spacing = self.base_info.spacing[self.view_type]
        x_mm_per_px, y_mm_per_px = spacing
        scale = self.transfer['zoom']
        distance = math.sqrt((delta_x * x_mm_per_px * scale) ** 2 + (delta_y * y_mm_per_px * scale) ** 2)
        return round(distance / 10, 2)

    def calc_angle(self):
        drawing = self.measuring_info
        drawing_points = drawing['points']
        if len(drawing_points) != 3:
            return
        vector1 = tuple(map(lambda x, y: x - y, drawing_points[0], drawing_points[1]))
        vector2 = tuple(map(lambda x, y: x - y, drawing_points[2], drawing_points[1]))
        spacing = self.base_info.spacing[self.view_type]
        actual_vector1 = tuple(vector1[i] * spacing[i] for i in range(len(vector1)))
        actual_vector2 = tuple(vector2[i] * spacing[i] for i in range(len(vector1)))
        return str(self.calc_vector_angle(actual_vector1, actual_vector2))

    def calc_shape_info(self, type):
        drawing = self.measuring_info
        drawing_points = drawing['points']
        img_ct_arr = self.base_info.get_current_index_ct_value_arr(self.view_type, 'transformed')
        if len(drawing_points) <= 3:
            return
        w = self.get_distance_by_two_points(drawing['points'][0], drawing['points'][1])
        h = self.get_distance_by_two_points(drawing['points'][1], drawing['points'][2])
        x = int(drawing['points'][0][0])
        x_1 = int(drawing['points'][1][0])

        y = int(drawing['points'][0][1])
        y_1 = int(drawing['points'][2][1])
        start_x = min(x, x_1)
        end_x = max(x, x_1)

        start_y = min(y, y_1)
        end_y = max(y, y_1)
        w_str = str(w) + 'CM'
        h_str = str(h) + 'CM'
        area = 0
        mean = 0
        min_val = 0
        max_val = 0
        stddev = 0
        if type == 'rectangle':
            area = np.around(w * h)
            drawing_arr = img_ct_arr[start_y:end_y + 1, start_x:end_x + 1]
            mean = np.around(np.mean(drawing_arr), 2)
            min_val = np.around(np.min(drawing_arr))
            max_val = np.around(np.max(drawing_arr))
            stddev = np.around(np.std(drawing_arr))
        elif type == 'ellipse':
            area = np.around(np.pi * w * h)
            drawing_arr = img_ct_arr[start_y:end_y + 1, start_x:end_x + 1]
            ellipsis_arr = self.get_rectangle_inner_ellipse(drawing_arr)
            mean = np.around(np.mean(ellipsis_arr))
            min_val = np.around(np.min(ellipsis_arr))
            max_val = np.around(np.max(ellipsis_arr))
            stddev = np.around(np.std(ellipsis_arr))
        area_str = str(area) + 'CM²'
        ans = [
            {
                'attr': 'Mean',
                'value': mean
            },
            {
                'attr': 'Min',
                'value': min_val
            },
            {
                'attr': 'Max',
                'value': max_val
            },
            {
                'attr': 'StdDev',
                'value': stddev
            },
            {
                'attr': 'Area',
                'value': area_str
            },
            [
                {
                    'attr': 'W',
                    'value': w_str
                },
                {
                    'attr': 'H',
                    'value': h_str
                },
            ]
        ]
        ans.reverse()
        return ans

    def get_rectangle_inner_ellipse(self, rectangle_matrix):
        h, w = rectangle_matrix.shape
        x0, y0 = h // 2, w // 2
        arr = rectangle_matrix
        a = max(h, w)
        b = min(h, w)
        indices = np.where(
            ((np.arange(arr.shape[0])[:, None] - x0) ** 2 / a ** 2 + (
                    np.arange(arr.shape[1]) - y0) ** 2 / b ** 2) <= 1)
        return arr[indices]
