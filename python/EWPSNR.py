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

def ewpsnr(src_path: str, ref_path: str, saliency_map_path: str, saliency_ext='png'):
    if src_path.endswith(".mp4") or src_path.endswith(".mkv"):
        src = cv2.VideoCapture(src_path)
    else:
        src = ImagesReader(src_path)

    if ref_path.endswith(".mp4"):
        ref = cv2.VideoCapture(ref_path)
    else:
        ref = ImagesReader(ref_path)

    sal = ImagesReader(saliency_map_path, ext=saliency_ext)
    total_ewpsnr = np.zeros((1))
    count = 0
    count_nnan = 0

    while sal.isOpened():
        src_frame = src.read()[1]
        ref_frame = ref.read()[1]
        sal_frame = sal.read(True)[1]
        if sal_frame.shape != (src_frame.shape[0], src_frame.shape[1]):
            sal_frame = cv2.resize(sal_frame, (src_frame.shape[1], src_frame.shape[0]))
        sal_frame = np.expand_dims(sal_frame, 2)
        src_frame, ref_frame = cv2.cvtColor(src_frame, cv2.COLOR_BGR2YUV), cv2.cvtColor(ref_frame, cv2.COLOR_BGR2YUV)
        src_frame, ref_frame = src_frame.astype(float), ref_frame.astype(float)
        sal_frame = sal_frame.astype(float)
        sal_frame = sal_frame / sal_frame.sum() * src_frame.shape[0] * src_frame.shape[1]
        mse = (sal_frame * np.square(src_frame - ref_frame)).sum() / sal_frame.sum() / 3
        psnr = 10.0 * np.log10(255.0 * 255.0 / mse)
        if not np.isnan(psnr):
            total_ewpsnr += psnr
            count_nnan += 1
        count += 1

    src.release()
    ref.release()
    return (count, total_ewpsnr / count_nnan)