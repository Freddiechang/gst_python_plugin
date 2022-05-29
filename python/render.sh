gst-launch-1.0 filesrc location=./1.mp4 ! qtdemux ! avdec_h264 ! queue ! videoconvert ! video/x-raw,width=720,height=480 ! ExampleTransform width=432 height=288 sal_dir=../../Datasets/UCF/training/Walk-Front-008/maps ! video/x-raw,width=432,height=288 ! ReverseWarp width=720 height=480 ! videoconvert ! pngenc ! multifilesink location=%d.png

gst-launch-1.0 -e multifilesrc location="%d.png" caps="image/png,framerate=5/1" ! pngdec ! videoconvert ! queue ! x264enc ! queue ! mp4mux ! filesink location=out.mp4
