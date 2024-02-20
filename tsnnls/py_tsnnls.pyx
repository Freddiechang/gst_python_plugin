
from libc.stdlib cimport malloc, free
from libc.string cimport strcpy, strlen

# Import the Python-level symbols of numpy
import numpy as np

# Import the C-level symbols of numpy
cimport numpy as np

# Numpy must be initialized. When using numpy from C or Cython you must
# _always_ do that, or you will have segfaults
np.import_array()


cdef extern from "libtsnnls/tsnnls.h":
    void tsnnls_version(char *version, size_t strlen)
    cdef int TAUCS_DOUBLE
    ctypedef double taucs_double
    ctypedef union _taucs_ccs_matrix_values:
        void * v
        taucs_double* d
    ctypedef struct taucs_ccs_matrix: 
        int n
        int m
        int flags
        int * colptr
        int * rowind
        _taucs_ccs_matrix_values values
    
    taucs_double* t_lsqr(taucs_ccs_matrix *A, taucs_double *b)
    # README for how to use t_snnls
    taucs_double* t_snnls( taucs_ccs_matrix *A_original_ordering, taucs_double *b, double* outResidualNorm, double inRelErrTolerance, int inPrintErrorWarnings)
    # tsnnls.h tsnnls_test.c
    taucs_ccs_matrix* taucs_construct_sorted_ccs_matrix( double* values, int rowsize, int rows )
    void taucs_print_ccs_matrix(const taucs_ccs_matrix* A )
    void taucs_ccs_free(taucs_ccs_matrix* A)

cdef class ArrayWrapper:
    cdef void* data_ptr
    cdef int size

    cdef set_data(self, int size, void* data_ptr):
        """ Constructor for the class.
        Mallocs a memory buffer of size (n*sizeof(int)) and sets up
        the numpy array.
        Parameters:
        -----------
        n -- Length of the array.
        Data attributes:
        ----------------
        data -- Pointer to an integer array.
        alloc -- Size of the data buffer allocated.
        """
        self.data_ptr = data_ptr
        self.size = size

    def __array__(self):
        cdef np.npy_intp shape[1]
        shape[0] = <np.npy_intp> self.size
        ndarray = np.PyArray_SimpleNewFromData(1, shape, np.NPY_FLOAT64, self.data_ptr)
        return ndarray

    def __dealloc__(self):
        """ Frees the array. """
        free(<void*>self.data_ptr)

def tsnnls_version_func():
    cdef char* p = <char *> malloc((200 + 1) * sizeof(char))
    cdef Py_ssize_t n = strlen(p)
    tsnnls_version(p, n)
    py_string = <bytes> p
    return py_string

def lsqr(A, b):
    """
    for A:
        n -> rowsize/cols
        m -> rows
        flags -> should always be taucs_double
        indptr -> taucs.colptr, rowsize + 1
        indices -> taucs.rowind, count of non-zero elements
        values -> taucs.values.d
    for b:
        b
    """
    m, n = A.shape
    indptr = A.indptr
    indices = A.indices
    values = A.data
    
    cdef taucs_ccs_matrix* A1 = <taucs_ccs_matrix*> malloc(sizeof(taucs_ccs_matrix))

    indptr = indptr.astype(np.int32)
    indices = indices.astype(np.int32)
    values = values.astype(np.float64)
    b = b.astype(np.float64)


    cdef np.ndarray[np.float64_t, ndim=1, mode = 'c'] npa_buff = np.ascontiguousarray(values)
    cdef double* A_buff = <double*> npa_buff.data
    cdef np.ndarray[np.float64_t, ndim=1, mode = 'c'] npb_buff = np.ascontiguousarray(b)
    cdef double* b_buff = <double*> npb_buff.data
    cdef np.ndarray[np.int32_t, ndim=1, mode = 'c'] npip_buff= np.ascontiguousarray(indptr)
    cdef int* indptr_buff = <int*> npip_buff.data
    cdef np.ndarray[np.int32_t, ndim=1, mode = 'c'] npidx_buff = np.ascontiguousarray(indices)
    cdef int* indices_buff = <int*> npidx_buff.data
    A1[0].n = n
    A1[0].m = m
    A1[0].flags = TAUCS_DOUBLE
    A1[0].colptr = indptr_buff
    A1[0].rowind = indices_buff
    A1[0].values.d = A_buff
    #taucs_print_ccs_matrix(A1)
    cdef taucs_double *results
    results = t_lsqr(A1, b_buff)
    array_wrapper = ArrayWrapper()
    array_wrapper.set_data(n, <void*> results) 
    free(A1)

    return (np.array(array_wrapper), None)

def snnls(A, b):
    """
    for A:
        n -> rowsize/cols
        m -> rows
        flags -> should always be taucs_double
        indptr -> taucs.colptr, rowsize + 1
        indices -> taucs.rowind, count of non-zero elements
        values -> taucs.values.d
    for b:
        b
    """
    m, n = A.shape
    indptr = A.indptr
    indices = A.indices
    values = A.data
    
    cdef taucs_ccs_matrix* A1 = <taucs_ccs_matrix*> malloc(sizeof(taucs_ccs_matrix))

    indptr = indptr.astype(np.int32)
    indices = indices.astype(np.int32)
    values = values.astype(np.float64)
    b = b.astype(np.float64)


    cdef np.ndarray[np.float64_t, ndim=1, mode = 'c'] npa_buff = np.ascontiguousarray(values)
    cdef double* A_buff = <double*> npa_buff.data
    cdef np.ndarray[np.float64_t, ndim=1, mode = 'c'] npb_buff = np.ascontiguousarray(b)
    cdef double* b_buff = <double*> npb_buff.data
    cdef np.ndarray[np.int32_t, ndim=1, mode = 'c'] npip_buff= np.ascontiguousarray(indptr)
    cdef int* indptr_buff = <int*> npip_buff.data
    cdef np.ndarray[np.int32_t, ndim=1, mode = 'c'] npidx_buff = np.ascontiguousarray(indices)
    cdef int* indices_buff = <int*> npidx_buff.data
    A1[0].n = n
    A1[0].m = m
    A1[0].flags = TAUCS_DOUBLE
    A1[0].colptr = indptr_buff
    A1[0].rowind = indices_buff
    A1[0].values.d = A_buff
    #taucs_print_ccs_matrix(A1)
    cdef taucs_double *results
    cdef double residual
    #taucs_double* t_snnls( taucs_ccs_matrix *A_original_ordering, taucs_double *b, double* outResidualNorm, double inRelErrTolerance, int inPrintErrorWarnings)
    results = t_snnls(A1, b_buff, &residual, -0.1, 0)
    array_wrapper = ArrayWrapper()
    array_wrapper.set_data(n, <void*> results) 
    free(A1)

    return (np.array(array_wrapper), None)

