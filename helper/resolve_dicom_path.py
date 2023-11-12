import os

import numpy as np
import pydicom


# 将所有地址排序
class ResolvePath:
    def load_ds_by_order(self, path):
        temp = [pydicom.dcmread(path + '/' + f) for f in os.listdir(path)]
        slices = [t for t in temp if t.Modality == 'CT']
        slices.sort(key=lambda x: int(x.InstanceNumber))
        try:
            slice_thickness = np.abs(slices[0].ImagePositionPatient[2] - slices[1].ImagePositionPatient[2])
        except:
            slice_thickness = np.abs(slices[0].SliceLocation - slices[1].SliceLocation)
        for s in slices:
            s.SliceThickness = slice_thickness
        return slices

    def load_one(self, path):
        dicom = pydicom.dcmread(path)
        return dicom
