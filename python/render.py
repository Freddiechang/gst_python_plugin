from os.path import join, isfile, isdir
from os import listdir
import os
import subprocess as sp
from multiprocessing import Pool

"""
gst-launch-1.0 filesrc location=./in.mp4 ! qtdemux ! avdec_h264 ! queue ! videoconvert  ! ExampleTransform width=504 height=300 quad_size=12 sal_dir=../../Datasets/UCF/training/Diving-Side-005/maps ! video/x-raw,width=504,height=300 ! ReverseWarp width=720 height=404 quad_size=12 ! videoconvert ! pngenc ! multifilesink location=out/%d.png
"""

def process(path: str, target_ratio, quad_size: int, sal_interval: int):
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
        target_size = [i - (i % quad_size) + quad_size if (i % quad_size) != 0 else i for i in target_size]
        command = 'gst-launch-1.0 multifilesrc location={0} start-index=1 caps="image/png,framerate=10/1" ! pngdec ! queue ! videoconvert ! ExampleTransform width={1} height={2} quad_size={3} sal_dir={4} sal_interval={7} ! video/x-raw,width={1},height={2},framerate=10/1,format=RGB ! tee name=t ! queue ! ReverseWarp width={5} height={6} quad_size={3} sal_interval={7} ! video/x-raw,width={5},height={6},framerate=10/1,format=RGB ! queue ! videoconvert ! x264enc pass=quant quantizer=0 speed-preset=ultrafast byte-stream=true ! matroskamux ! filesink location={8} t. ! queue ! videoconvert ! x264enc interlaced=true pass=quant quantizer=0 speed-preset=ultrafast byte-stream=true ! matroskamux ! filesink location={9}'.format(
            join(img_path, t[0][:-7] + "%03d.png"),
            target_size[1], target_size[0],
            quad_size,
            map_path,
            width, height,
            sal_interval,
            join("test/out/UCF_raw", filename + "_{}x{}".format(target_size[1], target_size[0]) + ".mkv"),
            join("test/out/UCF_compressed_raw", filename + "_{}x{}".format(target_size[1], target_size[0]) + ".mkv"),
        ).split(' ')
        #command = 'gst-launch-1.0 multifilesrc location={0} start-index=1 caps="image/png,framerate=10/1" ! pngdec ! queue ! videoconvert ! ExampleTransform width={1} height={2} quad_size={3} sal_dir={4} sal_interval={8} ! video/x-raw,width={1},height={2} ! ReverseWarp width={5} height={6} quad_size={3} sal_interval={8} ! videoconvert ! queue ! pngenc ! multifilesink location={7}'.format(
        #    join(img_path, t[0][:-7] + "%03d.png"), target_size[1], target_size[0], quad_size, map_path, width, height, join("test/out/UCF", filename + "_{}x{}".format(target_size[1], target_size[0]) + "_%d.png"), sal_interval
        #).split(' ')
        #print(' '.join(command))
        p = sp.run(command, capture_output=True)
        print(p.stdout.decode(), p.stderr.decode())

    elif 'ETMD' in path or 'SumMe' in path or 'DIEM' in path:
        # path is the path to the video file
        filename = path.split('/')[-1].split('.')[0]
        vid_path = path
        for i in ['ETMD', 'SumMe', 'DIEM']:
            if i in path:
                dataset = i
        path = '/'.join(path.split('/')[:-2])
        map_path = join(path, 'annotation', filename, 'maps')
        command = "ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of default=nw=1:nk=1 {}".format(vid_path).split(" ")
        p = sp.run(command, capture_output=True)
        width, height = p.stdout.decode().split("\n")[:2]
        target_size = (int(int(height) * target_ratio[0]), int(int(width) * target_ratio[1]))
        target_size = [i - (i % quad_size) + quad_size if (i % quad_size) != 0 else i for i in target_size]
        command = 'gst-launch-1.0 filesrc location={0} ! qtdemux ! avdec_h264 ! queue ! videoconvert ! ExampleTransform width={1} height={2} quad_size={3} sal_dir={4} sal_interval={7} ! video/x-raw,width={1},height={2},framerate=10/1,format=RGB ! tee name=t ! queue ! ReverseWarp width={5} height={6} quad_size={3} sal_interval={7} ! video/x-raw,width={5},height={6},framerate=10/1,format=RGB ! queue ! videoconvert ! x264enc pass=quant quantizer=0 speed-preset=ultrafast byte-stream=true ! matroskamux ! filesink location={8} t. ! queue ! videoconvert ! x264enc pass=quant quantizer=0 speed-preset=ultrafast byte-stream=true ! matroskamux ! filesink location={9}'.format(
            vid_path,
            target_size[1], target_size[0],
            quad_size,
            map_path,
            width, height,
            sal_interval,
            join("test/out", dataset + '_raw', filename + "_{}x{}".format(target_size[1], target_size[0]) + ".mkv"),
            join("test/out", dataset + "_compressed_raw", filename + "_{}x{}".format(target_size[1], target_size[0]) + ".mkv"),
        ).split(' ')
        #command = 'gst-launch-1.0 filesrc location={0} ! qtdemux ! avdec_h264 ! queue ! videoconvert ! ExampleTransform width={1} height={2} quad_size={3} sal_dir={4} sal_interval={8} ! video/x-raw,width={1},height={2} ! ReverseWarp width={5} height={6} quad_size={3} sal_interval={8} ! videoconvert ! queue ! pngenc ! multifilesink location={7}'.format(
        #    vid_path, target_size[1], target_size[0], quad_size, map_path, width, height, join("test/out/test", filename + "_{}x{}".format(target_size[1], target_size[0]) + "_%d.png"), sal_interval
        #).split(' ')
        print(' '.join(command))
        p = sp.run(command, capture_output=True)
        print(p.stdout.decode(), p.stderr.decode())
    else:
        pass


