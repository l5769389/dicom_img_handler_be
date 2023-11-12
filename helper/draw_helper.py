import copy
import math

import numpy as np

from config import config
from helper.DrawOnImg import Draw

every_line_offset = 20


class draw_helper:
    pre_move_position = None

    def calc_vector_angle(self, actual_vector1, actual_vector2):
        dot_product = np.dot(actual_vector1, actual_vector2)
        norm1 = np.linalg.norm(actual_vector1)
        norm2 = np.linalg.norm(actual_vector2)
        if norm1 * norm2 == 0:
            return None
        cosine_angle = dot_product / (norm1 * norm2)
        angle = np.arccos(cosine_angle)
        angle_degree = np.degrees(angle)
        return round(angle_degree, 2)

    def draw_shapes(self, drawer, each_shape, status,
                    ):
        points1 = each_shape['points']
        points = points1
        type = each_shape['type']
        desc = each_shape['desc']
        if type == 'line' or type == 'angle':
            for index, point in enumerate(points):
                if status == 'creating' or status == 'editing':
                    Draw.draw_circle(drawer, point[0], point[1])
                if index != len(points) - 1:
                    next_point = points[index + 1]
                    Draw.draw_line(drawer, point, next_point)
                elif len(points) > 1:
                    turn_point = points[1]
                    Draw.draw_text(drawer, desc, turn_point)
        elif type == 'ellipse':
            for index, point in enumerate(points):
                if status == 'creating' or status == 'editing':
                    Draw.draw_circle(drawer, point[0], point[1])
                    if index != len(points) - 1:
                        next_point = points[index + 1]
                        Draw.draw_line(drawer, point, next_point)
            if len(points) > 1:
                turn_point = points[1]
                # 0.003 ~ 0.005
                self.draw_multi_lines_text(drawer, desc, turn_point)

                p0 = points[0]
                p2 = points[2]
                left = (min(p0[0], p2[0]), min(p0[1], p2[1]))
                right = (max(p0[0], p2[0]), max(p0[1], p2[1]))
                Draw.draw_ellipse(drawer, [left, right])

        elif type == 'rectangle':
            for index, point in enumerate(points):
                if status == 'creating' or status == 'editing':
                    Draw.draw_circle(drawer, point[0], point[1])
                if index != len(points) - 1:
                    next_point = points[index + 1]
                    Draw.draw_line(drawer, point, next_point)
            if len(points) > 1:
                turn_point = points[1]
                self.draw_multi_lines_text(drawer, desc, turn_point)

    # zoom、pan的时候移动用户绘制的图像。
    def transfer_draw_img(self, points, total_offset_x, total_offset_y, total_zoom, center_x, center_y):
        arr = []
        for each_point in points:
            modify_list = list(each_point)
            modify_list[0] = int(1 / total_zoom * (modify_list[0] - center_x) + center_x + total_offset_x / total_zoom)
            modify_list[1] = int(1 / total_zoom * (modify_list[1] - center_y) + center_y + total_offset_y / total_zoom)
            modify_tuple = tuple(modify_list)
            arr.append(modify_tuple)
        return arr

    def draw_multi_lines_text(self, drawer, desc, start_point):
        if desc is None or len(desc) == 0:
            return
        ans = []
        for index, item in enumerate(desc):
            line = ''
            if type(item) == dict:
                key = item['attr']
                value = item['value']
                line = f'{key}: {value}'
            elif type(item) == list:
                for index1, item1 in enumerate(item):
                    key1 = item1['attr']
                    value1 = item1['value']
                    line = line + f' {key1}: {value1}'
            ans.append(line)
        for index1, line1 in enumerate(ans):
            current_posi = (int(start_point[0]), int(start_point[1] - every_line_offset * index1))
            Draw.draw_text(drawer, line1, current_posi)

    # 单次按下没有移动 判断在哪个图像中。如果在的话，着重显示。
    # 有foucs的 move则是在移动它
    # 按下有移动则是为了创建新的
    def check_down_in_which(self, position, drawing, measures):
        # 如果还有focu状态，那么说明还在针对特定的图像进行操作。
        # 没有focus 则说明要开始新的图像了。
        flag = False
        for index, measure_item in enumerate(measures):
            op_index = index
            flag = self.check_in(position, measure_item['type'], measure_item['points'])
            if flag:
                # 点击的在已有图形中，将点中的图像加入正在绘制中的。
                self.move_measured_to_measuring(op_index, drawing, measures)
                break
        return flag

    def move_measured_to_measuring(self, op_index, drawing, measures):
        pop0ne = measures.pop(op_index)
        if len(drawing['points']) > 0:
            self.move_measuring_to_measures(drawing, measures)
        drawing.update(pop0ne)
        drawing['status'] = 'editing'

    def move_measuring_to_measures(self, drawing, measures):
        measures.append(copy.deepcopy(drawing))
        drawing.update({
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
        })

    def check_in(self, position, measure_type, points):
        x, y = position
        if measure_type == 'line':
            distance = self.calc_point_to_line_distance(position, points[0], points[1])
            if distance <= config.judge_click_which_line_dis:
                return True
            return False
        elif measure_type == 'angle':
            distance1 = self.calc_point_to_line_distance(position, points[0], points[1])
            distance2 = self.calc_point_to_line_distance(position, points[1], points[2])
            if distance1 <= config.judge_click_which_line_dis or distance2 <= config.judge_click_which_line_dis:
                return True
            return False
        elif measure_type == 'rectangle' or measure_type == 'ellipse':
            x1, y1 = points[0]
            x2, y2 = points[1]
            x3, y3 = points[2]
            x4, y4 = points[3]
            cross1 = (x - x1) * (y2 - y1) - (y - y1) * (x2 - x1)
            cross2 = (x - x2) * (y3 - y2) - (y - y2) * (x3 - x2)
            cross3 = (x - x3) * (y4 - y3) - (y - y3) * (x4 - x3)
            cross4 = (x - x4) * (y1 - y4) - (y - y4) * (x1 - x4)
            if (cross1 >= 0 and cross2 >= 0 and cross3 >= 0 and cross4 >= 0) or \
                    (cross1 <= 0 and cross2 <= 0 and cross3 <= 0 and cross4 <= 0):
                return True
            else:
                return False

    # c到 ab连线的距离
    def calc_point_to_line_distance(self, c, a, b):
        ab = (b[0] - a[0], b[1] - a[1])
        ac = (c[0] - a[0], c[1] - a[1])
        if ab == (0, 0) or ac == (0, 0):
            return 0
        cross_product = ab[0] * ac[1] - ab[1] * ac[0]
        distance = abs(cross_product) / math.sqrt(ab[0] ** 2 + ab[1] ** 2)
        return distance
