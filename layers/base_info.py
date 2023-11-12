# 处理影像的基础信息，绘制线段等信息都放在不同的layers中。
import copy
import math
import os

import numpy as np

from helper.resolve_dicom_path import ResolvePath


class BaseInfo:
    def __init__(self):
        self.parent_path = ''
        self.resolve_path = ResolvePath()
        self.base_info = {
            "intercept": 0,
            "slope": 0,
            "spacing": [],
            "rows": 0,
            "columns": 0
        }
        # 用来计算每个点实时的value值。
        self.ct_value_arr_dict = {}
        self.latest_op_img_info = {}
        # 一张张dicom pixel数组
        self.dicoms = []
        self.volume = []
        self.spacing = {}
        self.total = {}
        self.get_base_info_flag = False
        self.ww_wl = {}
        self.transfer = {}
        self.init_zoom = {}
        # 前端显示的长宽比
        self.aspects = {}
        # mpr 影像中各个视图的中心点当前位置，来告知前端
        self.center_posi = {}
        self.bg = {}
        # 坐标系的方向，默认为x向右，y向下,实际上用到的就是右方向是哪个？ 上方向是哪个？
        self.coordinate_direction = {}
        # 记录了在每一张图片中真正影像部分的四个拐点的坐标
        self.corner_info = {}
        self.dicom_img_direction = {
            "init": None,
            "transformed": None
        }
        for item in ['preview', 'sag', 'cor', 'ax']:
            self.corner_info[item] = {
                "init": None,
                "transformed": None
            }
            self.init_zoom[item] = 1
            self.spacing = {
                item: []
            }
            self.center_posi[item] = ''
            self.total = {
                item: 0
            }
            self.latest_op_img_info[item] = {
                'slice': 0,
            }
            # 0123 表示：上、右、下、左
            self.coordinate_direction[item] = {
                "x": 1,
                "y": 2
            }
            self.transfer[item] = {
                'offset_x': 0,
                'offset_y': 0,
                'zoom': 1,
                'rotate': 0,
                'flip': [],
            }
            self.ct_value_arr_dict[item] = {
                "init": None,
                "transformed": None
            }
        for item in ['preview', 'mpr']:
            self.ww_wl[item] = {
                "ww": 0,
                "wl": 0,
                "init": {
                    "ww": 0,
                    "wl": 0
                }
            }

    def init_base_info(self, dict):
        dicom_addr = dict['address']
        self.parent_path = os.path.dirname(dicom_addr)
        dicom = self.resolve_path.load_one(dicom_addr)
        self.dicoms.append(dicom)
        # 2.设置一些基础信息, 添加到dicoms数组中,方便后续使用
        self.set_base_info(dicom, dict)
        self.set_latest('preview', len(self.dicoms) - 1)

    def set_total(self, view_type, total):
        self.total[view_type] = total

    def set_base_info(self, dicom, dict):
        self.set_total('preview', len(self.dicoms) - 1)
        if self.get_base_info_flag:
            return
        aspect = dict['size']
        spacing = np.array([dicom.PixelSpacing[0], dicom.PixelSpacing[1], dicom.SliceThickness])
        self.spacing['preview'] = spacing[[0, 1]]
        self.spacing['cor'] = spacing[[0, 2]]
        self.spacing['ax'] = spacing[[0, 1]]
        self.spacing['sag'] = spacing[[0, 2]]
        self.set_img_direction(dicom)
        self.set_view_aspect('preview', aspect)
        self.base_info = {
            "intercept": dicom.RescaleIntercept,
            "slope": dicom.RescaleSlope,
            "spacing": spacing,
            "rows": dicom.Rows,
            "columns": dicom.Columns,
            "manufacturer": dicom.Manufacturer,
            "ex": dicom.ContentDate + dicom.ContentTime,
            'se': dicom.SeriesNumber,
            'mA': dicom.XRayTubeCurrent,
            'kV': dicom.KVP,
            'thickness': dicom.SliceThickness
        }
        if 'PixelSpacing' in dicom:
            self.spacing['preview'] = dicom.PixelSpacing
        if 'WindowWidth' in dicom and 'WindowCenter' in dicom:
            # 获取窗宽和窗位值
            window_width = dicom.WindowWidth
            window_center = dicom.WindowCenter
            self.ww_wl['preview'] = {
                "ww": window_width,
                "wl": window_center,
                "init": {
                    "ww": window_width,
                    "wl": window_center,
                }
            }
            self.ww_wl['mpr'] = {
                "ww": window_width,
                "wl": window_center,
                "init": {
                    "ww": window_width,
                    "wl": window_center,
                }
            }
        self.get_base_info_flag = True

    def set_img_direction(self, dicom):
        vector = dicom.ImageOrientationPatient
        x_vector = vector[:2]
        y_vector = vector[3:]
        l_r_direction = ['L', 'R']
        a_p_direction = ['A', 'P']
        if x_vector == [1, 0, 0]:
            direction_x = l_r_direction
        else:
            direction_x = a_p_direction

        if y_vector == [0, 1, 0]:
            direction_y = l_r_direction
        else:
            direction_y = a_p_direction
        self.dicom_img_direction = {
            "init": {
                "x": direction_x,
                "y": direction_y
            },
            "transformed": {
                "x": direction_x,
                "y": direction_y
            }
        }

    def set_latest(self, view_type, current_op_index):
        self.latest_op_img_info[view_type]['slice'] = current_op_index

    def set_view_aspect(self, view_type, dict):
        self.aspects[view_type] = dict
        self.set_bg(view_type)

    def set_bg(self, view_type):
        target_width = self.aspects[view_type]['width']
        target_height = self.aspects[view_type]['height']
        self.bg[view_type] = {
            "width": int(target_width),
            "height": int(target_height)
        }

    def get_recent_pixel_array(self, view_type):
        current_index = self.get_current_slice_index(view_type)
        return self.get_hu_array_by_slice(view_type, current_index)

    def get_current_slice_index(self, view_type):
        return int(self.latest_op_img_info[view_type]['slice'])

    def get_hu_array_by_slice(self, view_type, slice):
        if view_type == 'sag':
            pixel_array = self.volume[:, :, slice]
        elif view_type == 'cor':
            pixel_array = self.volume[:, slice, :]
        elif view_type == 'ax':
            pixel_array = self.volume[slice, :, :]
        elif view_type == 'preview':
            pixel_array = self.dicoms[slice].pixel_array
        return pixel_array

    def adjust_window(self, view_type, x, y):
        ww = self.ww_wl[view_type]['ww']
        wl = self.ww_wl[view_type]['wl']
        ww = ww + x
        wl = wl + y
        self.ww_wl[view_type]['ww'] = ww
        self.ww_wl[view_type]['wl'] = wl

    def set_coordinate(self, view_type, transfer_type):
        coordination = self.coordinate_direction[view_type]
        x_direction = coordination['x']
        y_direction = coordination['y']
        self.update_img_direction(transfer_type)
        if transfer_type == 'hor':
            coordination['x'] = self.flip_coordinate(x_direction)
        elif transfer_type == 'ver':
            coordination['y'] = self.flip_coordinate(y_direction)
        elif transfer_type == 'clockwise_rotate':
            coordination['x'] = self.rotate_coordinate(x_direction, 1)
            coordination['y'] = self.rotate_coordinate(y_direction, 1)
        elif transfer_type == 'counterclockwise_rotate':
            coordination['x'] = self.rotate_coordinate(x_direction, -1)
            coordination['y'] = self.rotate_coordinate(y_direction, -1)

    def update_img_direction(self, transfer_type):
        direction_x = self.dicom_img_direction['transformed']['x']
        direction_y = self.dicom_img_direction['transformed']['y']
        if transfer_type == 'hor':
            direction_y[0], direction_y[1] = direction_y[1], direction_y[0]
        elif transfer_type == 'ver':
            direction_x[0], direction_x[1] = direction_x[1], direction_x[0]
        elif transfer_type == 'clockwise_rotate':
            temp = direction_y[0]
            direction_y[0] = direction_x[0]
            direction_x[0] = direction_y[1]
            direction_y[1] = direction_x[1]
            direction_x[1] = temp
        elif transfer_type == 'counterclockwise_rotate':
            temp = direction_x[0]
            direction_x[0] = direction_y[0]
            direction_y[0] = direction_x[1]
            direction_x[1] = direction_y[1]
            direction_y[1] = temp
        print(direction_x)
        print(direction_y)

    def flip_coordinate(self, direction):
        # 原先是0方向（向上）那么就变为2（向下）
        flip_map = {
            0: 2,
            1: 3,
            2: 0,
            3: 1
        }
        return flip_map[direction]

    def rotate_coordinate(self, direction, sign):
        if sign > 0:
            rotate_map = {
                0: 1,
                1: 2,
                2: 3,
                3: 0
            }
        else:
            rotate_map = {
                0: 3,
                3: 2,
                2: 1,
                1: 0
            }
        return rotate_map[direction]

    def pan_img(self, view_type, x, y):
        total_zoom = self.transfer[view_type].get('zoom')
        # 前端传来的数据中：x为正表示向右，y为正表示向下。
        current_offset_x = int(total_zoom * x)
        current_offset_y = int(total_zoom * y)
        direction_dict = self.get_coordinate_direction(view_type)
        set_dict = {}
        # 先处理前端的垂直方向上的拖动，y变化的情况：
        if direction_dict['bottom'] == 'y':
            set_dict['offset_y'] = int(self.transfer[view_type]['offset_y'] + current_offset_y)
        elif direction_dict['bottom'] == '-y':
            set_dict['offset_y'] = int(self.transfer[view_type]['offset_y'] - current_offset_y)
        elif direction_dict['bottom'] == 'x':
            # offset_x 指的是在初始状态下。图像向右的偏移量
            # offset_y 指的是在初始状态下。图像向上的偏移量
            # 下方向对应的是坐标轴的x轴正方向。
            set_dict['offset_x'] = int(self.transfer[view_type]['offset_x'] + current_offset_y)
        elif direction_dict['bottom'] == '-x':
            set_dict['offset_x'] = int(self.transfer[view_type]['offset_x'] - current_offset_y)

        # 右向是x轴的正方向。
        if direction_dict['right'] == 'x':
            set_dict['offset_x'] = int(self.transfer[view_type]['offset_x'] + current_offset_x)
        elif direction_dict['right'] == '-x':
            set_dict['offset_x'] = int(self.transfer[view_type]['offset_x'] - current_offset_x)
        elif direction_dict['right'] == 'y':
            set_dict['offset_y'] = int(self.transfer[view_type]['offset_y'] + current_offset_x)
        elif direction_dict['right'] == '-y':
            set_dict['offset_y'] = int(self.transfer[view_type]['offset_y'] - current_offset_x)
        return self.update_transfer(view_type, set_dict)

    def zoom_img(self, view_type, zoom):
        update_dict = {
            'zoom': zoom
        }
        return self.update_transfer(view_type, update_dict)

    # 此时原先的x、y坐标系可能已经发生了翻转。此方法来获取最新的向右移动delta_x、向下移动delta_y。
    # 在坐标系翻转的情况下，实际移动的情况。
    def get_coordinate_direction(self, view_type):
        coordination = self.coordinate_direction[view_type]
        x_direction = coordination['x']
        y_direction = coordination['y']
        ans = {
            "bottom": 'y',
            "right": 'x',
        }
        if x_direction == 0:
            ans['bottom'] = '-x'
        elif x_direction == 1:
            ans['right'] = 'x'
        elif x_direction == 2:
            ans['bottom'] = 'x'
        elif x_direction == 3:
            ans['right'] = '-x'

        if y_direction == 0:
            ans['bottom'] = '-y'
        elif y_direction == 1:
            ans['right'] = 'y'
        elif y_direction == 2:
            ans['bottom'] = 'y'
        elif y_direction == 3:
            ans['right'] = '-y'
        return ans

    def update_transfer(self, view_type, update_dict):
        self.transfer[view_type].update(update_dict)
        return update_dict

    def scroll_img(self, view_type, scroll):
        current_slice = self.get_current_slice_index(view_type)
        want_slice = current_slice + scroll
        total_slice = self.total[view_type]
        actual_slice = np.clip(want_slice, 0, total_slice)
        self.set_latest(view_type, actual_slice)

    def flip_img(self, view_type, direction):
        total_flip = self.transfer[view_type]['flip']
        self.set_coordinate(view_type, transfer_type=direction)
        if len(total_flip) == 0:
            total_flip.append(direction)
        else:
            if direction in total_flip:
                total_flip.remove(direction)
            else:
                total_flip.append(direction)
        update_dict = {
            "flip": total_flip
        }
        return self.update_transfer(view_type, update_dict)

    def rotate_img(self, view_type, angle):
        if angle == 90:
            self.set_coordinate(view_type, transfer_type='counterclockwise_rotate')
        elif angle == -90:
            self.set_coordinate(view_type, transfer_type='clockwise_rotate')
        pre_total_rotate = self.transfer[view_type]['rotate']
        total_rotate1 = pre_total_rotate + angle
        total_rotate = math.copysign(1, total_rotate1) * (abs(total_rotate1) % 360)
        return self.update_transfer(view_type, {
            "rotate": total_rotate
        })

    def clear_all_rotate(self, view_type):
        self.reset_coordinate(view_type)
        return self.update_transfer(view_type, {
            "flip": [],
            "rotate": 0
        })

    def reset_coordinate(self, view_type):
        self.coordinate_direction[view_type] = {
            "x": 1,
            "y": 2
        }

    def reset(self, view_type):
        if view_type == 'preview':
            self.transfer[view_type] = {
                'offset_x': 0,
                'offset_y': 0,
                'zoom': 1,
                'rotate': 0,
                'flip': []
            }
            self.ww_wl[view_type]['ww'] = self.ww_wl[view_type]['init']['ww']
            self.ww_wl[view_type]['wl'] = self.ww_wl[view_type]['init']['wl']
            self.set_latest(view_type, len(self.dicoms))
        else:
            for item in ['mpr']:
                self.ww_wl[item]['ww'] = self.ww_wl[item]['init']['ww']
                self.ww_wl[item]['wl'] = self.ww_wl[item]['init']['wl']
            for item in ['sag', 'cor', 'ax']:
                self.transfer[item] = {
                    'offset_x': 0,
                    'offset_y': 0,
                    'zoom': 1,
                    'rotate': 0,
                    'flip': []
                }
            self.record_init_mpr()

    def record_init_mpr(self):
        ax_total, sag_total, cor_total = self.volume.shape

        self.set_total('sag', sag_total - 1)
        self.set_total('cor', cor_total - 1)
        self.set_total('ax', ax_total - 1)

        self.set_latest('sag', int(self.total['sag'] // 2))
        self.set_latest('ax', int(self.total['ax'] // 2))
        self.set_latest('cor', int(self.total['cor'] // 2))

    def loop_play(self, view_type):
        current = self.get_current_slice_index(view_type)
        total = self.total[view_type]
        next = current + 1
        if next > total:
            next = 0
        self.set_latest(view_type, next)

    def init_mpr(self, mprAspect):
        # 提取像素数据和像素间距
        for item in ['sag', 'cor', 'ax']:
            self.set_view_aspect(item, mprAspect[item])
        pixel_arrays = [dicom.pixel_array for dicom in self.dicoms]
        if len(pixel_arrays) == 0:
            return
        volume = np.stack(pixel_arrays)
        self.volume = volume
        self.record_init_mpr()

    def update_init_zoom(self, view_type, zoom):
        self.init_zoom[view_type] = zoom

    def update_mpr_center_info(self, view_type, center):
        self.center_posi[view_type] = center

    def update_four_corner_position(self, view_type, new_dict):
        if self.corner_info[view_type]['transformed'] is None:
            self.corner_info[view_type].update({
                "init": new_dict['init'],
                'transformed': new_dict['init']
            })
        else:
            self.corner_info[view_type].update(new_dict)

    def get_four_corner_position(self, view_type, position_type='init'):
        return self.corner_info[view_type][position_type]

    def update_ct_value_arr_dict(self, view_type, new_dict):
        current_slice_index = self.get_current_slice_index(view_type)
        if current_slice_index not in self.ct_value_arr_dict[view_type]:
            # 设置每个view_type 对应层数的 init 数组 和变换后的数组。
            self.ct_value_arr_dict[view_type][current_slice_index] = new_dict
        else:
            self.ct_value_arr_dict[view_type][current_slice_index].update(new_dict)

    def get_current_index_ct_value_arr(self, view_type, arr_type='init'):
        current_slice_index = self.get_current_slice_index(view_type)
        return self.ct_value_arr_dict[view_type][current_slice_index][arr_type]

    def move_scroll_img(self, view_type, x, y):
        # 每个视图当前的张数
        sag_current_index = self.get_current_slice_index('sag')
        cor_current_index = self.get_current_slice_index('cor')
        ax_current_index = self.get_current_slice_index('ax')

        sag_total = self.total['sag']
        cor_total = self.total['cor']
        ax_total = self.total['ax']

        four_corner = self.get_four_corner_position(view_type)
        p0 = four_corner[0]
        p1 = four_corner[1]
        p2 = four_corner[2]
        total_x = p1[0] - p0[0]
        total_y = p2[1] - p1[1]

        if view_type == 'ax':
            # # 想要达到的目标张数
            want_slice_index_x = round(sag_current_index + x / total_x * sag_total)
            actual_slice_index_x = np.clip(want_slice_index_x, 0, sag_total)
            self.set_latest('sag', actual_slice_index_x)

            want_slice_index_y = round(cor_current_index + y / total_y * cor_total)
            actual_slice_index_y = np.clip(want_slice_index_y, 0, cor_total)
            self.set_latest('cor', actual_slice_index_y)
        elif view_type == 'sag':
            # cor
            # ax
            want_slice_index_x = round(cor_current_index + x / total_x * cor_total)
            actual_slice_index_x = np.clip(want_slice_index_x, 0, cor_total)
            self.set_latest('cor', actual_slice_index_x)

            want_slice_index_y = round(ax_current_index + y / total_y * ax_total)
            actual_slice_index_y = np.clip(want_slice_index_y, 0, ax_total)
            self.set_latest('ax', actual_slice_index_y)

        elif view_type == 'cor':
            # sag
            # ax
            want_slice_index_x = round(sag_current_index + x / total_x * sag_total)
            actual_slice_index_x = np.clip(want_slice_index_x, 0, sag_total)
            self.set_latest('sag', actual_slice_index_x)

            want_slice_index_y = round(ax_current_index + y / total_y * ax_total)
            actual_slice_index_y = np.clip(want_slice_index_y, 0, ax_total)
            self.set_latest('ax', actual_slice_index_y)
