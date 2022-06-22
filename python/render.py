from os.path import join, isfile, isdir
from os import listdir
import subprocess as sp
from multiprocessing import Pool

"""
gst-launch-1.0 filesrc location=./in.mp4 ! qtdemux ! avdec_h264 ! queue ! videoconvert  ! ExampleTransform width=504 height=300 quad_size=12 sal_dir=../../Datasets/UCF/training/Diving-Side-005/maps ! video/x-raw,width=504,height=300 ! ReverseWarp width=720 height=404 quad_size=12 ! videoconvert ! pngenc ! multifilesink location=out/%d.png
"""

def process(path: str, target_ratio, quad_size: int, sal_interval: int, quality: int):
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
        command = 'gst-launch-1.0 multifilesrc location={0} start-index=1 caps="image/png,framerate=10/1" ! pngdec ! queue ! videoconvert ! ExampleTransform width={1} height={2} quad_size={3} sal_dir={4} sal_interval={8} ! video/x-raw,width={1},height={2} ! tee name=t ! queue ! ReverseWarp width={5} height={6} quad_size={3} sal_interval={8} ! videoconvert ! queue ! x264enc pass=qual quantizer={9} ! queue ! mp4mux ! filesink location={7} t. ! videoconvert ! queue ! x264enc pass=qual quantizer={9} ! queue ! mp4mux ! filesink location={10}'.format(
            join(img_path, t[0][:-7] + "%03d.png"),
            target_size[1], target_size[0],
            quad_size,
            map_path,
            width, height,
            join("test/out/UCF", filename + "_{}x{}_q{:02d}".format(target_size[1], target_size[0], quality) + ".mp4"),
            sal_interval,
            quality,
            join("test/out/UCF_compressed", filename + "_{}x{}_q{:02d}".format(target_size[1], target_size[0], quality) + ".mp4"),
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
        command = 'gst-launch-1.0 filesrc location={0} ! qtdemux ! avdec_h264 ! queue ! videoconvert ! ExampleTransform width={1} height={2} quad_size={3} sal_dir={4} sal_interval={8} ! video/x-raw,width={1},height={2} ! tee name=t ! queue ! ReverseWarp width={5} height={6} quad_size={3} sal_interval={8} ! videoconvert ! queue ! x264enc pass=qual quantizer={9} ! queue ! mp4mux ! filesink location={7} t. ! videoconvert ! queue ! x264enc pass=qual quantizer={9} ! queue ! mp4mux ! filesink location={10}'.format(
            vid_path,
            target_size[1], target_size[0],
            quad_size,
            map_path,
            width, height,
            join("test/out", dataset, filename + "_{}x{}_q{:02d}".format(target_size[1], target_size[0], quality) + ".mp4"),
            sal_interval,
            quality,
            join("test/out", dataset + "_compressed", filename + "_{}x{}_q{:02d}".format(target_size[1], target_size[0], quality) + ".mp4"),
        ).split(' ')
        #command = 'gst-launch-1.0 filesrc location={0} ! qtdemux ! avdec_h264 ! queue ! videoconvert ! ExampleTransform width={1} height={2} quad_size={3} sal_dir={4} sal_interval={8} ! video/x-raw,width={1},height={2} ! ReverseWarp width={5} height={6} quad_size={3} sal_interval={8} ! videoconvert ! queue ! pngenc ! multifilesink location={7}'.format(
        #    vid_path, target_size[1], target_size[0], quad_size, map_path, width, height, join("test/out/test", filename + "_{}x{}".format(target_size[1], target_size[0]) + "_%d.png"), sal_interval
        #).split(' ')
        print(' '.join(command))
        p = sp.run(command, capture_output=True)
        print(p.stdout.decode(), p.stderr.decode())
    else:
        pass

if __name__ == "__main__":
    # filelist = listdir("/home/shupeizhang/Codes/Datasets/saliency/UCF/training/")
    # filelist = [join("/home/shupeizhang/Codes/Datasets/saliency/UCF/training/", i) for i in filelist]
    # nfilelist = filelist

    filelist = sorted(listdir("/home/shupeizhang/Codes/Datasets/saliency/DIEM/videos"))
    filelist = [join("/home/shupeizhang/Codes/Datasets/saliency/DIEM/videos", i) for i in filelist]
    # total 84
    # 0, 4, 12, 14, 21, 26
    # +0
    nfilelist = [filelist[i] for i in [0, 4, 12, 14, 21, 26]]
    filelist = [(i, (0.7, 0.7), 12, 5, j) for i in nfilelist for j in [10, 22, 34, 46, 51]]
    with Pool(processes=2) as pool:
        pool.starmap(process, filelist)
