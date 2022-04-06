#include "gst_saliency_info_meta.h"

#include "string.h"

static gboolean gst_saliency_info_meta_init(GstMeta *meta, gpointer params, GstBuffer *buffer);
static gboolean gst_saliency_info_meta_transform(GstBuffer *transbuf, GstMeta *meta, GstBuffer *buffer,
                                               GQuark type, gpointer data);


// Register metadata type and returns Gtype
// https://gstreamer.freedesktop.org/data/doc/gstreamer/head/gstreamer/html/gstreamer-GstMeta.html#gst-meta-api-type-register
GType gst_saliency_info_meta_api_get_type(void)
{
    static const gchar *tags[] = {NULL};
    static volatile GType type;
    if (g_once_init_enter (&type)) {
        GType _type = gst_meta_api_type_register("GstSaliencyInfoMetaAPI", tags);
        g_once_init_leave(&type, _type);
    }
    return type;
}



// GstMetaInfo provides info for specific metadata implementation
// https://gstreamer.freedesktop.org/data/doc/gstreamer/head/gstreamer/html/gstreamer-GstMeta.html#GstMetaInfo

const GstMetaInfo *gst_saliency_info_meta_get_info(void)
{
    static const GstMetaInfo *gst_saliency_info_meta_info = NULL;
 
    if (g_once_init_enter (&gst_saliency_info_meta_info)) {
        // Explanation of fields
        // https://gstreamer.freedesktop.org/documentation/design/meta.html#gstmeta1
        const GstMetaInfo *meta = gst_meta_register (GST_SALIENCY_INFO_META_API_TYPE, /* api type */
                                                     "GstSaliencyInfoMeta",           /* implementation type */
                                                     sizeof (GstSaliencyInfoMeta),    /* size of the structure */
                                                     gst_saliency_info_meta_init,
                                                     (GstMetaFreeFunction) NULL,
                                                     gst_saliency_info_meta_transform);
        g_once_init_leave (&gst_saliency_info_meta_info, meta);
    }
    return gst_saliency_info_meta_info;
}


// Meta init function
// 4-th field in GstMetaInfo
static gboolean gst_saliency_info_meta_init(GstMeta *meta, gpointer params, GstBuffer *buffer)
{
    GstSaliencyInfoMeta *gst_saliency_info_meta = (GstSaliencyInfoMeta*)meta;     
    gst_saliency_info_meta->gaussian_count = 0;
    gst_saliency_info_meta->parameters = NULL;
    return TRUE;
}

// Meta transform function
// 5-th field in GstMetaInfo
// https://gstreamer.freedesktop.org/data/doc/gstreamer/head/gstreamer/html/gstreamer-GstMeta.html#GstMetaTransformFunction
static gboolean gst_saliency_info_meta_transform(GstBuffer *transbuf, GstMeta *meta, GstBuffer *buffer,
                                               GQuark type, gpointer data)
{
    GstSaliencyInfoMeta *gst_saliency_info_meta = (GstSaliencyInfoMeta *)meta;
    gst_saliency_add_saliency_info_meta(transbuf, gst_saliency_info_meta->gaussian_count, 
    gst_saliency_info_meta->parameters);
    return TRUE;
}


GstSaliencyInfoMeta* gst_saliency_add_saliency_info_meta(GstBuffer *buffer, guint gaussian_count, gfloat *parameters)
{
    GstSaliencyInfoMeta *gst_saliency_info_meta = NULL;

    // check that gst_buffer valid
    g_return_val_if_fail(GST_IS_BUFFER(buffer), NULL);

    // check that gst_buffer writable
    if ( !gst_buffer_is_writable(buffer))
        return gst_saliency_info_meta;

    // https://gstreamer.freedesktop.org/data/doc/gstreamer/head/gstreamer/html/GstBuffer.html#gst-buffer-add-meta
    gst_saliency_info_meta = (GstSaliencyInfoMeta *) gst_buffer_add_meta (buffer, GST_SALIENCY_INFO_META_INFO, NULL);

    // copy fields to buffer's meta
    gst_saliency_info_meta->gaussian_count = gaussian_count;
    gst_saliency_info_meta->parameters = (gfloat *) malloc(sizeof(gfloat) * gaussian_count);
    memcpy(gst_saliency_info_meta->parameters, parameters, sizeof(gfloat) * gaussian_count);

    return gst_saliency_info_meta;
}


GstSaliencyInfoMeta* gst_saliency_get_saliency_info_meta(GstBuffer *b)
{}

gboolean gst_saliency_remove_saliency_info_meta(GstBuffer *buffer)
{}