import math

import cv2
import numpy as np
from PIL import Image

from helper.pseudo_helper import PseudoHelper


class DicomLayer(PseudoHelper):
    def __init__(self, base_info, view_type):
        super().__init__()
        self.base_info = base_info
        self.spacing = None
        self.base_info = base_info
        self.view_type = view_type
        self.cache_img = {}
        self.transfer = {
            'offset_x': 0,
            'offset_y': 0,
            'zoom': 1,
            'rotate': 0,
            'flip': []
        }

    def get_dicom_img(self):
        if self.check_cache_dicom_exist():
            print('cache')
            rgb_img = self.get_cache_dicom_img()
        else:
            print('no cache')
            pixel_array = self.base_info.get_recent_pixel_array(self.view_type)
            resized_pixel_array = self.resize_to_fit_spacing(pixel_array)
            img_hu_arr = self.pixel_to_hu_arr(resized_pixel_array)
            self.check_need_update_ct_arr(img_hu_arr)
            clipped_img_arr = self.clip_data(img_hu_arr)
            full_arr = self.add_bg_and_img(clipped_img_arr)
            colored_img_arr = self.change_color_space(full_arr)
            rgb_img = self.full_img_to_base64(colored_img_arr)
            self.set_cache_dicom_img(rgb_img)
        return self.transfer_img(rgb_img)

    def set_cache_dicom_img(self, rbg_img):
        current_index = self.base_info.get_current_slice_index(self.view_type)
        self.cache_img[current_index] = rbg_img

    def get_cache_dicom_img(self):
        current_index = self.base_info.get_current_slice_index(self.view_type)
        return self.cache_img[current_index]

    def check_cache_dicom_exist(self):
        current_index = self.base_info.get_current_slice_index(self.view_type)
        return current_index in self.cache_img.keys()

    def check_need_update_ct_arr(self, full_arr):
        update_dict = {
            "init": full_arr,
            "transformed": full_arr
        }
        self.base_info.update_ct_value_arr_dict(self.view_type, update_dict)

    def update_four_angle_point(self, update_dict):
        self.base_info.update_four_corner_position(self.view_type, update_dict)

    def update_dicom_ct_arr(self, arr):
        update_dict = {
            "transformed": arr
        }
        self.base_info.update_ct_value_arr_dict(self.view_type, update_dict)

    def transfer_img(self, img_pil):
        view_type = self.view_type
        w, h = img_pil.size
        pil_transfer_tuple = self.get_transfer_matrix(view_type)
        dsize = (int(w), int(h))
        transformed_img = img_pil.transform(dsize, Image.AFFINE, pil_transfer_tuple)
        flipped_img = self.rotate_flip_img(transformed_img, view_type)
        return flipped_img

    def full_img_to_base64(self, full_arr):
        encode_img = self.rgb_to_base64(full_arr)
        return encode_img

    def rgb_to_base64(self, full_arr_3ch):
        img_pil = self.arr_to_img(full_arr_3ch)
        return img_pil

    def arr_to_img(self, arr):
        img_pil = Image.fromarray(arr)
        return img_pil

    def resize_to_fit_spacing(self, hu_array):
        space_x, space_y = self.base_info.spacing[self.view_type]
        h, w = hu_array.shape
        target_w = int(w * space_x)
        target_h = int(h * space_y)
        return cv2.resize(hu_array, (target_w, target_h), interpolation=cv2.INTER_LINEAR)

    def pixel_to_hu_arr(self, pixel_array):
        transformed_array = self.pixel_to_transformed_arr(pixel_array)
        return transformed_array

    def pixel_to_transformed_arr(self, pixel_array):
        # 斜率 和 截距值
        slope = self.base_info.base_info['slope']
        intercept = self.base_info.base_info['intercept']
        return pixel_array * slope + intercept

    def add_bg_and_img(self, img_arr):
        img_arr = self.scale_img_if_need(img_arr)
        rows, cols = img_arr.shape[:2]
        target_cols, target_rows = self.get_bg_size()
        img_min = np.min(img_arr)
        if img_arr.ndim == 2:
            bg = np.full((target_rows, target_cols), img_min)
        else:
            bg = np.full((target_rows, target_cols, 3), img_min)
        delta_rows = max((target_rows - rows) // 2, 0)
        delta_cols = max((target_cols - cols) // 2, 0)
        four_corner = [(delta_cols, delta_rows), (delta_cols + cols, delta_rows),
                       (delta_cols + cols, delta_rows + rows),
                       (delta_cols, delta_rows + rows)]
        update_dict = {
            "init": four_corner,
        }
        self.update_four_angle_point(update_dict)
        start_row = delta_rows
        end_row = (delta_rows + rows)
        start_col = delta_cols
        end_col = delta_cols + cols
        if img_arr.ndim == 2:
            bg[start_row: end_row, start_col: end_col] = img_arr
        else:
            bg[start_row: end_row, start_col: end_col, :] = img_arr
        return bg

    def update_transfer(self, new_dict):
        self.transfer.update(new_dict)
        self.transfer_ct_arr(self.view_type)

    def get_bg_size(self):
        target_w = self.base_info.bg[self.view_type]['width']
        target_h = self.base_info.bg[self.view_type]['height']
        return target_w, target_h

    def scale_img_if_need(self, gray_arr):
        target_w, target_h = self.get_bg_size()
        h, w = gray_arr.shape[:2]
        aspect_ratio = min(target_w / w, target_h / h)
        preset_resized_h = int(h * aspect_ratio)
        preset_resized_w = int(w * aspect_ratio)
        # # 最小需要的放大倍数
        if aspect_ratio <= 1:
            self.base_info.update_init_zoom(self.view_type, aspect_ratio)
            # 真实图像需要缩小，才能变为渲染尺寸,先缩小为初始尺寸 再乘以放大倍数
            dsize = (preset_resized_w, preset_resized_h)
            return cv2.resize(gray_arr, dsize, interpolation=cv2.INTER_LINEAR)
        else:
            return gray_arr

    def clip_data(self, arr):
        view_type = self.view_type
        view = self.map_view_type(view_type)
        window_width = self.base_info.ww_wl[view]['ww']
        window_center = self.base_info.ww_wl[view]['wl']
        # 根据窗宽窗位调整像素值
        min_value = window_center - window_width / 2
        max_value = window_center + window_width / 2
        adjusted_pixel_array = np.clip(arr, min_value, max_value)
        adjusted_pixel_array = adjusted_pixel_array.astype(np.int16)
        return adjusted_pixel_array

    def map_view_type(self, view_type):
        view = ''
        if view_type == 'preview':
            view = view_type
        elif view_type == 'sag' or view_type == 'cor' or view_type == 'ax':
            view = 'mpr'
        return view

    def change_color_space(self, arr):
        normalization_arr = arr / arr.max()
        cmap = self.get_cmap(self.base_info.pseudo_color_type)
        cmap_arr = cmap(normalization_arr)
        changed_arr = (cmap_arr * 255)[:, :, :3].astype(np.uint8)
        return changed_arr

    def transfer_ct_arr(self, view_type):
        self.transfer_ct_value_arr(view_type)
        self.transfer_four_angle_point(view_type)

    def transfer_ct_value_arr(self, view_type):
        arr = self.base_info.get_current_index_ct_value_arr(view_type)
        img_pil = self.arr_to_img(arr)
        w, h = img_pil.size
        dsize = (int(w), int(h))
        # 对图像进行仿射变换。
        pil_transfer_tuple = self.get_transfer_matrix(view_type)
        transformed_img = img_pil.transform(dsize, Image.AFFINE, pil_transfer_tuple)
        flipped_img = self.rotate_flip_img(transformed_img, view_type)
        flipped_img_arr = np.array(flipped_img)
        self.update_dicom_ct_arr(flipped_img_arr)

    def transfer_four_angle_point(self, view_type):
        point_transfer_tuple = self.get_point_transfer_matrix(view_type)
        # 对四个点进行旋转、平移、缩放变换。
        affine_matrix = (point_transfer_tuple[0], point_transfer_tuple[1], point_transfer_tuple[2],
                         point_transfer_tuple[3], point_transfer_tuple[4], point_transfer_tuple[5])
        matrix_np = np.array(affine_matrix).reshape(2, 3)

        transformed_points = []
        init_four_corner = self.base_info.get_four_corner_position(view_type, 'init')
        for point in init_four_corner:
            # 对4个边缘点进行变换。
            transformed_point = np.around(np.dot(matrix_np, [point[0], point[1], 1]))
            transformed_point = self.rotate_or_flip_point_coord_viewer_center(view_type, transformed_point)
            transformed_points.append(transformed_point[:2])
        self.update_four_angle_point({
            "transformed": transformed_points
        })

    def get_transfer_matrix(self, view_type):
        total_zoom = self.get_transfer_info('zoom')
        total_offset_x = self.get_transfer_info('offset_x')
        total_offset_y = self.get_transfer_info('offset_y')
        w, h = self.get_bg_size()
        rotate_center = (w // 2, h // 2)
        pil_transfer_tuple = (
            total_zoom, 0, rotate_center[0] * (1 - total_zoom) - total_offset_x,
            0, total_zoom, rotate_center[1] * (1 - total_zoom) - total_offset_y,
            0, 0, 1
        )
        return pil_transfer_tuple

    def get_point_transfer_matrix(self, view_type):
        # 缩小图像， self.transfer[view_type].get('zoom') 为 2，原图 / 现在图
        total_zoom = 1 / self.get_transfer_info('zoom')
        total_offset_x = -self.get_transfer_info('offset_x') * total_zoom
        total_offset_y = -self.get_transfer_info('offset_y') * total_zoom
        w, h = self.get_bg_size()
        rotate_center = (w // 2, h // 2)
        pil_transfer_tuple = (
            total_zoom, 0, rotate_center[0] * (1 - total_zoom) - total_offset_x,
            0, total_zoom, rotate_center[1] * (1 - total_zoom) - total_offset_y,
            0, 0, 1
        )
        return pil_transfer_tuple

    def rotate_flip_img(self, img, view_type):
        total_flip = self.get_transfer_info('flip')
        total_rotate = self.get_transfer_info('rotate')
        for each_flip in total_flip:
            if each_flip == 'hor':
                img = img.transpose(Image.FLIP_LEFT_RIGHT)
            elif each_flip == 'ver':
                img = img.transpose(Image.FLIP_TOP_BOTTOM)
        if total_rotate != 0:
            img = img.rotate(total_rotate)
        return img

    def rotate_or_flip_point_coord_viewer_center(self, view_type, point):
        total_flip = self.get_transfer_info('flip')
        total_rotate = self.get_transfer_info('rotate')
        w, h = self.get_bg_size()
        x, y = point
        rotate_center = (w // 2, h // 2)
        for each_flip in total_flip:
            if each_flip == 'hor':
                x = w - x
            elif each_flip == 'ver':
                y = h - y
        if total_rotate != 0:
            x_shift = x - rotate_center[0]
            y_shift = y - rotate_center[1]
            cos_angle = math.cos(math.radians(-total_rotate))
            sin_angle = math.sin(math.radians(-total_rotate))
            x_rotate = x_shift * cos_angle - y_shift * sin_angle
            y_rotate = x_shift * sin_angle + y_shift * cos_angle
            x = np.around(x_rotate + rotate_center[0])
            y = np.around(y_rotate + rotate_center[1])
        return (x, y)

    def get_transfer_info(self, key):
        val = self.base_info.transfer[self.view_type][key]
        return val

    def calc_current_position(self, view_type, x, y):
        try:
            x_show, y_show = self.get_x_y_index_by_position(view_type, x, y)
        except Exception as e:
            print(e)
            return 0, 0, 0
        h, w = self.base_info.get_current_index_ct_value_arr(view_type, 'transformed').shape
        x = np.clip(x, 0, w - 1)
        y = np.clip(y, 0, h - 1)
        value = self.base_info.get_current_index_ct_value_arr(view_type, 'transformed')[int(y)][int(x)]
        return round(x_show), round(y_show), round(value)

    def get_x_y_index_by_position(self, view_type, x, y):
        corners = self.base_info.get_four_corner_position(view_type, 'transformed')
        p0 = corners[0]
        p1 = corners[1]
        p2 = corners[2]
        direction_dict = self.get_coordinate_direction(view_type)
        distance_to_x_start = 0
        distance_to_y_start = 0
        x_start = 0
        x_end = 0
        y_start = 0
        y_end = 0
        x_length = 0
        y_length = 0
        # 影像y坐标系和前端页面的y坐标系方向一致。
        # 根据坐标系的位置计算距离
        if direction_dict['bottom'] == 'y':
            y_start = p1[1]
            y_end = p2[1]
            distance_to_y_start = y - y_start
        elif direction_dict['bottom'] == '-y':
            y_start = p1[1]
            y_end = p2[1]
            distance_to_y_start = y_start - y
        elif direction_dict['bottom'] == 'x':
            x_start = p0[1]
            x_end = p1[1]
            distance_to_x_start = y - x_start
        elif direction_dict['bottom'] == '-x':
            x_start = p0[1]
            x_end = p1[1]
            distance_to_x_start = x_start - y

        if direction_dict['right'] == 'y':
            y_start = p1[0]
            y_end = p2[0]
            distance_to_y_start = x - y_start
        elif direction_dict['right'] == '-y':
            y_start = p1[0]
            y_end = p2[0]
            distance_to_y_start = y_start - x
        elif direction_dict['right'] == 'x':
            x_start = p0[0]
            x_end = p1[0]
            distance_to_x_start = x - x_start
        elif direction_dict['right'] == '-x':
            x_start = p0[0]
            x_end = p1[0]
            distance_to_x_start = x_start - x

        if direction_dict['bottom'] == 'y' or direction_dict['bottom'] == '-y':
            y_length = abs(y_end - y_start)
        elif direction_dict['bottom'] == 'x' or direction_dict['bottom'] == '-x':
            x_length = abs(x_end - x_start)

        if direction_dict['right'] == 'y' or direction_dict['right'] == '-y':
            y_length = abs(y_end - y_start)
        elif direction_dict['right'] == 'x' or direction_dict['right'] == '-x':
            x_length = abs(x_end - x_start)
        x_total = self.base_info.base_info["columns"]
        y_total = self.base_info.base_info["rows"]
        pixel_per_x = x_length / x_total
        pixel_per_y = y_length / y_total
        x_show = np.clip(round(distance_to_x_start / pixel_per_x), 0, x_total - 1)
        y_show = np.clip(round(distance_to_y_start / pixel_per_y), 0, y_total - 1)
        return x_show, y_show

    def get_coordinate_direction(self, view_type):
        coordination = self.base_info.coordinate_direction[view_type]
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
