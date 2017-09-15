def get_bucket_n_object_name(obsdate, obsid, band, ext=None):
    bucket_name = obsdate
    if ext is None:
        fmt = "SDC{band}_{obsdate}_{obsid:04d}"
    else:
        fmt = "SDC{band}_{obsdate}_{obsid:04d}.{ext}"

    object_name = fmt.format(**locals())

    return bucket_name, object_name