def compress(path: str, target_ratio, quad_size: int, sal_interval: int):
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
        target_size = [i - (i % quad_size) + quad_size if (i % quad_size) != 0 else i for i in target_size]
        command = 'gst-launch-1.0 multifilesrc location={0} start-index=1 caps="image/png,framerate=10/1" ! pngdec ! queue ! videoconvert ! ExampleTransform width={1} height={2} quad_size={3} sal_dir={4} sal_interval={5} popt_dir={6} ! video/x-raw,width={1},height={2},framerate=10/1,format=RGB ! queue ! videoconvert ! x264enc interlaced=true pass=quant quantizer=0 speed-preset=ultrafast byte-stream=true ! matroskamux ! filesink location={7}'.format(
            join(img_path, t[0][:-7] + "%03d.png"),
            target_size[1], target_size[0],
            quad_size,
            map_path,
            sal_interval,
            join("test", "out", "UCF_popt", filename),
            join("test/out/UCF_compressed_raw", filename + "_{}x{}".format(target_size[1], target_size[0]) + ".mkv"),
        ).split(' ')
        if not isdir(join("test", "out", "UCF_popt", filename)):
            os.mkdir(join("test", "out", "UCF_popt", filename))
        #command = 'gst-launch-1.0 multifilesrc location={0} start-index=1 caps="image/png,framerate=10/1" ! pngdec ! queue ! videoconvert ! ExampleTransform width={1} height={2} quad_size={3} sal_dir={4} sal_interval={8} ! video/x-raw,width={1},height={2} ! ReverseWarp width={5} height={6} quad_size={3} sal_interval={8} ! videoconvert ! queue ! pngenc ! multifilesink location={7}'.format(
        #    join(img_path, t[0][:-7] + "%03d.png"), target_size[1], target_size[0], quad_size, map_path, width, height, join("test/out/UCF", filename + "_{}x{}".format(target_size[1], target_size[0]) + "_%d.png"), sal_interval
        #).split(' ')
        #print(' '.join(command))
        p = sp.run(command, capture_output=True)
        print(p.stdout.decode(), p.stderr.decode())

    elif 'ETMD' in path or 'SumMe' in path or 'DIEM' in path:
        # path is the path to the video file
        filename = path.split('/')[-1].split('.')[0]
        vid_path = path
        for i in ['ETMD', 'SumMe', 'DIEM']:
            if i in path:
                dataset = i
        path = '/'.join(path.split('/')[:-2])
        map_path = join(path, 'annotation', filename, 'maps')
        command = "ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of default=nw=1:nk=1 {}".format(vid_path).split(" ")
        p = sp.run(command, capture_output=True)
        width, height = p.stdout.decode().split("\n")[:2]
        target_size = (int(int(height) * target_ratio[0]), int(int(width) * target_ratio[1]))
        target_size = [i - (i % quad_size) + quad_size if (i % quad_size) != 0 else i for i in target_size]
        command = 'gst-launch-1.0 filesrc location={0} ! qtdemux ! avdec_h264 ! queue ! videoconvert ! ExampleTransform width={1} height={2} quad_size={3} sal_dir={4} sal_interval={5} popt_dir={6} ! video/x-raw,width={1},height={2},framerate=10/1,format=RGB ! queue ! videoconvert ! x264enc pass=quant quantizer=0 speed-preset=ultrafast byte-stream=true ! matroskamux ! filesink location={7}'.format(
            vid_path,
            target_size[1], target_size[0],
            quad_size,
            map_path,
            sal_interval,
            join("test/out", dataset + '_popt', filename),
            join("test/out", dataset + "_compressed_raw", filename + "_{}x{}".format(target_size[1], target_size[0]) + ".mkv"),
        ).split(' ')
        #command = 'gst-launch-1.0 filesrc location={0} ! qtdemux ! avdec_h264 ! queue ! videoconvert ! ExampleTransform width={1} height={2} quad_size={3} sal_dir={4} sal_interval={8} ! video/x-raw,width={1},height={2} ! ReverseWarp width={5} height={6} quad_size={3} sal_interval={8} ! videoconvert ! queue ! pngenc ! multifilesink location={7}'.format(
        #    vid_path, target_size[1], target_size[0], quad_size, map_path, width, height, join("test/out/test", filename + "_{}x{}".format(target_size[1], target_size[0]) + "_%d.png"), sal_interval
        #).split(' ')
        print(' '.join(command))
        p = sp.run(command, capture_output=True)
        print(p.stdout.decode(), p.stderr.decode())
    else:
        pass

