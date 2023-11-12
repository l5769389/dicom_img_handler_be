from helper.DrawOnImg import Draw


class DicomInfoLayer():
    def __init__(self, base_info, view_type):
        self.base_info = base_info
        self.view_type = view_type
        self.current_position_info = {
            "x": 0,
            "y": 0,
            "value": 0
        }

    def draw_info_on_img(self, drawer, w, h):
        desc_info = self.get_img_desc_info()
        Draw.add_dicom_info(drawer, desc_info, w, h)

    def get_bg_size(self):
        target_w = self.base_info.bg[self.view_type]['width']
        target_h = self.base_info.bg[self.view_type]['height']
        return target_w, target_h

    def update_current_position_info(self, view_type, attr, val):
        self.current_position_info[attr] = val

    def get_img_desc_info(self):
        view_type = self.view_type
        current = self.base_info.get_current_slice_index(view_type) + 1
        total = self.base_info.total[view_type] + 1
        x = self.current_position_info['x']
        y = self.current_position_info['y']
        value = self.current_position_info['value']
        manufacturer = self.base_info.base_info['manufacturer']
        ex = self.base_info.base_info['ex']
        se = self.base_info.base_info['se']
        kV = self.base_info.base_info['kV']
        mA = self.base_info.base_info['mA']
        thickness = self.base_info.base_info['thickness']
        img_direction = self.base_info.dicom_img_direction['transformed']
        tm_direction = img_direction['x'][0]
        rm_direction = img_direction['y'][0]
        bm_direction = img_direction['x'][1]
        lm_direction = img_direction['y'][1]
        if view_type == 'preview':
            return {
                "lt": [
                    {
                        "": f'{manufacturer}',
                    },
                    {
                        "ex": f'{ex}',
                    },
                    {
                        "Se": f'{se}',
                    },
                    {
                        "Im": f'{current}/ {total}'
                    }
                ],
                # 倒序
                "lb": [
                    {
                        "W": self.base_info.ww_wl[view_type]['ww'],
                        'L': self.base_info.ww_wl[view_type]['wl']
                    },
                    {
                        "thickness": f'{thickness}',
                    },
                    {
                        "kV": f'{kV}',
                        "mA": f'{mA}',
                    },
                ],
                "tm": [
                    {
                        "": f'{tm_direction}',
                    }
                ],
                "rm": [
                    {
                        "": f'{rm_direction}',
                    }
                ],
                "bm": [
                    {
                        "": f'{bm_direction}',
                    }
                ],
                "lm": [
                    {
                        "": f'{lm_direction}',
                    }
                ],
                # 倒序
                "rb": [
                    {
                        "x": x,
                        "y": y,
                        "value": value
                    },
                ]
            }
        elif view_type == 'sag' or view_type == 'cor' or view_type == 'ax':
            return {
                "lt": [
                    {
                        "Im": f'{current}/ {total}'
                    }
                ],
                "lb": [
                    {
                        "W": self.base_info.ww_wl['mpr']['ww'],
                        'L': self.base_info.ww_wl['mpr']['wl']
                    }
                ],
                "rb": [
                    {
                        "x": x,
                        "y": y,
                        "value": value
                    },
                ]
            }
