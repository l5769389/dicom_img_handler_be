import numpy as np
from matplotlib import pyplot as plt
from matplotlib.colors import ListedColormap

from config.constant import PSEUDO_COLOR_TYPE


class PseudoHelper:
    def __init__(self):
        self.cmap_dict = {}
        bw_cmap_inverse = self.get_bw_inverse_cmap()
        bw_cmap = self.get_bw_cmap()
        rainbow_cmap = self.get_rainbow_cmap()
        rainbow1_cmap = self.get_rainbow1_cmap()
        rainbow2_cmap = self.get_rainbow2_cmap()
        self.cmap_dict = {
            PSEUDO_COLOR_TYPE.BW: bw_cmap,
            PSEUDO_COLOR_TYPE.BW_INVERSE: bw_cmap_inverse,
            PSEUDO_COLOR_TYPE.RAINBOW: rainbow_cmap,
            PSEUDO_COLOR_TYPE.RAINBOW1: rainbow1_cmap,
            PSEUDO_COLOR_TYPE.RAINBOW2: rainbow2_cmap
        }

    def get_bw_cmap(self):
        bw_cmap = plt.cm.get_cmap('binary')
        bw_colors = bw_cmap(np.arange(bw_cmap.N))
        # 反转黑白颜色映射
        cmap = ListedColormap(bw_colors[::-1])
        return cmap

    def get_rainbow_cmap(self):
        cmap = plt.cm.get_cmap(PSEUDO_COLOR_TYPE.RAINBOW)
        return cmap

    def get_rainbow1_cmap(self):
        rainbow_cmap = plt.cm.get_cmap(PSEUDO_COLOR_TYPE.RAINBOW)
        # rainbow_cmap.N 获取颜色映射中的索引数量
        # np.arange(N) 创建一个长度为N的np数组
        from_rainbow_arr = np.arange(rainbow_cmap.N)
        cmap_array = rainbow_cmap(from_rainbow_arr)
        # 将映射数组的第一个映射为黑色，那么影像中的背景颜色就变成了黑色。
        cmap_array[0] = [0, 0, 0, 1]
        cmap = rainbow_cmap.from_list('rainbow1', cmap_array, rainbow_cmap.N)
        return cmap

    def get_rainbow2_cmap(self):
        rainbow_cmap = plt.cm.get_cmap(PSEUDO_COLOR_TYPE.RAINBOW)
        from_rainbow_arr = np.arange(rainbow_cmap.N)
        cmap_array = rainbow_cmap(from_rainbow_arr)
        cmap_array[:, 0:2] = 1.0
        cmap_array[0] = [0, 0, 0, 1]
        cmap = rainbow_cmap.from_list('rainbow2', cmap_array, rainbow_cmap.N)
        return cmap

    def get_bw_inverse_cmap(self):
        cmap = plt.cm.get_cmap('binary')
        return cmap

    def get_cmap(self, type):
        return self.cmap_dict[type]