def decompress(path: str, target_ratio, quad_size: int, sal_interval: int, quality: int):
    if 'UCF' in path:
        filename = path.split('/')[-1]
        print("working on {}".format(filename))
        img_path = join(path, 'images')
        t = listdir(img_path)
        t = sorted([i for i in t if i.endswith('.png')])
        command = "ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of default=nw=1:nk=1 {}".format(join(img_path, t[0])).split(" ")
        p = sp.run(command, capture_output=True)
        width, height = p.stdout.decode().split("\n")[:2]
        target_size = (int(int(height) * target_ratio[0]), int(int(width) * target_ratio[1]))
        target_size = [i - (i % quad_size) + quad_size if (i % quad_size) != 0 else i for i in target_size]
        command = "ffmpeg -hide_banner -loglevel error -i {0} -c:v libx264 -profile:v high -level:v 4.0 -preset slow -crf {1} -pix_fmt yuv444p {2}".format(
            join("test/out/UCF_compressed_raw", filename + "_{}x{}".format(target_size[1], target_size[0]) + ".mkv"),
            quality,
            join("test/out/UCF_compressed_from_raw", filename + "_{}x{}_q{:02d}".format(target_size[1], target_size[0], quality) + ".mkv")
        )
        p = sp.run(command, capture_output=True)
        print(p.stdout.decode(), p.stderr.decode())
        command = 'gst-launch-1.0 filesrc location={0} ! matroskademux ! avdec_h264 ! queue ! videoconvert ! ReverseWarp width={1} height={2} quad_size={3} sal_interval={4} popt_dir={5} ! queue ! videoconvert ! x264enc pass=quant quantizer=0 speed-preset=ultrafast byte-stream=true ! matroskamux ! filesink location={6}'.format(
            join("test/out/UCF_compressed_from_raw", filename + "_{}x{}_q{:02d}".format(target_size[1], target_size[0], quality) + ".mkv"),
            width, height,
            quad_size,
            sal_interval,
            join("test", "out", "UCF_popt", filename),
            join("test/out/UCF_decompressed", filename + "_{}x{}_q{:02d}".format(target_size[1], target_size[0], quality) + ".mkv"),
        ).split(' ')
        #command = 'gst-launch-1.0 multifilesrc location={0} start-index=1 caps="image/png,framerate=10/1" ! pngdec ! queue ! videoconvert ! ExampleTransform width={1} height={2} quad_size={3} sal_dir={4} sal_interval={8} ! video/x-raw,width={1},height={2} ! ReverseWarp width={5} height={6} quad_size={3} sal_interval={8} ! videoconvert ! queue ! pngenc ! multifilesink location={7}'.format(
        #    join(img_path, t[0][:-7] + "%03d.png"), target_size[1], target_size[0], quad_size, map_path, width, height, join("test/out/UCF", filename + "_{}x{}".format(target_size[1], target_size[0]) + "_%d.png"), sal_interval
        #).split(' ')
        #print(' '.join(command))
        p = sp.run(command, capture_output=True)
        print(p.stdout.decode(), p.stderr.decode())

def UCF_original(path: str):
    if 'UCF' in path:
        filename = path.split('/')[-1]
        print("working on {}".format(filename))
        img_path = join(path, 'images')
        map_path = join(path, 'maps')
        t = listdir(img_path)
        t = sorted([i for i in t if i.endswith('.png')])
        command = 'ffmpeg -y -hide_banner -loglevel error -r 10/1 -i {0} -start_number 1 {1} {2}'.format(
            join(img_path, t[0][:-7] + "%03d.png"), 
            "-c:v libx264 -preset veryslow -qp 0",
            join("test", "out", "UCF_original", "{}.mp4".format(filename))
        )
        if not isdir(join("test", "out", "UCF_original")):
            os.mkdir(join("test", "out", "UCF_original"))
        p = sp.run(command.split(' '), capture_output=True)
        print(p.stdout.decode(), p.stderr.decode())


if __name__ == "__main__":
    # filelist = sorted(listdir("/home/shupeizhang/Codes/Datasets/saliency/UCF/training/"))
    # filelist = [join("/home/shupeizhang/Codes/Datasets/saliency/UCF/training/", i) for i in filelist]
    # nfilelist = filelist

    filelist = sorted(listdir("/home/shupeizhang/Codes/Datasets/saliency/DIEM/videos"))
    filelist = [join("/home/shupeizhang/Codes/Datasets/saliency/DIEM/videos", i) for i in filelist]
    nfilelist = [filelist[i + 43] for i in [0, 4, 12, 14, 21, 26]] # not finished
    # total 84
    # 0, 1, 2, 3, 4 sal_interval 5 +20 + 40 +31 +11 +43

    # 0, 4, 12, 14, 21, 26
    # 12, 14, 21, 26 sal_interval 2
    
    filelist = [(i, (0.7, 0.7), 12, 5) for i in nfilelist]
    with Pool(processes=2) as pool:
        pool.starmap(process, filelist)
