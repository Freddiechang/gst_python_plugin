import subprocess as sp
import re

from os.path import join, getsize, isfile, isdir
from os import listdir

def process(path: str, quality, method):
    videos = []
    if 'UCF' in path:
        filename = path.split('/')[-1]
        print("working on {}".format(filename))
        filelist = [i for i in listdir(join("test9090", "out", "UCF_reverse_{}".format(method))) if i.startswith(filename) and i.endswith("q{:02d}.mp4".format(quality))]
        if len(filelist) == 1:
            videos.append("./test9090/out/UCF_reverse_{}/{}".format(method, filelist[0]))
        if isfile("./test_access_1/out/UCF_original/{}.mp4".format(filename)):
            videos.append("./test_access_1/out/UCF_original/{}.mp4".format(filename))
        if isfile("./test9090/{}/UCF/{}_q{:02d}.mp4".format(method, filename, quality)):
            videos.append("./test9090/{}/UCF/{}_q{:02d}.mp4".format(method, filename, quality))
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
        filelist = [i for i in listdir(join("test", "out", dataset + "_reverse_" + method)) if i.startswith(filename) and i.endswith("q{:02d}.mp4".format(quality))]
        if len(filelist) == 1:
            videos.append("./test/out/{}_reverse_{}/{}".format(dataset, method, filelist[0]))
        if isfile(vid_path):
            videos.append(vid_path)
        if isfile("./test/{}/{}/{}_q{:02d}.mp4".format(method, dataset, filename, quality)):
            videos.append("./test/{}/{}/{}_q{:02d}.mp4".format(method, dataset, filename, quality))
        if len(videos) != 3:
            print("File {}/{}/{} is not complete.\n {}\n".format(method, dataset, filename, videos))
            return -1

    scores = []
    command = 'ffmpeg -i {} -i {} -lavfi "[0][1]libvmaf=phone_model=true:model_path=/home/shupeizhang/Codes/ffmpeg-5.0.1/model/vmaf_v0.6.1.json" -hide_banner -loglevel info  -f null -'.format(
        videos[0],
        videos[1]
    )
    r = sp.run(command, shell=True, capture_output=True)
    scores.append(float(re.findall("\d+\.\d+", r.stderr.decode().split('\n')[-2])[0]))

    command = 'ffmpeg -i {} -i {} -lavfi "[0][1]libvmaf=phone_model=true:model_path=/home/shupeizhang/Codes/ffmpeg-5.0.1/model/vmaf_v0.6.1.json" -hide_banner -loglevel info  -f null -'.format(
        videos[2],
        videos[1]
    )
    r = sp.run(command, shell=True, capture_output=True)
    scores.append(float(re.findall("\d+\.\d+", r.stderr.decode().split('\n')[-2])[0]))

    return scores


if __name__ == "__main__":
    filelist = sorted(listdir("UCF/training/"))
    filelist = [join("UCF/training/", i) for i in filelist]
    nfilelist = filelist
    method = '264'
    filelist = [(i, j, method) for i in nfilelist for j in [10, 18, 26, 32, 38, 44, 50]]
    with open("new_vmaf_{}_2.txt".format(method), 'w') as file:
        file.write("Filename\tQuality\tProposed\t{}\n".format(method))
        for i in filelist:
            r = process(*i)
            file.write("{}\t{}\t{}\t{}\n".format(i[0].split('/')[-1], i[1], r[0], r[1]))
    method = '265'
    filelist = [(i, j, method) for i in nfilelist for j in [10, 18, 26, 32, 38, 44, 50]]
    with open("new_vmaf_{}_2.txt".format(method), 'w') as file:
        file.write("Filename\tQuality\tProposed\t{}\n".format(method))
        for i in filelist:
            r = process(*i)
            file.write("{}\t{}\t{}\t{}\n".format(i[0].split('/')[-1], i[1], r[0], r[1]))
