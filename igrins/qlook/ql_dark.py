import numpy as np

from astropy.modeling import models, fitting

from load_calib import add_path


def fit_2gauss_dark(x, y, two_comp=False):
    # it seems like it has 2 component, narrow(std=0.2) and broad(std=2)

    w = y**.5

    fit_t = fitting.LevMarLSQFitter()

    g0 = models.Gaussian1D(amplitude=1., mean=0, stddev=2.)

    if two_comp:
        g0 = models.Gaussian1D(amplitude=1., mean=0, stddev=2.)
        g0.mean.fixed = True

        # mask out the narrow component dominant range
        m = (x < -1) | (1 < x)

        t1 = fit_t(g0, x[m], y[m], weights=w[m])

        # now fix t1, and do 2 component fit
        t1.stddev.fixed = True
        t1.amplitude.fixed = True

        g1 = models.Gaussian1D(amplitude=1., mean=0., stddev=0.1)
        g1.mean.fixed = True

        g2 = g1 + t1

        t2 = fit_t(g2, x, y, weights=w)

        # free everything and fit again
        t2.stddev_0.fixed = False
        t2.stddev_1.fixed = False
        t2.mean_0.fixed = False
        t2.mean_1.fixed = False

        t3 = fit_t(t2, x, y, weights=w)
    else:
        g0 = models.Gaussian1D(amplitude=y.max(), mean=0, stddev=3.)
        g0.mean.fixed = True
        g0.amplitude.fixed = True

        t1 = fit_t(g0, x, y, weights=w)

        t1.mean.fixed = False
        t1.amplitude.fixed = False
        t3 = fit_t(t1, x, y, weights=w)

    return t3


def plot_model(ax, x, y, m):
    ax.plot(x, y, "-", color="r", lw="0.5")
    try:
        for m1 in m:
            ax.plot(x, m1(x), "-", color="0.8")
    except TypeError:
        pass

    ax.plot(x, m(x), "-", color="k")


def jsonize_model(m):
    j = dict(model_name=m.__class__.__name__,
             params=dict(zip(m.param_names, m.parameters)))

    return j


def do_dark(hdu, calib):

    d = hdu.data

    order_map = calib.order_map.copy()

    # if (np.nanpercentile(d, 98) < 30):
    if hdu.header["EXPTIME"] < 60:
        from igrins.libs.destriper import destriper
        d_destriped, p = destriper.get_destriped(d, pattern=64, hori=True,
                                                 return_pattern=True,
                                                 remove_vertical=False,
                                                 mask=(order_map == 0))
        do_twocomp = True
    else:
        v = np.median(d, axis=0)
        d1 = d - v
        p = np.median(np.hstack([d1[:, :4], d1[:, -4:]]), axis=1)
        d_destriped = d1 - p[:, np.newaxis]
        do_twocomp = False

    bg = np.nanmedian(d_destriped[order_map == 0])
    d_destriped -= bg

    ds = 4
    f = d_destriped[ds:-ds, ds:-ds].flat
    r = np.histogram(f, bins=np.arange(-31, 31, 0.04))

    x = 0.5*(r[1][:-1] + r[1][1:])
    y = r[0]

    m = fit_2gauss_dark(x, y, two_comp=False)

    x0 = abs(m.mean.value)
    dx = abs(m.stddev.value) * 10

    f_std = ((f[(-dx < f) & (f < x0)] - x0)**2).mean()**.5

    jo = dict(std=float(f_std),
              model=jsonize_model(m),
              _raw_data_fig1=dict(x=x, y=y, m=m))

    if do_twocomp and (calib.band in ["H", "K"]):

        m = fit_2gauss_dark(x, y, two_comp=True)

        dx = max(abs(m1.stddev.value) for m1 in m) * 10
        f_std = f[(-dx < f) & (f < dx)].std()

        jo["2nd_comp"] = dict(std=float(f_std),
                              model=jsonize_model(m))

        jo["_raw_data_fig2"] = dict(x=x, y=y, m=m)

    return jo


def plot_f(jo, fig):
    ax = fig.add_subplot(111)

    _ = jo["_raw_data_fig1"]

    plot_model(ax, _["x"], _["y"], _["m"])


