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
        filelist = [i for i in listdir(join("test", "out", "UCF_reverse_265")) if i.startswith(filename) and i.endswith("q{:02d}.mp4".format(quality))]
        if len(filelist) == 1:
            videos.append("./test/out/UCF_reverse_265/{}".format(filelist[0]))
        if isfile("./test/out/UCF_original/{}.mp4".format(filename)):
            videos.append("./test/out/UCF_original/{}.mp4".format(filename))
        if isfile("./test/265/UCF/{}_q{:02d}.mp4".format(filename, quality)):
            videos.append("./test/265/UCF/{}_q{:02d}.mp4".format(filename, quality))
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
        response = input("XY -> X, Y (1 - 5) scores for left and right, 6 -> replay\n")
        while len(response) % 2 != 0 and response != "6":
            print("Invalid input. Please try again.")
            response = input("XY -> X, Y (1 - 5) scores for left and right, 6 -> replay\n")
        if response == '6':
            continue
        else:
            replay = False
            score1 = [i for idx, i in enumerate(response) if idx % 2 == 0]
            score2 = [i for idx, i in enumerate(response) if idx % 2 == 1]
            scores = [''.join(score1), ''.join(score2)]
            return scores if not reverse else list(reversed(scores))

if __name__ == "__main__":
    filelist = sorted(listdir("UCF/training/"))
    with open("subjective_list.txt", 'r') as file:
        filter_list = file.readlines()
        filter_list = [i.strip('\n') for i in filter_list]
    filelist = [join("UCF/training/", i) for i in filelist if i in filter_list]
    nfilelist = filelist

    result = []
    test_id = input("Test id: ")
    filelist = [(i, j, 2) for i in nfilelist for j in [32, 38, 44, 50]]
    with open("response_dsis.txt", 'a') as file:
        file.write("ID\tFilename\tQuality\tResult\n")
        for i in filelist:
            r = process(*i)
            file.write("{}\t{}\t{}\t{}\t{}\n".format(test_id, i[0].split('/')[-1], i[1], r[0], r[1]))
            
        
            
            
        
