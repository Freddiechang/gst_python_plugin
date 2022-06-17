from os.path import join, getsize, isfile
from os import listdir
import subprocess as sp
from multiprocessing import Pool
from EWPSNR import ewpsnr

"""
gst-launch-1.0 filesrc location=./in.mp4 ! qtdemux ! avdec_h264 ! queue ! videoconvert  ! ExampleTransform width=504 height=300 quad_size=12 sal_dir=../../Datasets/UCF/training/Diving-Side-005/maps ! video/x-raw,width=504,height=300 ! ReverseWarp width=720 height=404 quad_size=12 ! videoconvert ! pngenc ! multifilesink location=out/%d.png
"""

def process(path: str, target_ratio, out_filename):
    if 'UCF' in path:
        filename = path.split('/')[-1]
        print("working on {}".format(filename))
        img_path = join(path, 'images')
        map_path = join(path, 'maps')
        t = listdir(img_path)
        t = sorted([i for i in t if i.endswith('.png')])
        command = "ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of default=nw=1:nk=1 {}".format(join(img_path, t[0])).split(" ")
        p = sp.run(command, capture_output=True)
        width, height = p.stdout.decode().split("\n")[:2]
        target_size = (int(int(height) * target_ratio[0]), int(int(width) * target_ratio[1]))
        if isfile("./test/out/UCF/{}_{}x{}.mp4".format(filename, target_size[1], target_size[0])):
            score = ewpsnr("./test/out/UCF/{}_{}x{}.mp4".format(filename, target_size[1], target_size[0]), 
                img_path, map_path)
            bpp = getsize("./test/out/UCF/{}_{}x{}.mp4".format(filename, target_size[1], target_size[0])) * 8 / score[0] / int(width) / int(height)
            with open(out_filename, 'a') as f:
                f.write("{}\t{}\t{}\n".format(
                    filename,
                    bpp,
                    score[1][0]
                ))

    elif 'ETMD' in path or 'SumMe' in path or 'DIEM' in path:
        # path is the path to the video file
        filename = path.split('/')[-1].split('.')[0]
        for i in ['ETMD', 'SumMe', 'DIEM']:
            if i in path:
                dataset = i
        vid_path = path
        path = '/'.join(path.split('/')[:-2])
        map_path = join(path, 'annotation', filename, 'maps')
        command = "ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of default=nw=1:nk=1 {}".format(vid_path).split(" ")
        p = sp.run(command, capture_output=True)
        width, height = p.stdout.decode().split("\n")[:2]
        target_size = (int(int(height) * target_ratio[0]), int(int(width) * target_ratio[1]))
        if isfile("./test/out/{}/{}_{}x{}.mp4".format(dataset, filename, target_size[1], target_size[0])):
            score = ewpsnr("./test/out/{}/{}_{}x{}.mp4".format(dataset, filename, target_size[1], target_size[0]), 
                vid_path, map_path, 'jpg')
            bpp = getsize("./test/out/{}/{}_{}x{}.mp4".format(dataset, filename, target_size[1], target_size[0])) * 8 / score[0] / int(width) / int(height)
            with open(out_filename, 'a') as f:
                f.write("{}\t{}\t{}\n".format(
                    filename,
                    bpp,
                    score[1][0]
                ))
    else:
        pass

if __name__ == "__main__":
    #filelist = listdir("/home/shupeizhang/Codes/Datasets/saliency/UCF/training/")
    #filelist = [join("/home/shupeizhang/Codes/Datasets/saliency/UCF/training/", i) for i in filelist]
    #nfilelist = filelist

    filelist = sorted(listdir("/home/shupeizhang/Codes/Datasets/saliency/DIEM/videos"))
    filelist = [join("/home/shupeizhang/Codes/Datasets/saliency/DIEM/videos", i) for i in filelist]
    # total 84
    # 0, 4, 12, 14, 21, 26
    # +0 +20 +40 +11 +31 +41
    nfilelist = [filelist[i + 51] for i in [0, 4, 12, 14, 21, 26]]
    filelist = [(i, (0.7, 0.7), 'diem.txt') for i in nfilelist]
    with Pool(processes=1) as pool:
        pool.starmap(process, filelist)
