import numpy as np
import scipy.ndimage as ni

from matplotlib.figure import Figure
from mpl_toolkits.axes_grid1 import Grid

# slit_length_arcsec = 10.


def _rebin(x, y, bins):
    bx, _ = np.histogram(x, bins=bins, weights=y)
    bn, _ = np.histogram(x, bins=bins)

    return 0.5 * (bins[:-1] + bins[1:]), bx / bn


def _measure_height_width(xxm, yym, bg_percentile=50):

    bg = np.nanpercentile(yym, bg_percentile)

    yym = yym - bg
    yym[yym < 0] = 0.

    max_indx = np.argmax(yym)
    max_x = xxm[max_indx]
    height = yym[max_indx]

    # height_mask = yym > 0.5 * height
    # weighted_x = np.sum(xxm[height_mask] * yym[height_mask]) \
    #              / np.sum(yym[height_mask])

    bin_dx = xxm[1:] - xxm[:-1]
    bin_height = .5 * (yym[1:] + yym[:-1])
    equivalent_width = np.sum(bin_height * bin_dx) / height

    return bg, max_x, height, equivalent_width


def do_ql_stellar(hdu, calib):

    order_map = calib.order_map
    ap = calib.ap

    slit_length_arcsec = calib.slit_length_arcsec

    inimage = hdu

    # TODO : should include destriping here

    min_order = order_map[order_map > 0].min()
    max_order = order_map.max()

    yi, xi = np.indices(inimage.data.shape)

    x1, x2 = 1024 - 200, 1024 + 200
    xmask = (x1 < xi) & (xi < x2)

    smoothed_profiles = []

    for o in range(min_order + 2, max_order - 2):
        # o = 112

        omask = order_map == o
        msk = omask & xmask

        yc = ap(o, ap.xi, 0.5)
        yh = np.abs(ap(o, ap.xi, 0.) - ap(o, ap.xi, 1.))
        # yic = np.ma.array((yi - yc), mask=~msk).filled(np.nan)

        xx, yy = ((yi - yc) / yh)[msk], inimage.data[msk]
        indx = np.argsort(xx)

        slit_length_in_pixel = yh[int(len(yh)*0.5)]

        xxm = xx[indx]
        n = int(len(xxm) / 100.)
        yym = ni.median_filter(yy[indx], n)

        r = dict(x=xxm, y=yym,
                 smoothing_length=n,
                 slit_length_arcsec=slit_length_arcsec)

        smoothed_profiles.append((o, r))

    per_order = dict(slit_length_arcsec=slit_length_arcsec)

    l = per_order["50%"] = []

    for o, xy in smoothed_profiles:

        xxm, yym = xy["x"], xy["y"]
        n = xy["smoothing_length"]

        r = dict(x_sampled=xxm[::n],
                 y_sampled=yym[::n])

        (bg, max_x, height,
         equivalent_width) = _measure_height_width(xxm, yym, 50)

        r.update(bg=bg,
                 height=height,
                 equivalent_width=equivalent_width,
                 slit_length_in_pixel=slit_length_in_pixel)

        l.append((o, r))

    bins = np.linspace(-0.5, 0.5, 128)

    ww = []
    for o, xy in smoothed_profiles:

        xxm, yym = xy["x"], xy["y"]
        _, w = _rebin(xxm, yym, bins)
        ww.append(w)

    ww0 = np.array(ww).sum(axis=0)

    bins0 = 0.5 * (bins[1:] + bins[:-1])
    (bg, max_x, height,
     equivalent_width) = _measure_height_width(bins0, ww0, 50)

    stacked = dict(slit_length_arcsec=slit_length_arcsec)

    r = dict(bg=bg, max_x=max_x * slit_length_arcsec,
             height=height,
             equivalent_width=equivalent_width * slit_length_arcsec,
             xx=bins0 * slit_length_arcsec, yy=ww0)

    stacked["50%"] = r

    return dict(smoothed_profiles=smoothed_profiles,
                stacked=stacked,
                per_order=per_order)


