#!/usr/bin/python3
# exampleTransform.py
# 2019 Daniel Klamt <graphics@pengutronix.de>

# Inverts a grayscale image in place, requires numpy.
#
# gst-launch-1.0 videotestsrc ! ExampleTransform ! videoconvert ! xvimagesink

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstBase', '1.0')

from gi.repository import Gst, GObject, GstBase

import numpy as np
from os.path import join

from warp import *
from gst_saliency_info_meta import *

Gst.init(None)
FIXED_CAPS = Gst.Caps(Gst.Structure("video/x-raw", format=Gst.ValueList(["RGB"]), 
    width=Gst.IntRange(range(1, 20480)), height=Gst.IntRange(range(1, 20480))))

class ReverseWarp(GstBase.BaseTransform):
    __gstmetadata__ = ('Image Warping', 'Transform',
                      'Warp image using given saliency map', 'freddie')

    __gsttemplates__ = (Gst.PadTemplate.new("src",
                                           Gst.PadDirection.SRC,
                                           Gst.PadPresence.ALWAYS,
                                           FIXED_CAPS),
                       Gst.PadTemplate.new("sink",
                                           Gst.PadDirection.SINK,
                                           Gst.PadPresence.ALWAYS,
                                           FIXED_CAPS))
    __gproperties__ = {
        "width": (GObject.TYPE_INT64,
                 "Target width",
                 "Target width",
                 1,
                 20480,
                 1,  # default
                 GObject.ParamFlags.READWRITE
                 ),

        "height": (GObject.TYPE_INT64,
                "Target height",
                "Target height",
                1,
                20480,
                1,  # default
                GObject.ParamFlags.READWRITE
                ),
        "sal_threshold": (GObject.TYPE_UINT,
                "Saliency threshold",
                "Saliency threshold, uint8",
                0,
                255,
                10,  # default
                GObject.ParamFlags.READWRITE
                ),
        "n_sal_weight": (GObject.TYPE_UINT,
                "Non-Salient weight",
                "Saliency weight for non-salient regions",
                0,
                255,
                5,  # default
                GObject.ParamFlags.READWRITE
                ),
        "quad_size": (GObject.TYPE_UINT,
                "Quad size",
                "Mesh quad size, uint",
                1,
                256,
                8,  # default
                GObject.ParamFlags.READWRITE
                ),
        "sal_interval": (GObject.TYPE_INT64,
                 "Saliency map interval",
                 "Saliency map interval",
                 1,
                 20480,
                 1,  # default
                 GObject.ParamFlags.READWRITE
                 ),
        "popt_dir": (GObject.TYPE_STRING,
                "Saliency popt location",
                "Saliency popt location, string",
                "./", # default
                GObject.ParamFlags.READWRITE
                ),
    }

    def __init__(self) -> None:
        self.outheight = 1
        self.outwidth = 1
        self.threshold = 30
        self.weight = 5
        self.quad_size = 8
        self.frame_count = 0
        self.sal_interval = 1
        self.popt_dir = "./"

    def do_set_property(self, prop: GObject.GParamSpec, value):
        print("invoking do_set_property\n")
        if prop.name == 'width':
            self.outwidth = value
        elif prop.name == 'height':
            self.outheight = value
        elif prop.name == 'sal-threshold':
            self.threshold = value
        elif prop.name == 'n-sal-weight':
            self.weight = value
        elif prop.name == 'quad-size':
            self.quad_size = value
        elif prop.name == 'sal-interval':
            self.sal_interval = value
        elif prop.name == 'popt-dir':
            self.save_popt = value
        else:
            raise AttributeError('unknown property %s' % prop.name)
    
    def do_transform_caps(self, direction: Gst.PadDirection, caps: Gst.Caps, filter_: Gst.Caps) -> Gst.Caps:
        print("invoking do_transform_caps\n")
        caps_ = FIXED_CAPS if direction == Gst.PadDirection.SRC else FIXED_CAPS
    
        # intersect caps if there is transform
        if filter_:
            # create new caps that contains all formats that are common to both
            caps_ = caps_.intersect(filter_)
    
        return caps_

    def do_fixate_caps(self, direction, caps, othercaps):
        print("invoking do_fixate_caps\n")
        if direction == Gst.PadDirection.SRC:
            return othercaps.fixate()
        else:
            so = othercaps.get_structure(0).copy()
            so.fixate_field_nearest_int("width", self.outwidth)
            so.fixate_field_nearest_int("height", self.outheight)
            ret = Gst.Caps.new_empty()
            ret.append_structure(so)
            return ret.fixate()

    def do_set_caps(self, incaps, outcaps):
        print("invoking do_set_caps\n")
        struct = incaps.get_structure(0)
        self.inwidth = struct.get_int("width").value
        self.inheight = struct.get_int("height").value
        self.gaussian = Gaussian((self.outheight, self.outwidth))

        return True

    def update_saliency_map(self, saliency_parameters):
        self.gaussian.from_parameters(saliency_parameters)
        self.centers = self.gaussian.extract_centers()
        sa = self.gaussian.build_map_from_params()
        mask = sa >= self.threshold
        sa = self.gaussian.build_new_map_from_params()
        sa -= self.threshold
        sa = sa.clip(1, 255)
        s = (self.inheight/self.outheight, self.inwidth/self.outwidth)
        self.scale = salient_scale(mask, (self.outheight, self.outwidth), s)
        w = lambda x, y: rescale2(x, *s, (self.outheight, self.outwidth))
        self.mesh = Mesh(sa, mask, (self.inheight, self.inwidth), self.quad_size, w)
        self.mesh.V = self.mesh.warped_vertices
        self.mesh.generate_mapping(self.weight, (self.outheight, self.outwidth), (self.inheight, self.inwidth), self.scale)

    def do_transform(self, inbuffer, outbuffer):
        try:
            with inbuffer.map(Gst.MapFlags.READ) as ininfo:
                # Create a NumPy ndarray from the memoryview and modify it in place:
                A = np.ndarray(shape = (self.inheight, self.inwidth, 3), dtype = np.uint8, buffer = ininfo.data)
                with outbuffer.map(Gst.MapFlags.WRITE) as outinfo:
                    if self.frame_count % self.sal_interval == 0:
                        if self.popt_dir != "./":
                            popt = np.load(join(self.popt_dir, "{}_popt.npy".format(self.frame_count)))
                        else:
                            popt = get_saliency_meta(inbuffer)
                        self.update_saliency_map(popt)
                    B = np.ndarray(shape = (self.outheight, self.outwidth, 3), dtype = np.uint8, buffer = outinfo.data)
                    B[:, :, :] = self.mesh.reverse_warping_remap(A)
                    self.frame_count += 1
                #A *= 0
            return Gst.FlowReturn.OK
        except Gst.MapError as e:
            Gst.error("Mapping error: %s" % e)
            return Gst.FlowReturn.ERROR

GObject.type_register(ReverseWarp)
__gstelementfactory__ = ("ReverseWarp", Gst.Rank.NONE, ReverseWarp)
