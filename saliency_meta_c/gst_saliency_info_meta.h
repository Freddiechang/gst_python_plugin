/*
reference: https://github.com/jackersson/gst-python-hacks/blob/master/gst-metadata
*/
#ifndef __GST_SALIENCY_INFO_META_H__
#define __GST_SALIENCY_INFO_META_H__
 
#include <gst/gst.h>
 
 
G_BEGIN_DECLS
 
typedef enum {
    GST_SALIENCY_INFO_META_PARTIAL_RELIABILITY_NONE,
    GST_SALIENCY_INFO_META_PARTIAL_RELIABILITY_TTL,
    GST_SALIENCY_INFO_META_PARTIAL_RELIABILITY_BUF,
    GST_SALIENCY_INFO_META_PARTIAL_RELIABILITY_RTX 
} GstSaliencyInfoMetaPartiallyReliability;
 
// Api Type
// 1-st field of GstMetaInfo
#define GST_SALIENCY_INFO_META_API_TYPE (gst_saliency_info_meta_api_get_type())
#define GST_SALIENCY_INFO_META_INFO     (gst_saliency_info_meta_get_info())
 
typedef struct _GstSaliencyInfoMeta  GstSaliencyInfoMeta;



struct _GstSaliencyInfoMeta {

    // Required as it is base structure for metadata
    // https://gstreamer.freedesktop.org/data/doc/gstreamer/head/gstreamer/html/gstreamer-GstMeta.html
    GstMeta meta;  

    // Custom fields
    guint gaussian_count;
    gfloat *parameters;
};  


GType gst_saliency_info_meta_api_get_type(void);
 
GST_EXPORT
const GstMetaInfo * gst_saliency_info_meta_get_info(void);
 
GST_EXPORT
GstSaliencyInfoMeta* gst_saliency_add_saliency_info_meta(GstBuffer *buffer, guint gaussian_count, gfloat *parameters);

GST_EXPORT
gboolean gst_saliency_remove_saliency_info_meta(GstBuffer *buffer);

GST_EXPORT 
GstSaliencyInfoMeta* gst_saliency_get_saliency_info_meta(GstBuffer *b);
 
G_END_DECLS
 
#endif /* __GST_BUFFER_INFO_META_H__ */