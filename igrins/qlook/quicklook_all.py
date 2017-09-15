# import numpy as np
# import scipy.ndimage as ni

from matplotlib.figure import Figure
# from mpl_toolkits.axes_grid1 import Grid

from igr_ql.qa_helper import fig_to_png_string
from load_calib import get_calibs

import quicklook_stellar as ql_stellar
import ql_flat
import ql_dark


class Calib(object):
    def __init__(self, band, slit_length_arcsec):

        self.band = band
        self.slit_length_arcsec = slit_length_arcsec

        ap, order_map, slitposmap = get_calibs(band)
        self.ap = ap
        self.order_map = order_map[0].data
        self.slitposmap = slitposmap[0]


class QuickLook(object):
    def __init__(self, slit_length_arcsec):

        self.calib = {}
        for band in "HK":
            self.calib[band] = Calib(band, slit_length_arcsec)

    def do_stellar(self, hdu, obsdate, obsid, band, objtype, frametype,
                   **aux):

        binaries = dict()

        calib = self.calib[band]

        r = ql_stellar.do_ql_stellar(hdu, calib)

        fig1 = Figure(figsize=(5, 4))

        ql_stellar.do_figure_stacked_profile(r, calib, fig=fig1)

        s = fig_to_png_string(fig1)
        binaries["stacked_profile.png"] = s

        fig2 = Figure(figsize=(5, 4))

        ql_stellar.do_figure_profile_per_order(r, calib, fig=fig2)

        s = fig_to_png_string(fig2)
        binaries["slit_profile_per_order.png"] = s

        fig3 = Figure(figsize=(5, 4))

        ql_stellar.do_figure_stat_per_order(r, calib, fig=fig3)

        fig3.tight_layout()
        s = fig_to_png_string(fig3)
        binaries["slit_stat_per_order.png"] = s

        jo = dict(per_order=r["per_order"],
                  stacked=r["stacked"])

        return jo, binaries

    def do_flat(self, hdu, obsdate, obsid, band, objtype, frametype,
                **aux):

        binaries = dict()

        calib = self.calib[band]

        r = ql_flat.do_flat(hdu, calib, frametype)

        fig1 = Figure(figsize=(5, 4))
        # fig1.subplots_adjust(wspace=0.3)

        ql_flat.plot_f(r, fig=fig1)

        s = fig_to_png_string(fig1)
        binaries["center_cut_profile.png"] = s

        fig2 = Figure(figsize=(5, 4))

        ql_flat.plot_f2(r, fig=fig2)

        s = fig_to_png_string(fig2)
        binaries["center_cut_profile_by_order.png"] = s

        # jo = dict(per_order=r["per_order"],
        #           stacked=r["stacked"])

        return r, binaries

    def do_dark(self, hdu, obsdate, obsid, band, objtype, frametype,
                **aux):

        binaries = dict()

        calib = self.calib[band]

        r = ql_dark.do_dark(hdu, calib)

        fig1 = Figure(figsize=(5, 4))
        # fig1.subplots_adjust(wspace=0.3)

        ql_dark.plot_f(r, fig=fig1)

        s = fig_to_png_string(fig1)
        binaries["dark_hist_1comp.png"] = s

        fig2 = Figure(figsize=(5, 4))

        if "_raw_data_fig2" in r:
            ql_dark.plot_f2(r, fig=fig2)

            s = fig_to_png_string(fig2)
            binaries["dark_hist_2comp.png"] = s

        # jo = dict(per_order=r["per_order"],
        #           stacked=r["stacked"])

        return r, binaries