def plot_f2(jo, fig):
    ax = fig.add_subplot(111)

    _ = jo["_raw_data_fig2"]

    plot_model(ax, _["x"], _["y"], _["m"])


# def plot_f():
#         fig = Figure()
#         plot_model(fig, x, y, m)
#         s = fig_to_png_string(fig)
#         binaries["dark_hist_2comp.png"] = s



# def do_dark__(hdu, obsdate, obsid, band, obstype, frametype, **aux):

#     # from igr_ql.bucket import get_bucket_n_object_name

#     # bucket_name, obj_name = get_bucket_n_object_name(obsdate, obsid, band)

#     binaries = dict()

#     d = hdu.data

#     # if (np.nanpercentile(d, 98) < 30):
#     if hdu.header["EXPTIME"] < 5:
#         from igrins.libs.destriper import destriper
#         d_destriped, p = destriper.get_destriped(d, pattern=64, hori=True,
#                                                  return_pattern=True)
#         do_twocomp = True
#     else:
#         p = np.median(np.hstack([d[:, :4], d[:, -4:]]), axis=1)
#         d_destriped = d - p[:, np.newaxis]
#         do_twocomp = False

#     ds = 4
#     f = d_destriped[ds:-ds, ds:-ds].flat
#     r = np.histogram(f, bins=np.arange(-31, 31, 0.04))

#     x = 0.5*(r[1][:-1] + r[1][1:])
#     y = r[0]

#     m = fit_2gauss_dark(x, y, two_comp=False)

#     fig = Figure()
#     plot_model(fig, x, y, m)
#     s = fig_to_png_string(fig)
#     binaries["dark_hist_1comp.png"] = s

#     x0 = abs(m.mean.value)
#     dx = abs(m.stddev.value) * 10

#     f_std = ((f[(-dx < f) & (f < x0)] - x0)**2).mean()**.5

#     jo = dict(std=float(f_std),
#               model=jsonize_model(m))

#     if do_twocomp and band in ["H", "K"]:

#         m = fit_2gauss_dark(x, y, two_comp=True)

#         fig = Figure()
#         plot_model(fig, x, y, m)
#         s = fig_to_png_string(fig)
#         binaries["dark_hist_2comp.png"] = s

#         dx = max(abs(m1.stddev.value) for m1 in m) * 10
#         f_std = f[(-dx < f) & (f < dx)].std()

#         jo["2nd_comp"] = dict(std=float(f_std),
#                               model=jsonize_model(m))

#     return jo, binaries


# # def process_band(utdate, recipe_name, band,
# #                  obsids, frametypes, config_name):

# #     from igrins import get_caldb, get_obsset

# #     caldb = get_caldb(config_name, utdate, ensure_dir=True)
# #     obsset = get_obsset(caldb, band, recipe_name, obsids, frametypes)

# #     hdu_list = obsset.get_hdu_list()

# #     # just use the first one
# #     d = hdu_list[0].data - hdu_list[1].data
# #     # d = hdu_list[0].data

# #     from igrins.libs.destriper import destriper
# #     d_destriped, p = destriper.get_destriped(d, pattern=64, hori=True,
# #                                              return_pattern=True)

# #     ds = 4
# #     f = d_destriped[ds:-ds, ds:-ds].flat
# #     r = np.histogram(f, bins=np.arange(-31, 31, 0.04))

# #     x = 0.5*(r[1][:-1] + r[1][1:])
# #     y = r[0]

# #     m = fit_2gauss_dark(x, y, two_comp=False)

# #     plot_model(x, y, m)

# #     dx = abs(m.stddev.value) * 10

# #     f_std = f[(-dx < f) & (f < dx)].std()

# #     j = dict(std=float(f_std),
# #              model=jsonize_model(m))

# #     j_xy = dict(x=list(x), y=list(y))

# #     if band in ["H", "K"]:

# #         m = fit_2gauss_dark(x, y, two_comp=True)

# #         plot_model(x, y, m)

# #         dx = max(abs(m1.stddev.value) for m1 in m) * 10
# #         f_std = f[(-dx < f) & (f < dx)].std()

# #         j["2nd_comp"] = dict(std=float(f_std),
# #                              model=jsonize_model(m))

