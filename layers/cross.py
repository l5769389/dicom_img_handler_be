from PIL import Image, ImageDraw
from helper.DrawOnImg import Draw

class CrossLayer:
    def __init__(self, base_info, view_type):
        self.draw_image = None
        self.drawer = None
        self.base_info = base_info
        self.view_type = view_type

    def create_layer(self):
        width, height = self.get_bg_size()
        self.draw_image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        self.drawer = ImageDraw.Draw(self.draw_image)

    def get_drew_img(self):
        self.create_layer()
        self.draw_cross(self.drawer)
        return self.draw_image

    def get_bg_size(self):
        target_w = self.base_info.bg[self.view_type]['width']
        target_h = self.base_info.bg[self.view_type]['height']
        return target_w, target_h

    def draw_cross(self, drawer):
        view_type = self.view_type
        if view_type == 'preview':
            return
        else:
            total_w, total_h = self.get_bg_size()

            sag_current = self.base_info.get_current_slice_index('sag')
            cor_current = self.base_info.get_current_slice_index('cor')
            ax_current = self.base_info.get_current_slice_index('ax')
            sag_total = self.base_info.total['sag']
            cor_total = self.base_info.total['cor']
            ax_total = self.base_info.total['ax']
            four_corner = self.base_info.get_four_corner_position(view_type,'transformed')
            p0 = four_corner[0]
            p1 = four_corner[1]
            p2 = four_corner[2]
            total_x = p1[0] - p0[0]
            total_y = p2[1] - p1[1]
            if view_type == 'ax':
                # ax图中的四角位置，横向为sag， 纵向为cor指标
                center_x = round(p0[0] + sag_current / sag_total * total_x)
                center_y = round(p1[1] + cor_current / cor_total * total_y)
            elif view_type == 'sag':
                # cor
                center_x = round(p0[0] + cor_current / cor_total * total_x)
                # ax
                center_y = round(p1[1] + ax_current / ax_total * total_y)
            else:
                center_x = round(p0[0] + sag_current / sag_total * total_x)
                center_y = round(p1[1] + ax_current / ax_total * total_y)
            center = (center_x, center_y)
            self.base_info.update_mpr_center_info(view_type, center)
            Draw.draw_cross_line(drawer, center, view_type, total_w, total_h)

    def get_transfer_info(self, view_type, key):
        val = self.base_info.transfer[view_type][key]
        return val
