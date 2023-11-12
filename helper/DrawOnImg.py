from PIL import ImageFont

# text_color = (255, 255, 255)
text_color = (255, 255, 255)
cross_ball_radius = 10
# bgr
r_color = (255, 0, 0)
g_color = (0, 255, 0)
b_color = (0, 0, 255)
endpoint_ball_radius = 5
font_4_angle = ImageFont.truetype('/resource/HarmonyOS_Sans_SC_Bold.ttf', size=16)

font_draw = ImageFont.truetype('arial.ttf', size=14)
line_width = 2


class Draw:
    @staticmethod
    def draw_line(drawer, start, end, color=r_color, scale=1):
        drawer.line((int(start[0]), int(start[1]), int(end[0]), int(end[1])), fill=color,
                    width=line_width, joint='curve')

    @staticmethod
    def draw_circle(drawer, center_x, center_y, scale=1):
        drawer.ellipse([(center_x - endpoint_ball_radius, center_y - endpoint_ball_radius),
                        (center_x + endpoint_ball_radius, center_y + endpoint_ball_radius)], outline=r_color,
                       width=line_width)

    @staticmethod
    def draw_ellipse(drawer, bounding, scale=1):
        drawer.ellipse(bounding, outline=r_color, width=line_width)

    @staticmethod
    def draw_text(drawer, content, posi, type='draw'):
        if content is None:
            return
        font = font_4_angle if type == '4angle' else font_draw
        drawer.text(posi, content, font=font, fill=text_color)

    @staticmethod
    def draw_cross_line(drawer, center, view_type, w, h):
        center_x, center_y = center
        if view_type == 'ax':
            h_color = g_color
            v_color = b_color
        elif view_type == 'sag':
            h_color = r_color
            v_color = g_color
        else:
            h_color = r_color
            v_color = b_color
        Draw.draw_line(drawer, (0, center_y), (center_x - cross_ball_radius, center_y), color=h_color)
        Draw.draw_line(drawer, (center_x + cross_ball_radius, center_y), (w, center_y), color=h_color)

        Draw.draw_line(drawer, (center_x, 0), (center_x, center_y - cross_ball_radius), color=v_color)
        Draw.draw_line(drawer, (center_x, center_y + cross_ball_radius),
                       (center_x, h), color=v_color)

    @staticmethod
    def add_dicom_info(drawer, desc_info, w, h):
        padding = 5
        one_text = 'a'
        one_text_w, one_text_h = font_4_angle.getsize(one_text)
        position_dict = {
            # 左上角的起始位置
            "lt": (padding, padding),
            # 左下角的起始位置,倒着往上面写
            "lb": (padding, h - padding),
            # 右上角的截止位置
            "rt": (w - padding, padding),
            # 右下角的截止位置
            "rb": (w - padding - one_text_w, h - padding),
            "tm": (w // 2, padding),
            "rm": (w - padding - one_text_w, h // 2),
            "bm": (w // 2, h - padding - one_text_h),
            "lm": (padding, h // 2)
        }
        for position, desc_arr in desc_info.items():
            for index, item in enumerate(desc_arr):
                text = ''
                for each_line_k, each_line_v in item.items():
                    if each_line_k != '':
                        text = text + f"{each_line_k}: {each_line_v}" + ' '
                    else:
                        text = text + f"{each_line_v}" + ' '
                text_w, text_h = font_4_angle.getsize(text)
                spacing_h = 5
                every_line_offset = text_h + spacing_h
                posi = position_dict[position]
                current_posi = (0, 0)
                if position == 'lt':
                    current_posi = (int(posi[0]), int(posi[1] + every_line_offset * index))
                elif position == 'lb':
                    current_posi = (int(posi[0]), int(posi[1] - every_line_offset * index - every_line_offset))
                elif position == 'rt':
                    current_posi = (int(posi[0] - text_w), int(posi[1] + every_line_offset * index))
                elif position == 'rb':
                    current_posi = (int(posi[0] - text_w), int(posi[1] - every_line_offset * index - every_line_offset))
                else:
                    current_posi = (posi[0], posi[1])
                Draw.draw_text(drawer, text, current_posi, type='4angle')