# #     print(f_std)
# #     json.dump(j, open("test.json", "w"))
# #     json.dump(j, open("test.json", "w"))
# #     json.dump(j_xy, open("test_xy.json", "w"))



# # def process_band_flat_off(utdate, recipe_name, band,
# #                           obsids, frametypes, config_name):

# #     from igrins import get_caldb, get_obsset

# #     caldb = get_caldb(config_name, utdate, ensure_dir=True)
# #     obsset = get_obsset(caldb, band, recipe_name, obsids, frametypes)

# #     hdu_list = obsset.get_hdu_list()

# #     # just use the first one
# #     # d = hdu_list[0].data - hdu_list[1].data
# #     d = hdu_list[0].data

# #     from igrins.libs.destriper import destriper
# #     m = np.zeros(d.shape, dtype=bool)
# #     m[:1024, ] = True


# #     # r = caldb.load_resource_for(obsset.basename, "bias_mask")
# #     # m1 = pyfits.open("../calib/primary/20150305/FLAT_SDCK_20150305_0021.bias_mask.fits")[0].data > 0.5


# #     # dd = np.vstack([d[:4], d[-4:]])
# #     # h = np.median(dd, axis=0)

# #     d_destriped, p = destriper.get_destriped(d, mask=m,
# #                                              pattern=64, hori=False,
# #                                              remove_vertical=False,
# #                                              return_pattern=True)


# #     im = d_destriped[:, 1024-128:1024+128]

# #     plot(np.median(im, axis=1))


# #     # im = d[:, 1024-128:1024+128]

# #     # plot(np.median(im, axis=1))


# # def process_band_simple(utdate, recipe_name, band,
# #                         obsids, frametypes, config_name):

# #     from igrins import get_caldb, get_obsset

# #     caldb = get_caldb(config_name, utdate, ensure_dir=True)
# #     obsset = get_obsset(caldb, band, recipe_name, obsids, frametypes)

# #     hdu_list = obsset.get_hdu_list()

# #     # just use the first one
# #     # d = hdu_list[0].data - hdu_list[1].data
# #     d = hdu_list[0].data

# #     from igrins.libs.destriper import destriper
# #     m = np.zeros(d.shape, dtype=bool)
# #     m[:1024, ] = True


# #     # r = caldb.load_resource_for(obsset.basename, "bias_mask")
# #     # m = pyfits.open("../calib/primary/20150305/FLAT_SDCK_20150305_0021.bias_mask.fits")[0].data > 0.5

# #     # dd = np.vstack([d[:4], d[-4:]])
# #     # h = np.median(dd, axis=0)

# #     if 1:
# #         # readout patter using the boundary pixels
# #         dd = np.hstack([d[:, :4], d[:, -4:]])
# #         v = np.median(dd, axis=1)
# #         v1 = destriper.get_stripe_pattern64(v)

# #         d_destriped = d - v1[:, np.newaxis]

# #         d = d_destriped
# #         h = np.median(np.vstack([d[:4], d[-4:]]))

# #         d_destriped = d - h


# #     im = d_destriped[:, 1024-128:1024+128]

# #     plot(np.median(im, axis=1))



# # def process_band_naive(utdate, recipe_name, band,
# #                        obsids, frametypes, config_name):

# #     from igrins import get_caldb, get_obsset

# #     caldb = get_caldb(config_name, utdate, ensure_dir=True)
# #     obsset = get_obsset(caldb, band, recipe_name, obsids, frametypes)

# #     hdu_list = obsset.get_hdu_list()

# #     # just use the first one
# #     # d = hdu_list[0].data - hdu_list[1].data
# #     d = hdu_list[0].data

# #     im = d[:, 1024-128:1024+128]

# #     plot(np.median(im, axis=1))


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

    fn = "/media/igrins128/jjlee/igrins/20170904/SDCK_20170904_0001.fits"

    # fn = "/media/igrins128/jjlee/annex/igrins/20170414/SDCK_20170414_0014.fits.gz"
    f = pyfits.open(fn)
    r = do_dark(f[0], calib)

    import matplotlib.pyplot as plt
    if 1:
        fig = plt.figure(figsize=(5, 4))
        fig.subplots_adjust(wspace=0.3)

        plot_f(r, fig)

    if 1:
        fig = plt.figure(figsize=(5, 4))
        plot_f2(r, fig)
