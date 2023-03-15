import lpips
import numpy as np
import torch
import cv2

from os.path import join, getsize, isfile, isdir
from os import listdir

def process(path: str, quality, loss_fn, method):
    videos = []
    if 'UCF' in path:
        filename = path.split('/')[-1]
        print("working on {}".format(filename))
        filelist = [i for i in listdir(join("test", "out", "UCF_reverse_{}".format(method))) if i.startswith(filename) and i.endswith("q{:02d}.mp4".format(quality))]
        if len(filelist) == 1:
            videos.append("./test/out/UCF_reverse_{}/{}".format(method, filelist[0]))
        if isfile("./test_access_1/out/UCF_original/{}.mp4".format(filename)):
            videos.append("./test_access_1/out/UCF_original/{}.mp4".format(filename))
        if isfile("./test/{}/UCF/{}_q{:02d}.mp4".format(method, filename, quality)):
            videos.append("./test/{}/UCF/{}_q{:02d}.mp4".format(method, filename, quality))
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

    videos = [cv2.VideoCapture(i) for i in videos]
    status = [i.isOpened() == False for i in videos]
    # proposed, h264
    total = torch.zeros(2).cuda()
    if any(status):
        for i in range(3):
            if status[i]:
                print("File {} cannot be opened.\n {}\n".format(filename, videos))
        return -1
    count = 0
    while videos[0].isOpened():
        frames = [i.read() for i in videos]
        if frames[0][0] == True:
            count += 1
            images = [np.expand_dims(np.transpose(i[1], (2, 0, 1)), axis=0) for i in frames]
            images = np.array(images) / 255. * 2 - 1
            images = torch.Tensor(images).cuda()
            test_images = torch.cat([images[0], images[2]])
            ref_images = torch.cat([images[1], images[1]])
            total += loss_fn.forward(ref_images, test_images).squeeze()
        else:
            break
    return (total / count).detach().cpu().numpy()


if __name__ == "__main__":
    filelist = sorted(listdir("/home/shupeizhang/Codes/Datasets/saliency/UCF/training/"))
    filelist = [join("/home/shupeizhang/Codes/Datasets/saliency/UCF/training/", i) for i in filelist]
    nfilelist = filelist
    method = '264'
    with torch.no_grad():
        loss_fn = lpips.LPIPS(net='alex').cuda()
        filelist = [(i, j, loss_fn, method) for i in nfilelist for j in [10, 18, 26, 32, 38, 44, 50]]
        with open("new_lpips_{}_2.txt".format(method), 'w') as file:
            file.write("Filename\tQuality\tProposed\t{}\n".format(method))
            for i in filelist:
                r = process(*i)
                file.write("{}\t{}\t{}\t{}\n".format(i[0].split('/')[-1], i[1], r[0], r[1]))
    method = '265'
    with torch.no_grad():
        loss_fn = lpips.LPIPS(net='alex').cuda()
        filelist = [(i, j, loss_fn, method) for i in nfilelist for j in [10, 18, 26, 32, 38, 44, 50]]
        with open("new_lpips_{}_2.txt".format(method), 'w') as file:
            file.write("Filename\tQuality\tProposed\t{}\n".format(method))
            for i in filelist:
                r = process(*i)
                file.write("{}\t{}\t{}\t{}\n".format(i[0].split('/')[-1], i[1], r[0], r[1]))
