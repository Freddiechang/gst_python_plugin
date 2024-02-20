import subprocess as sp
from multiprocessing import Pool
import re

from os.path import join, getsize, isfile, isdir
from os import listdir

from PIL import Image
import numpy as np
import cv2

def process(path: str):
    if 'UCF' in path:
        filename = path.split('/')[-1]
        print("working on {}".format(filename))
        img_path = join(path, 'images')
        t = listdir(img_path)
        t = sorted([i for i in t if i.endswith('.png')])
        video_list = listdir(join("test", "out", "UCF_compressed_raw"))
        video = [i for i in video_list if filename in i][0]
        compressed_resolution = re.findall("\d+x\d+", video)[0].split('x')
        compressed_resolution = [int(i) for i in compressed_resolution]
        video_cap = cv2.VideoCapture(join("test", "out", "UCF_compressed_raw", video))
        im = Image.open(join(path, 'images', t[0]))
        gray_im = im.convert('L')
        original_size = gray_im.size
        scores = []
        for i in t:
            tmp_score = []
            im = Image.open(join(path, 'images', i))
            gray_im = im.convert('L')
            gray_im.save(filename + ".png")
            im.close()
            command = 'sipp/bin/sipp -in={}'.format(filename + ".png")
            r = sp.run(command, shell=True, capture_output=True)
            tmp_score.append(float(re.findall("\d+\.\d+", r.stdout.decode().split('\n')[-2])[0]))
            flag, frame = video_cap.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            cv2.imwrite(filename + ".png", gray)
            r = sp.run(command, shell=True, capture_output=True)
            tmp_score.append(float(re.findall("\d+\.\d+", r.stdout.decode().split('\n')[-2])[0]))
            scores.append(tmp_score)
        video_cap.release()
        scores = np.array(scores)
    return filename, original_size, tuple(compressed_resolution), scores


if __name__ == "__main__":
    filelist = sorted(listdir("UCF/training/"))
    filelist = [join("UCF/training/", i) for i in filelist]
    nfilelist = filelist
    with Pool(8) as p:
        results = p.map(process, nfilelist)
    with open("entropy.txt", 'w') as f:
        f.write("filename\toriginal_size\tcompressed_size\toriginal_bpp\tcompressed_bpp\toriginal_total_entropy\tcompressed_toal_entropy\n")
        for i in results:
            filename = i[0]
            original_size = i[1][0] * i[1][1]
            compressed_size = i[2][0] * i[2][1]
            scores = i[3].mean(axis=0)
            f.write("{}\t{}\t{}\t{:.4f}\t{:.4f}\t{:.4f}\t{:.4f}\n".format(filename, original_size, compressed_size, scores[0], scores[1], scores[0] * original_size, scores[1] * compressed_size))