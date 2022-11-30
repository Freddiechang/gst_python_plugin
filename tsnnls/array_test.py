import numpy as np
from scipy.sparse import csc_matrix
from scipy.sparse.linalg import lsqr as splsqr
import sys

from tsnnls import *


indptr = np.array([0, 2, 3, 6])
indices = np.array([0, 2, 2, 0, 1, 2])
data = np.array([1, 2, 3, 4, 5.56, 6.45])
b = np.array([1.0,1.0,1.0])
A = csc_matrix((data, indices, indptr), shape=(3, 3))
#c = py_t_lsqr(3,3,A.indptr, A.indices, A.data, b)
#print(c)
print(lsqr(A, b))
