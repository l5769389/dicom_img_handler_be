import vtk

class Generate3D:
    @staticmethod
    def dicom_to_vti(dicom_directory, vti_file):
        reader = vtk.vtkDICOMImageReader()
        reader.SetDirectoryName(dicom_directory)
        reader.Update()

        # 创建 VTK 图像数据对象
        vti_data = vtk.vtkImageData()
        vti_data.ShallowCopy(reader.GetOutput())

        # 输出为 .vti 文件
        writer = vtk.vtkXMLImageDataWriter()
        writer.SetFileName(vti_file)
        writer.SetInputData(vti_data)
        writer.Write()
