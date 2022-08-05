from os.path import join, getsize, isfile, isdir
from os import listdir
import os
import subprocess as sp
from multiprocessing import Pool
from EWPSNR import ewpsnr

"""
gst-launch-1.0 filesrc location=./in.mp4 ! qtdemux ! avdec_h264 ! queue ! videoconvert  ! ExampleTransform width=504 height=300 quad_size=12 sal_dir=../../Datasets/UCF/training/Diving-Side-005/maps ! video/x-raw,width=504,height=300 ! ReverseWarp width=720 height=404 quad_size=12 ! videoconvert ! pngenc ! multifilesink location=out/%d.png
"""

def process(path: str, target_ratio, quality, out_filename):
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
        filelist = [i for i in listdir(join("test", "out", "UCF_reverse")) if i.startswith(filename) and i.endswith("q{:02d}.mp4".format(quality))]
        if len(filelist) != 1:
            return 1
        if isfile("./test/out/UCF_reverse/{}".format(filelist[0])):
            score = ewpsnr("./test/out/UCF_reverse/{}".format(filelist[0]), 
                img_path, map_path)
            command = "ffprobe -v error -select_streams v:0 -show_entries stream=bit_rate,r_frame_rate -of default=nw=1:nk=1 {}".format("./test/out/UCF_compressed_from_raw/{}".format(filelist[0])).split(" ")
            p = sp.run(command, capture_output=True)
            framerate, bitrate = p.stdout.decode().split('\n')[:2]
            bitrate = int(bitrate)
            framerate = framerate.split('/')
            framerate = int(framerate[0]) / int(framerate[1])
            bpp = bitrate / framerate / int(width) / int(height)
            with open(out_filename, 'a') as f:
                f.write("{}\t{}\t{}\t{}\n".format(
                    filename,
                    quality,
                    bpp,
                    score[1][0]
                ))
            print("{}\t{}\t{}\t{}\n".format(
                    filename,
                    quality,
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
        filelist = [i for i in listdir(join("test", "out", dataset +"_compressed")) if i.startswith(filename) and i.endswith("q{:02d}.mp4".format(quality))]
        if len(filelist) != 1:
            return 1
        if isfile("./test/out/{}_reverse/{}".format(dataset, filelist[0])):
            score = ewpsnr("./test/out/{}_reverse/{}".format(dataset, filelist[0]), 
                vid_path, map_path, 'jpg')
            command = "ffprobe -v error -select_streams v:0 -show_entries stream=bit_rate,r_frame_rate -of default=nw=1:nk=1 {}".format("./test/out/{}_compressed_from_raw/{}".format(dataset, filelist[0])).split(" ")
            p = sp.run(command, capture_output=True)
            framerate, bitrate = p.stdout.decode().split('\n')[:2]
            bitrate = int(bitrate)
            framerate = framerate.split('/')
            framerate = int(framerate[0]) / int(framerate[1])
            bpp = bitrate / framerate / int(width) / int(height)
            with open(out_filename, 'a') as f:
                f.write("{}\t{}\t{}\t{}\n".format(
                    filename,
                    quality,
                    bpp,
                    score[1][0]
                ))
    else:
        pass

def avc_and_hevc(path: str, quality, method):
    if 'UCF' in path:
        filename = path.split('/')[-1]
        print("working on {} q: {}".format(filename, quality))
        img_path = join(path, 'images')
        map_path = join(path, 'maps')
        t = listdir(img_path)
        t = sorted([i for i in t if i.endswith('.png')])
        command = "ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of default=nw=1:nk=1 {}".format(join(img_path, t[0])).split(" ")
        p = sp.run(command, capture_output=True)
        width, height = p.stdout.decode().split("\n")[:2]
        command = "ffmpeg -r 10/1 -i {0} -hide_banner -loglevel error -start_number 1 -c:v libx{1} -crf {2} {3}".format(
            join(img_path, t[0][:-7] + "%03d.png"), 
            method,
            quality,
            join("test", method, "UCF", "{}_q{:02d}.mp4".format(filename, quality))
            )
        if not isdir(join("test", method, "UCF")):
            os.mkdir(join("test", method, "UCF"))
        if not isfile(join("test", method, "UCF", "{}_q{:02d}.mp4".format(filename, quality))):
            sp.run(command.split(' '))
        if isfile(join("test", method, "UCF", "{}_q{:02d}.mp4".format(filename, quality))):
            score = ewpsnr(join("test", method, "UCF", "{}_q{:02d}.mp4".format(filename, quality)), 
                img_path, map_path)
            bpp = getsize(join("test", method, "UCF", "{}_q{:02d}.mp4".format(filename, quality))) * 8 / score[0] / int(width) / int(height)
            with open(method + ".txt", 'a') as f:
                f.write("{}\t{}\t{}\t{}\n".format(
                    filename,
                    quality,
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
        command = "ffmpeg -i {0} -hide_banner -loglevel error -c:v libx{1} -crf {2} {3}".format(
            vid_path, 
            method,
            quality,
            join("test", method, dataset, "{}_q{:02d}.mp4".format(filename, quality))
            )
        if not isdir(join("test", method, dataset)):
            os.mkdir(join("test", method, dataset))
        if not isfile(join("test", method, dataset, "{}_q{:02d}.mp4".format(filename, quality))):
            sp.run(command.split(' '))



        if isfile(join("test", method, dataset, "{}_q{:02d}.mp4".format(filename, quality))):
            score = ewpsnr(join("test", method, dataset, "{}_q{:02d}.mp4".format(filename, quality)), 
                vid_path, map_path, 'jpg')
            bpp = getsize(join("test", method, dataset, "{}_q{:02d}.mp4".format(filename, quality))) * 8 / score[0] / int(width) / int(height)
            with open(method + ".txt", 'a') as f:
                f.write("{}\t{}\t{}\t{}\n".format(
                    filename,
                    quality,
                    bpp,
                    score[1][0]
                ))
    else:
        pass



def avc_and_hevc2(path: str, quality, method):
    if 'UCF' in path:
        filename = path.split('/')[-1]
        print("working on {} q: {}".format(filename, quality))
        img_path = join(path, 'images')
        map_path = join(path, 'maps')
        t = listdir(img_path)
        t = sorted([i for i in t if i.endswith('.png')])
        command = "ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of default=nw=1:nk=1 {}".format(join(img_path, t[0])).split(" ")
        p = sp.run(command, capture_output=True)
        width, height = p.stdout.decode().split("\n")[:2]
        if method == '264':
            encoder = 'x264enc pass=qual quantizer={}'.format(quality)
        elif method == '265':
            encoder = 'x265enc option-string="crf:{}"'.format(quality)
        command = 'gst-launch-1.0 multifilesrc location={0} start-index=1 caps="image/png,framerate=10/1" ! pngdec ! queue ! videoconvert ! queue ! {1} ! mp4mux ! filesink location={2}'.format(
            join(img_path, t[0][:-7] + "%03d.png"), 
            encoder,
            join("test", method, "UCF", "{}_q{:02d}.mp4".format(filename, quality))
            )
        if not isdir(join("test", method, "UCF")):
            os.mkdir(join("test", method, "UCF"))
        if not isfile(join("test", method, "UCF", "{}_q{:02d}.mp4".format(filename, quality))):
            sp.run(command.split(' '))
        if isfile(join("test", method, "UCF", "{}_q{:02d}.mp4".format(filename, quality))):
            score = ewpsnr(join("test", method, "UCF", "{}_q{:02d}.mp4".format(filename, quality)), 
                img_path, map_path)
            bpp = getsize(join("test", method, "UCF", "{}_q{:02d}.mp4".format(filename, quality))) * 8 / score[0] / int(width) / int(height)
            with open(method + ".txt", 'a') as f:
                f.write("{}\t{}\t{}\t{}\n".format(
                    filename,
                    quality,
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
        command = "ffmpeg -i {0} -hide_banner -loglevel error -c:v libx{1} -crf {2} {3}".format(
            vid_path, 
            method,
            quality,
            join("test", method, dataset, "{}_q{:02d}.mp4".format(filename, quality))
            )
        if not isdir(join("test", method, dataset)):
            os.mkdir(join("test", method, dataset))
        if not isfile(join("test", method, dataset, "{}_q{:02d}.mp4".format(filename, quality))):
            sp.run(command.split(' '))



        if isfile(join("test", method, dataset, "{}_q{:02d}.mp4".format(filename, quality))):
            score = ewpsnr(join("test", method, dataset, "{}_q{:02d}.mp4".format(filename, quality)), 
                vid_path, map_path, 'jpg')
            bpp = getsize(join("test", method, dataset, "{}_q{:02d}.mp4".format(filename, quality))) * 8 / score[0] / int(width) / int(height)
            with open(method + ".txt", 'a') as f:
                f.write("{}\t{}\t{}\t{}\n".format(
                    filename,
                    quality,
                    bpp,
                    score[1][0]
                ))
    else:
        pass



def avc_and_hevc_match(path: str, quality, method):
    if 'UCF' in path:
        filename = path.split('/')[-1]
        print("working on {} q: {}".format(filename, quality))
        img_path = join(path, 'images')
        map_path = join(path, 'maps')
        t = listdir(img_path)
        t = sorted([i for i in t if i.endswith('.png')])
        command = "ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of default=nw=1:nk=1 {}".format(join(img_path, t[0])).split(" ")
        p = sp.run(command, capture_output=True)
        width, height = p.stdout.decode().split("\n")[:2]
        # compress the warped version
        filelist = [i for i in listdir(join("test", "out", "UCF_compressed_raw")) if i.startswith(filename) and i.endswith(".mkv")]
        command = "ffmpeg -y -hide_banner -loglevel error -i {0} -c:v libx264 -preset slow -crf {1} -pix_fmt yuv420p {2}".format(
            join("test", "out", "UCF_compressed_raw", filelist[0]),
            quality,
            join("test", "out", "UCF_compressed_from_raw", filelist[0][:-4] + "_q{:02d}.mp4".format(quality))
        )
        p = sp.run(command.split(' '), capture_output=True)
        print(p.stdout.decode(), p.stderr.decode())
        # compress the reverse warped version
        command = "ffmpeg -y -hide_banner -loglevel error -i {0} -c:v libx264 -preset slow -crf {1} -pix_fmt yuv420p {2}".format(
            join("test", "out", "UCF_raw", filelist[0]),
            quality,
            join("test", "out", "UCF_reverse", filelist[0][:-4] + "_q{:02d}.mp4".format(quality))
        )
        p = sp.run(command.split(' '), capture_output=True)
        print(p.stdout.decode(), p.stderr.decode())

        filelist = [i for i in listdir(join("test", "out", "UCF_compressed_from_raw")) if i.startswith(filename) and i.endswith("q{:02d}.mp4".format(quality))]
        if len(filelist) == 1:
            command = "ffprobe -v error -select_streams v:0 -show_entries stream=bit_rate -of default=nw=1:nk=1 {}".format(join("test", "out", "UCF_compressed_from_raw", filelist[0])).split(" ")
            p = sp.run(command, capture_output=True)
            # kbits/sec
            bitrate = int(p.stdout.decode())
            #pass 1
            if method == '264':
                encoder = '-c:v libx264 -b:v {} -pass 1'.format(bitrate)
            elif method == '265':
                encoder = '-c:v libx265 -b:v {} -x265-params pass=1'.format(bitrate)
            command = 'ffmpeg -hide_banner -loglevel error -r 10/1 -i {0} -start_number 1 {1} -f null /dev/null'.format(
                join(img_path, t[0][:-7] + "%03d.png"), 
                encoder
                )
            if not isdir(join("test", method, "UCF")):
                os.mkdir(join("test", method, "UCF"))
            if not isfile(join("test", method, "UCF", "{}_q{:02d}.mp4".format(filename, quality))):
                p = sp.run(command.split(' '), capture_output=True)
                print(p.stdout.decode(), p.stderr.decode())
            #pass 2
            if method == '264':
                encoder = '-c:v libx264 -b:v {} -pass 2'.format(bitrate)
            elif method == '265':
                encoder = '-c:v libx265 -b:v {} -x265-params pass=2'.format(bitrate)
            command = 'ffmpeg -hide_banner -loglevel error -r 10/1 -i {0} -start_number 1 {1} {2}'.format(
                join(img_path, t[0][:-7] + "%03d.png"), 
                encoder,
                join("test", method, "UCF", "{}_q{:02d}.mp4".format(filename, quality))
                )
            if not isfile(join("test", method, "UCF", "{}_q{:02d}.mp4".format(filename, quality))):
                p = sp.run(command.split(' '), capture_output=True)
                print(p.stdout.decode(), p.stderr.decode())

            if isfile(join("test", method, "UCF", "{}_q{:02d}.mp4".format(filename, quality))):
                score = ewpsnr(join("test", method, "UCF", "{}_q{:02d}.mp4".format(filename, quality)), 
                    img_path, map_path)
                command = "ffprobe -v error -select_streams v:0 -show_entries stream=bit_rate,r_frame_rate -of default=nw=1:nk=1 {}".format(join("test", method, "UCF", "{}_q{:02d}.mp4".format(filename, quality))).split(" ")
                p = sp.run(command, capture_output=True)
                framerate, bitrate = p.stdout.decode().split('\n')[:2]
                bitrate = int(bitrate)
                framerate = framerate.split('/')
                framerate = int(framerate[0]) / int(framerate[1])
                bpp = bitrate / framerate / int(width) / int(height)
                with open(method + ".txt", 'a') as f:
                    f.write("{}\t{}\t{}\t{}\n".format(
                        filename,
                        quality,
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
        filelist = [i for i in listdir(join("test", "out", dataset +"_compressed_raw")) if i.startswith(filename) and i.endswith(".mkv")]
        # compress the warped version
        command = "ffmpeg -hide_banner -loglevel error -i {0} -c:v libx264 -preset slow -crf {1} -pix_fmt yuv420p {2}".format(
            join("test", "out", dataset + "_compressed_raw", filelist[0]),
            quality,
            join("test", "out", dataset + "_compressed_from_raw", filelist[0][:-4] + "_q{:02d}.mp4".format(quality))
        )
        p = sp.run(command, capture_output=True)
        print(p.stdout.decode(), p.stderr.decode())
        # compress the reverse warped version
        command = "ffmpeg -hide_banner -loglevel error -i {0} -c:v libx264 -preset slow -crf {1} -pix_fmt yuv420p {2}".format(
            join("test", "out", dataset + "_raw", filelist[0]),
            quality,
            join("test", "out", dataset + "_reverse", filelist[0][:-4] + "_q{:02d}.mp4".format(quality))
        )
        p = sp.run(command, capture_output=True)
        print(p.stdout.decode(), p.stderr.decode())
        filelist = [i for i in listdir(join("test", "out", dataset +"_compressed")) if i.startswith(filename) and i.endswith("q{:02d}.mp4".format(quality))]
        if len(filelist) == 1:
            command = "ffprobe -v error -select_streams v:0 -show_entries stream=bit_rate -of default=nw=1:nk=1 {}".format(join("test", "out", dataset + "_compressed", filelist[0])).split(" ")
            p = sp.run(command, capture_output=True)
            bitrate = int(p.stdout.decode())
            #pass 1
            if method == '264':
                encoder = '-c:v libx264 -b:v {} -pass 1'.format(bitrate)
            elif method == '265':
                encoder = '-c:v libx265 -b:v {} -x265-params pass=1'.format(bitrate)
            command = 'ffmpeg -hide_banner -loglevel error -i {0} -start_number 1 {1} -f null /dev/null'.format(
                vid_path, 
                encoder
                )
            if not isdir(join("test", method, dataset)):
                os.mkdir(join("test", method, dataset))
            if not isfile(join("test", method, dataset, "{}_q{:02d}.mp4".format(filename, quality))):
                p = sp.run(command.split(' '), capture_output=True)
                print(p.stdout.decode(), p.stderr.decode())
            #pass 2
            if method == '264':
                encoder = '-c:v libx264 -b:v {} -pass 2'.format(bitrate)
            elif method == '265':
                encoder = '-c:v libx265 -b:v {} -x265-params pass=2'.format(bitrate)
            command = 'ffmpeg -hide_banner -loglevel error -i {0} -start_number 1 {1} {2}'.format(
                vid_path, 
                encoder,
                join("test", method, dataset, "{}_q{:02d}.mp4".format(filename, quality))
                )
            if not isfile(join("test", method, dataset, "{}_q{:02d}.mp4".format(filename, quality))):
                p = sp.run(command.split(' '), capture_output=True)
                print(p.stdout.decode(), p.stderr.decode())
            

            if isfile(join("test", method, dataset, "{}_q{:02d}.mp4".format(filename, quality))):
                score = ewpsnr(join("test", method, dataset, "{}_q{:02d}.mp4".format(filename, quality)), 
                    vid_path, map_path, 'jpg')
                command = "ffprobe -v error -select_streams v:0 -show_entries stream=bit_rate,r_frame_rate -of default=nw=1:nk=1 {}".format(join("test", method, dataset, "{}_q{:02d}.mp4".format(filename, quality))).split(" ")
                p = sp.run(command, capture_output=True)
                framerate, bitrate = p.stdout.decode().split('\n')[:2]
                bitrate = int(bitrate)
                framerate = framerate.split('/')
                framerate = int(framerate[0]) / int(framerate[1])
                bpp = bitrate / framerate / int(width) / int(height)
                with open(method + ".txt", 'a') as f:
                    f.write("{}\t{}\t{}\t{}\n".format(
                        filename,
                        quality,
                        bpp,
                        score[1][0]
                    ))
    else:
        pass



if __name__ == "__main__":
    filelist = sorted(listdir("/home/shupeizhang/Codes/Datasets/saliency/UCF/training/"))
    filelist = [join("/home/shupeizhang/Codes/Datasets/saliency/UCF/training/", i) for i in filelist]
    nfilelist = filelist

    #filelist = sorted(listdir("/home/shupeizhang/Codes/Datasets/saliency/DIEM/videos"))
    #filelist = [join("/home/shupeizhang/Codes/Datasets/saliency/DIEM/videos", i) for i in filelist]
    # total 84
    # 0, 4, 12, 14, 21, 26
    # +0 +20 +40 +11 +31 +41
    #nfilelist = [filelist[i + 51] for i in [0, 4, 12, 14, 21, 26]]
    filelist = [(i, (0.7, 0.7), j, 'proposed.txt') for i in nfilelist for j in [10, 18, 26, 32, 38, 44, 50]]
    with Pool(processes=1) as pool:
        pool.starmap(process, filelist)



    # filelist = sorted(listdir("/home/shupeizhang/Codes/Datasets/saliency/UCF/training/"))
    # filelist = [join("/home/shupeizhang/Codes/Datasets/saliency/UCF/training/", i) for i in filelist]
    # nfilelist = filelist

    # #filelist = sorted(listdir("/home/shupeizhang/Codes/Datasets/saliency/DIEM/videos"))
    # #filelist = [join("/home/shupeizhang/Codes/Datasets/saliency/DIEM/videos", i) for i in filelist]
    # # total 84
    # # 0, 4, 12, 14, 21, 26
    # # +0 +20 +40 +11 +31 +41
    # #nfilelist = [filelist[i + 51] for i in [0, 4, 12, 14, 21, 26]]
    # filelist = [(i, j, '264') for i in nfilelist for j in range(1, 52, 5)]
    # with Pool(processes=1) as pool:
    #     pool.starmap(avc_and_hevc, filelist)
