import subprocess as sp
import re

from os.path import join, getsize, isfile, isdir
from os import listdir

def process(path: str, quality):
    videos = []
    if 'UCF' in path:
        filename = path.split('/')[-1]
        print("working on {}".format(filename))
        filelist = [i for i in listdir(join("test", "out", "UCF_reverse")) if i.startswith(filename) and i.endswith("q{:02d}.mp4".format(quality))]
        if len(filelist) == 1:
            videos.append("./test/out/UCF_reverse/{}".format(filelist[0]))
        if isfile("./test/out/UCF_original/{}.mp4".format(filename)):
            videos.append("./test/out/UCF_original/{}.mp4".format(filename))
        if isfile("./test/264/UCF/{}_q{:02d}.mp4".format(filename, quality)):
            videos.append("./test/264/UCF/{}_q{:02d}.mp4".format(filename, quality))
        if len(videos) != 3:
            print("File {} is not complete.\n {}\n".format(filename, videos))
            return -1
        
    elif 'ETMD' in path or 'SumMe' in path or 'DIEM' in path:
        # path is the path to the video file
        filename = path.split('/')[-1].split('.')[0]
        vid_path = path
        print("working on {}".format(filename))
        for i in ['ETMD', 'SumMe', 'DIEM']:
            if i in path:
                dataset = i
        filelist = [i for i in listdir(join("test", "out", dataset +"_reverse")) if i.startswith(filename) and i.endswith("q{:02d}.mp4".format(quality))]
        if len(filelist) == 1:
            videos.append("./test/out/{}_reverse/{}".format(dataset, filelist[0]))
        if isfile(vid_path):
            videos.append(vid_path)
        if isfile("./test/264/{}/{}_q{:02d}.mp4".format(dataset, filename, quality)):
            videos.append("./test/264/{}/{}_q{:02d}.mp4".format(dataset, filename, quality))
        if len(videos) != 3:
            print("File {}/{} is not complete.\n {}\n".format(dataset, filename, videos))
            return -1

    scores = []
    command = '/home/shupeizhang/Codes/ffmpeg-5.0.1/ffmpeg -i {} -i {} -lavfi "[0][1]libvmaf=model_path=/home/shupeizhang/Codes/ffmpeg-5.0.1/model/vmaf_v0.6.1.json" -hide_banner -loglevel info  -f null -'.format(
        videos[0],
        videos[1]
    )
    r = sp.run(command, shell=True, capture_output=True)
    scores.append(float(re.findall("\d+\.\d+", r.stderr.decode().split('\n')[-2])[0]))

    command = '/home/shupeizhang/Codes/ffmpeg-5.0.1/ffmpeg -i {} -i {} -lavfi "[0][1]libvmaf=model_path=/home/shupeizhang/Codes/ffmpeg-5.0.1/model/vmaf_v0.6.1.json" -hide_banner -loglevel info  -f null -'.format(
        videos[2],
        videos[1]
    )
    r = sp.run(command, shell=True, capture_output=True)
    scores.append(float(re.findall("\d+\.\d+", r.stderr.decode().split('\n')[-2])[0]))

    return scores


if __name__ == "__main__":
    filelist = sorted(listdir("/home/shupeizhang/Codes/Datasets/saliency/UCF/training/"))
    filelist = [join("/home/shupeizhang/Codes/Datasets/saliency/UCF/training/", i) for i in filelist]
    nfilelist = filelist
    filelist = [(i, j) for i in nfilelist for j in [10, 18, 26, 32, 38, 44, 50]]
    with open("vmaf.txt", 'w') as file:
        file.write("Filename\tQuality\tProposed\th264\n")
        for i in filelist:
            r = process(*i)
            file.write("{}\t{}\t{}\t{}\n".format(i[0].split('/')[-1], i[1], r[0], r[1]))