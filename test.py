import numpy as np

A = np.array([[1, 2], [3, 4]])

# 单位矩阵
I = np.identity(2)

print(A.dot(I))

print(I.dot(A))

# A的逆矩阵
inv_A = np.linalg.inv(A)
