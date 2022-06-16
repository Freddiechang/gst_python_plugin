from os.path import join, isfile, isdir
from os import listdir

import numpy as np
import cv2

class ImagesReader():
    def __init__(self, path, ext='png') -> None:
        self.path = path
        self.files = sorted([i for i in listdir(path) if i.endswith(ext)])
        self.counter = 0
        self.total = len(self.files)
    def read(self, gray=False):
        if gray:
            r = cv2.imread(join(self.path, self.files[self.counter]), cv2.IMREAD_GRAYSCALE)
        else:
            r = cv2.imread(join(self.path, self.files[self.counter]))
        self.counter += 1
        return (True, r)
    def release(self):
        pass
    def isOpened(self):
        return self.counter < self.total

def ewpsnr(src_path: str, ref_path: str, saliency_map_path: str):
    if src_path.endswith(".mp4"):
        src = cv2.VideoCapture(src_path)
    else:
        src = ImagesReader(src_path)
    
    if ref_path.endswith(".mp4"):
        ref = cv2.VideoCapture(ref_path)
    else:
        ref = ImagesReader(ref_path)
    
    sal = ImagesReader(saliency_map_path)
    total_ewpsnr = np.zeros((1))
    count = 0
    while sal.isOpened():
        src_frame = src.read()[1]
        ref_frame = ref.read()[1]
        sal_frame = np.expand_dims(sal.read(True)[1], 2)
        total_pix = src_frame.shape[0] * src_frame.shape[1] * src_frame.shape[2]
        mse = (sal_frame * np.square(src_frame - ref_frame)).sum() / total_pix
        psnr = 10 * np.log10(255 * 255 / mse)
        total_ewpsnr += psnr
        count += 1

    src.release()
    ref.release()
    return total_ewpsnr / count