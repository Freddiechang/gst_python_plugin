from cgi import test
from os.path import join, getsize, isfile, isdir
from os import listdir
import os
import random
import subprocess as sp
from multiprocessing import Pool

#ffplay -f lavfi -i "movie=out/UCF_reverse/Diving-Side-005_504x288_q50.mp4[v0];movie=out/UCF_reverse/Diving-Side-005_504x288_q50.mp4[v1];movie=264/UCF/Diving-Side-005_q44.mp4[v2];[v0][v1][v2]vstack=inputs=3[v3];[v3]scale=iw/2:ih/2" -hide_banner -autoexit -loglevel error


def process(path: str, quality, scale):
    """
    returns 1 if proposed method is better than 264, 0 otherwise
    """
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
    
    reverse = random.choice([True, False])
    if reverse:
        videos[0], videos[2] = videos[2], videos[0]
    command = 'ffplay -f lavfi -i "movie={0}[v0];movie={1}[v1];movie={2}[v2];[v0][v1][v2]vstack=inputs=3[v3];[v3]scale=iw/{3}:ih/{3}" -hide_banner -autoexit -loglevel error'.format(
        videos[0],
        videos[1],
        videos[2],
        scale
    )
    replay = True
    while replay:
        input("Press enter to proceed.")
        p = sp.run(command, shell=True)
        response = input("0: left is better, 1: right is better, 2: replay")
        while response not in ['0', '1', '2']:
            print("Invalid input. Please try again.")
            response = input("0: left is better, 1: right is better, 2: replay")
        if response == '0':
            replay = False
            return 1 if not reverse else 0
        elif response == '1':
            replay = False
            return 0 if not reverse else 1
        else:
            continue

if __name__ == "__main__":
    filelist = sorted(listdir("/home/shupeizhang/Codes/Datasets/saliency/UCF/training/"))
    filelist = [join("/home/shupeizhang/Codes/Datasets/saliency/UCF/training/", i) for i in filelist]
    nfilelist = filelist

    result = []
    test_id = input("Test id: ")
    filelist = [(i, j, 2) for i in nfilelist for j in [10, 18, 26, 32, 38, 44, 50]]
    with open("response.txt", 'a') as file:
        file.write("ID\tFilename\tQuality\tResult\n")
        for i in filelist:
            r = process(*i)
            file.write("{}\t{}\t{}\t{}\n".format(test_id, i[0].split('/')[-1], i[1], r))
            
        
            
            
        
