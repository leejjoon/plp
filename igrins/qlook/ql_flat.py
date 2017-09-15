import numpy as np


def plot_f(jo, fig):
    ax = fig.add_subplot(111)

    ax.plot(jo["y_profile"], "-", color="0.5")


def plot_f2(jo, fig):
    ax = fig.add_subplot(111)

    peak_list = jo["peak_list"]
    ax.plot([j["order"] for j in peak_list],
            [j["peak"] for j in peak_list],
            "o-")

    # ax.set_ylim(ymin=0)


def do_flat(hdu, calib, frametype="on"):

    # from igr_ql.bucket import get_bucket_n_object_name

    # bucket_name, obj_name = get_bucket_n_object_name(obsdate, obsid, band)

    d0 = hdu.data

    # destripe
    if (frametype.lower() == "off") and hdu.header["EXPTIME"] < 10:
        from igrins.libs.destriper import destriper
        d, p = destriper.get_destriped(d0, pattern=64, hori=True,
                                       return_pattern=True)
    else:
        p = np.median(np.hstack([d0[:, :4], d0[:, -4:]]), axis=1)
        d = d0 - p[:, np.newaxis]

    order_map = calib.order_map.copy()

    bg = np.nanmedian(d[order_map == 0])
    d -= bg

    yi, xi = np.indices(d.data.shape)

    x1, x2 = 1024 - 200, 1024 + 200
    xmask = (x1 < xi) & (xi < x2)

    h = np.nanpercentile(d[:, x1:x2], 95, axis=1)

    # by order

    order_map[~xmask] = 0

    min_order = order_map[order_map > 0].min()
    max_order = order_map.max()

    peak_list = []

    for o in range(min_order + 2, max_order - 2):

        omask = order_map == o

        p = np.nanpercentile(d[omask], 95)

        r = dict(order=o, peak=p)
        peak_list.append(r)

    jo = dict(y_profile=h,
              peak_list=peak_list)

    # return jo

    return jo


if __name__ == "__main__":
    import astropy.io.fits as pyfits
    from load_calib import get_calibs

    class Calib(object):
        def __init__(self, band, slit_length_arcsec):

            self.slit_length_arcsec = slit_length_arcsec

            ap, order_map, slitposmap = get_calibs(band)
            self.ap = ap
            self.order_map = order_map[0].data
            self.slitposmap = slitposmap[0]

    band = "K"
    calib = Calib(band, 10.)

    # fn = "/media/igrins128/jjlee/igrins/20170904/SDCK_20170904_0025.fits"

    fn = "/media/igrins128/jjlee/annex/igrins/20170414/SDCK_20170414_0014.fits.gz"
    f = pyfits.open(fn)
    r = do_flat(f[0], calib)

    import matplotlib.pyplot as plt
    if 1:
        fig = plt.figure(figsize=(5, 4))
        fig.subplots_adjust(wspace=0.3)

        plot_f(r, fig)

    if 1:
        fig = plt.figure(figsize=(5, 4))
        plot_f2(r, fig)