def do_figure_stacked_profile(jo, calib, fig=None):

    stacked = jo["stacked"]["50%"]

    if fig is None:
        fig = Figure(figsize=(4, 4))

    ax1 = fig.add_subplot(111)

    ax1.axhline(0, color="0.8", ls="--")
    ax1.plot(stacked["xx"], stacked["yy"] - stacked["bg"])

    ax1.errorbar([stacked["max_x"]], [.5*stacked["height"]],
                 xerr=.5*stacked["equivalent_width"],
                 yerr=.5*stacked["height"])

    ax1.set_xlabel("slit length")
    ax1.set_ylabel("count / pixel")
    ax1.tick_params(labelleft=False)

    return fig


def do_figure_profile_per_order(jo, calib, fig=None):

    # smoothed_profiles = jo["smoothed_profiles"]
    stats = jo["per_order"]["50%"]

    slit_length_arcsec = calib.slit_length_arcsec

    if fig is None:
        fig = Figure(figsize=(8, 4))

    ax1 = fig.add_subplot(111)

    bins = np.linspace(-0.5, 0.5, 128)

    for o, k in stats:
        bin_center, w = _rebin(k["x_sampled"], k["y_sampled"], bins)
        m = np.isfinite(w)
        ax1.plot(bin_center[m] * slit_length_arcsec,
                 w[m] - k["bg"], "-", label=o)

    ax1.set_xlabel("slit length")
    ax1.set_ylabel("count / pixel")

    return fig


def do_figure_stat_per_order(jo, calib, fig=None):

    # smoothed_profiles = jo["smoothed_profiles"]
    stats = jo["per_order"]["50%"]

    slit_length_arcsec = calib.slit_length_arcsec

    if fig is None:
        fig = Figure(figsize=(8, 4))

    grid = Grid(fig, 111, (3, 1), share_y=False, axes_pad=0.15)

    ax31 = grid[0]
    ax32 = grid[1]
    ax33 = grid[2]

    for o, k in stats:
        ax31.plot(o, k["height"], "o")

    bg_line, = ax31.plot([o for (o, _) in stats],
                         [_["bg"] for (o, _) in stats], color="0.8",
                         ls="--")
    ax31.legend([bg_line], ["background"], loc=1)

    for o, k in stats:
        ax32.plot(o, k["equivalent_width"] * slit_length_arcsec, "o")

    for o, k in stats:
        v = (k["height"] * k["equivalent_width"]
             * k["slit_length_in_pixel"] * 3.5)
        ax33.plot(o, v**.5, "o")

    ax33.set_xlabel("order number")

    ax31.set_ylabel("peak count\n/ piexl")
    ax32.set_ylabel("FWHM [\"]")
    ax33.set_ylabel("(total counts\nper RE)^1/2")

    return fig


__all__ = ["do_ql_stellar",
           "do_figure_stacked_profile",
           "do_figure_profile_per_order", "do_figure_stat_per_order"]


if __name__ == "__main__":
    class Calib(object):
        def __init__(self, band, slit_length_arcsec):

            self.slit_length_arcsec = slit_length_arcsec

            from load_calib import get_calibs

            ap, order_map, slitposmap = get_calibs(band)
            self.ap = ap
            self.order_map = order_map[0].data
            self.slitposmap = slitposmap[0]

    band = "K"
    calib = Calib(band, 10.)

    import astropy.io.fits as pyfits
    fn = "/media/igrins128/jjlee/igrins/20170903/SDCK_20170903_0151.fits"
    f = pyfits.open(fn)
    r = do_ql_stellar(f[0], calib)

    import matplotlib.pyplot as plt
    if 1:
        fig = plt.figure(figsize=(5, 4))
        fig.subplots_adjust(wspace=0.3)

        do_figure_stacked_profile(r, calib, fig=fig)

    if 1:
        fig = plt.figure(figsize=(5, 4))
        do_figure_profile_per_order(r, calib, fig=fig)

    if 1:
        fig = plt.figure(figsize=(5, 4))
        do_figure_stat_per_order(r, calib, fig=fig)

    plt.show()
