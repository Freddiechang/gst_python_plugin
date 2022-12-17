gst-launch-1.0 filesrc location=./1.mp4 ! qtdemux ! avdec_h264 ! queue ! videoconvert ! video/x-raw,width=720,height=480 ! ExampleTransform width=432 height=288 sal_dir=../../Datasets/UCF/training/Walk-Front-008/maps ! video/x-raw,width=432,height=288 ! ReverseWarp width=720 height=480 ! videoconvert ! pngenc ! multifilesink location=%d.png

gst-launch-1.0 -e multifilesrc location="%d.png" caps="image/png,framerate=5/1" ! pngdec ! videoconvert ! queue ! x264enc ! queue ! mp4mux ! filesink location=out.mp4


gst-launch-1.0 multifilesrc location=/home/shupeizhang/Codes/Datasets/saliency/UCF/training/Walk-Front-013/images/Walk-Front_013_%03d.png start-index=1 stop-index=21 caps="image/png,framerate=10/1" ! pngdec ! queue ! videoconvert ! ExampleTransform width=504 height=336 quad_size=8 sal_dir=/home/shupeizhang/Codes/Datasets/saliency/UCF/training/Walk-Front-013/maps sal_interval=5 ! video/x-raw,width=504,height=336,framerate=10/1,format=RGB ! queue ! ReverseWarp width=720 height=480 quad_size=8 sal_interval=5 ! video/x-raw,width=720,height=480,framerate=10/1,format=RGB ! queue ! videoconvert ! x264enc pass=quant quantizer=0 speed-preset=ultrafast byte-stream=true ! matroskamux ! filesink location=1.mkv




gst-launch-1.0 multifilesrc location=/home/shupeizhang/Codes/Datasets/saliency/UCF/training/Walk-Front-013/images/Walk-Front_013_%03d.png start-index=1 stop-index=21 caps="image/png,framerate=10/1" ! pngdec ! queue ! videoconvert ! ExampleTransform width=504 height=336 quad_size=8 sal_dir=/home/shupeizhang/Codes/Datasets/saliency/UCF/training/Walk-Front-013/maps sal_interval=5 ! video/x-raw,width=504,height=336,framerate=10/1,format=RGB ! tee name=t ! queue ! ReverseWarp width=720 height=480 quad_size=8 sal_interval=5 ! video/x-raw,width=720,height=480,framerate=10/1,format=RGB ! queue ! videoconvert ! x264enc pass=quant quantizer=0 speed-preset=ultrafast byte-stream=true ! matroskamux ! filesink location=1.mkv t. ! queue ! videoconvert ! x264enc pass=quant quantizer=0 speed-preset=ultrafast byte-stream=true ! matroskamux ! filesink location=2.mkv
