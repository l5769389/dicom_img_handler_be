import base64
import concurrent
import threading
import time
from io import BytesIO

from PIL import Image, ImageDraw

from helper.generate_3d import Generate3D
from layers.base_info import BaseInfo
from layers.cross import CrossLayer
from layers.dicom import DicomLayer
from layers.dicom_info import DicomInfoLayer
from layers.measure import MeasureLayer

total_time = 0
total_count = 0
executor = concurrent.futures.ThreadPoolExecutor()


class GenerateImg():
    def __init__(self):
        self.base_info = BaseInfo()
        self.dicom_layer_dict = {}
        self.dicom_info_dict = {}
        self.measure_layer_dict = {}
        self.cross_layer_dict = {}
        self.init_loading = True
        for item in ['preview', 'sag', 'cor', 'ax']:
            self.dicom_layer_dict[item] = DicomLayer(self.base_info, item)
            self.dicom_info_dict[item] = DicomInfoLayer(self.base_info, item)
            self.measure_layer_dict[item] = MeasureLayer(self.base_info, item)
            self.cross_layer_dict[item] = CrossLayer(self.base_info, item)

    def get_preview_img(self, dict):
        self.base_info.init_base_info(dict)
        view_type = 'preview'
        ans = self.get_blend_img(view_type)
        return ans

    def get_blend_img(self, view_type):
        dicom_img = self.dicom_layer_dict[view_type].get_dicom_img()
        measure_img = self.measure_layer_dict[view_type].get_drew_img()
        cross_img = None
        if view_type != 'preview':
            cross_img = self.cross_layer_dict[view_type].get_drew_img()
        final_img = self.blend_img(dicom_img, measure_img, cross_img)
        desc = self.dicom_info_dict[view_type].get_img_desc_info()
        encode_img = self.img_to_base64(final_img)
        return {
            "type": view_type,
            "imgs": encode_img,
            "desc": desc
        }

    def draw_desc(self, img, view_type):
        dicom_img_drawer = ImageDraw.Draw(img)
        w, h = img.size
        self.dicom_info_dict[view_type].draw_info_on_img(dicom_img_drawer, w, h)

    def blend_img(self, dicom_img, measure_img, img_cross=None):
        rgba_img = dicom_img.convert('RGBA')
        measure_img = measure_img.convert('RGBA')
        blended_img = rgba_img
        if measure_img is not None:
            blended_img = Image.alpha_composite(rgba_img, measure_img)
        if img_cross is not None:
            img_cross = img_cross.convert('RGBA')
            blended_img = Image.alpha_composite(blended_img, img_cross)
        blended_img = blended_img.convert('RGB')
        return blended_img

    def img_to_base64(self, img):
        # 使用cv压缩，这种方式耗时很多，所以采用转为Image的方式。
        buffer = BytesIO()
        # 限制颜色数
        # img = img.quantize(colors=256)
        img.save(buffer, format='JPEG', quality=70)
        # img.save(buffer, format='PNG')
        encoded_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return encoded_data

    def draw_various_img(self, view_type, sub_op_type, position, action_type):
        self.measure_layer_dict[view_type].draw_img(action_type, position, sub_op_type)
        return self.get_blend_img(view_type)

    def adjust_window_single(self, x, y):
        view_type = 'preview'
        self.adjust_window(x, y, view_type)
        return self.get_blend_img(view_type)

    def adjust_window_multi(self, x, y):
        view_type = 'mpr'
        self.adjust_window(x, y, view_type)
        return self.get_mpr_img()

    def adjust_window(self, x, y, view_type):
        self.base_info.adjust_window(view_type, x, y)

    def pan_img(self, view_type, x, y):
        update_transfer_dict = self.base_info.pan_img(view_type, x, y)
        self.update_other_layers(view_type, update_transfer_dict)
        return self.get_current_img_dict(view_type)

    def zoom_img(self, view_type, zoom):
        update_transfer_dict = self.base_info.zoom_img(view_type, zoom)
        self.update_other_layers(view_type, update_transfer_dict)
        return self.get_current_img_dict(view_type)

    def flip_img(self, view_type, direction):
        update_transfer_dict = self.base_info.flip_img(view_type, direction)
        self.update_other_layers(view_type, update_transfer_dict)
        return self.get_current_img_dict(view_type)

    def rotate_img(self, view_type, angle):
        update_transfer_dict = self.base_info.rotate_img(view_type, angle)
        self.update_other_layers(view_type, update_transfer_dict)
        return self.get_current_img_dict(view_type)

    def update_other_layers(self, view_type, update_dict):
        self.measure_layer_dict[view_type].update_transfer(update_dict)
        self.dicom_layer_dict[view_type].update_transfer(update_dict)

    def get_current_img_dict(self, view_type):
        if view_type == 'preview':
            return self.get_blend_img(view_type)
        else:
            return self.get_mpr_img()

    def scroll_img(self, view_type, scroll):
        self.base_info.scroll_img(view_type, scroll)
        return self.get_current_img_dict(view_type)

    def clear_choosing_img(self, view_type):
        self.measure_layer_dict[view_type].reset_drawing_points()
        return self.get_current_img_dict(view_type)

    def clear_all_draw_img(self, view_type):
        self.measure_layer_dict[view_type].reset_measures()
        return self.get_current_img_dict(view_type)

    def clear_all_rotate(self, view_type):
        self.base_info.clear_all_rotate(view_type)
        return self.get_current_img_dict(view_type)

    def reset_img(self, view_type):
        self.base_info.reset(view_type)
        return self.get_current_img_dict(view_type)

    def loop_play(self, view_type):
        self.base_info.loop_play(view_type)
        return self.get_current_img_dict(view_type)

    def resize_single_view(self, view_type, dict):
        self.base_info.set_view_aspect(view_type, dict)
        return self.get_blend_img(view_type)

    def resize_multi_view(self, view_type):
        return self.get_mpr_img()

    def calc_current_position(self, view_type, x, y):
        try:
            x, y, value = self.dicom_layer_dict[view_type].calc_current_position(view_type, x, y)
            self.dicom_info_dict[view_type].update_current_position_info(view_type, 'x', x)
            self.dicom_info_dict[view_type].update_current_position_info(view_type, 'y', y)
            self.dicom_info_dict[view_type].update_current_position_info(view_type, 'value', value)
            return self.get_blend_img(view_type)
        except Exception as e:
            print(e)

    def init_mpr(self, mprAspect):
        self.base_info.init_mpr(mprAspect)
        return self.get_mpr_img()

    def get_mpr_img(self):
        global total_time
        global total_count
        imgs_dict = {}
        img_desc_dict = {}
        # 多线程的方式：
        futures = []
        for view in ['sag', 'cor', 'ax']:
            future = executor.submit(self.get_blend_img, view)
            futures.append(future)
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
        for item in results:
            imgs_dict[item['type']] = item['imgs']
            img_desc_dict[item['type']] = item['desc']
        return {
            "type": "mpr",
            "imgs": imgs_dict,
            "desc": img_desc_dict,
            "center": self.base_info.center_posi
        }

    def move_scroll_img(self, view_type, x, y):
        self.base_info.move_scroll_img(view_type, x, y)
        return self.get_current_img_dict(view_type)

    def get_3d_vti(self):
        if self.base_info.parent_path == '':
            return False
        try:
            Generate3D.dicom_to_vti(self.base_info.parent_path, './static/output.vti')
            return True
        except Exception as e:
            print(e)
            return False

    def change_color_space(self, view_type, pseudo_color_type):
        self.base_info.change_color_space(pseudo_color_type)
        return self.get_current_img_dict(view_type)
