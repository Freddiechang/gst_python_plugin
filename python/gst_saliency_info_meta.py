"""
https://github.com/jackersson/gst-python-hacks/blob/master/gst-metadata/gst_buffer_info_meta.py
"""
import gi
gi.require_version('Gst', '1.0')

from ctypes import cdll, c_uint, c_void_p, c_bool, c_float, cast, POINTER, Structure

import numpy as np
# Metadata structure that describes GstBufferInfo (C)
class GstSaliencyInfo(Structure):
    _fields_ = [
        ("gaussian_count", c_uint),
        ("parameters", c_void_p)
        ]

# Pointer to GstBufferInfo structure
GstSaliencyInfoPtr = POINTER(GstSaliencyInfo)
clib = cdll.LoadLibrary("../saliency_meta_c/build/libgst_saliency_info_meta.so")
clib.gst_saliency_add_saliency_info_meta.argtypes = [c_void_p, c_uint, c_void_p]
clib.gst_saliency_add_saliency_info_meta.restype = c_void_p

clib.gst_saliency_get_saliency_info_meta.argtypes = [c_void_p]
clib.gst_saliency_get_saliency_info_meta.restype = GstSaliencyInfoPtr

clib.gst_saliency_remove_saliency_info_meta.argtypes = [c_void_p]
clib.gst_saliency_remove_saliency_info_meta.restype = c_bool

def write_saliency_meta(buffer, gaussian_parameters):
    gaussian_parameters = gaussian_parameters.astype(np.float32)
    gaussian_count = c_uint(gaussian_parameters.shape[0] // 6)
    if not gaussian_parameters.flags['C_CONTIGUOUS']:
        gaussian_parameters = np.ascontiguousarray(gaussian_parameters)
    parameters = c_void_p(gaussian_parameters.ctypes.data)
    clib.gst_saliency_add_saliency_info_meta(hash(buffer), gaussian_count, parameters)

def get_saliency_meta(buffer):
    res = clib.gst_saliency_get_saliency_info_meta(hash(buffer))
    s = res.contents
    return np.ctypeslib.as_array(cast(s.parameters, POINTER(c_float)), (s.gaussian_count * 6,))

def remove_saliency_meta(buffer):
    return clib.gst_saliency_remove_saliency_info_meta(hash(buffer))