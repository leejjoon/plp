import json
from pandas.io.json import dumps as json_dumps
import astropy.io.fits as pyfits

from igr_ql.bucket import get_bucket_n_object_name

# from ql_dark import do_dark

# from ql_stellar import QlStellar

import quicklook_all

quicklook = quicklook_all.QuickLook(slit_length_arcsec=10.)


def json_dump(obj, f):
    f.write(json_dumps(obj))


class QuickLookWorker():
    def on_init(self):
        pass

    def do_task(self, taskname, msg):
        pass


# class LocalStorage(object):
#     def __init__(self, root):
#         self.root = root

#     def exists(self, bucket_name, object_name):
#         p = self.get_path(bucket_name, object_name)
#         return self.os.path.exists(p)

#     def ensure_dir(self, bucket_name, object_name):
#         p = self.get_path(bucket_name, object_name)
#         dir_name = os.path.dirname(p)
#         if not os.path.exists(dir_name):
#             os.makedirs(dir_name)

#     def open(self, bucket_name, object_name, mode="rb"):
#         "return File-like object"
#         p = self.get_path(bucket_name, object_name)
#         return open(p, mode)

#     def get_path(self, bucket_name, object_name):
#         return os.path.join(self.root, bucket_name, object_name)


# class SshStorage(object):
#     def __init__(self, host, root):
#         self.root = root

#     def exists(self, bucket_name, object_name):
#         p = self.get_path(bucket_name, object_name)
#         return self.os.path.exists(p)

#     def ensure_dir(self, bucket_name, object_name):
#         p = self.get_path(bucket_name, object_name)
#         dir_name = os.path.dirname(p)
#         if not os.path.exists(dir_name):
#             os.makedirs(dir_name)

#     def open(self, bucket_name, object_name, mode="rb"):
#         "return File-like object"
#         p = self.get_path(bucket_name, object_name)
#         return open(p, mode)

#     def get_path(self, bucket_name, object_name):
#         return os.path.join(self.root, bucket_name, object_name)



class QuickLook():
    def __init__(self, storage, output_stroage, use_gzip=False):
        self.storage = storage
        self.output_storage = output_stroage
        self.use_gzip = use_gzip

    def get_file(self, obsdate, obsid, band):
        if self.use_gzip:
            ext = "fits.gz"
        else:
            ext = "fits"

        bucket_name, object_name = get_bucket_n_object_name(obsdate, obsid,
                                                            band, ext=ext)

        f = self.storage.open(bucket_name, object_name,
                              use_gzip=self.use_gzip)
        return f

    def _get_hdu_info(self, hdu):
        h = hdu.header
        k_list = ["EXPTIME", "NSAMP", "OBJECT",
                  "AMSTART", "AMEND", "PASTART", "PAEND",
                  "OBJTYPE", "FRMTYPE"]

        jo = dict((k.lower(), h.get(k, None)) for k in k_list)

        return jo

    def store_result(self, hdu,
                     obsdate, obsid, band, objtype, frametype,
                     jo, binaries):

        bucket_name, object_name = get_bucket_n_object_name(obsdate, obsid,
                                                            band)
        s = self.output_storage
        s.ensure_dir(bucket_name, object_name)

        jo["obsdate"] = obsdate
        jo["obsid"] = obsid
        jo["band"] = band

        jo["binaries"] = {}
        for k, v in binaries.items():
            fn = object_name + "." + k
            s.open(bucket_name, fn, "wb").write(v)
            jo["binaries"][k] = (bucket_name, fn)

        json_dump(jo,
                  s.open(bucket_name, object_name + ".json", "w"))

        r = self._get_hdu_info(hdu)
        r.update(basename=object_name,
                 obsid=obsid,
                 objtype=objtype,
        )

        if s.exists(bucket_name, "index.json"):
            index_json = json.load(s.open(bucket_name,
                                          "index.json", "r"))
        else:
            index_json = dict(ql_list=[])

        ql_dict = dict((j["basename"], j) for j in index_json["ql_list"])

        ql_dict[object_name] = r
        ql_list = [ql_dict[k] for k in sorted(ql_dict.keys())]
        index_json["ql_list"] = ql_list
        # index_json["ql_list"].append(r)

        json_dump(index_json,
                  s.open(bucket_name, "index.json", "w"))

    def process(self, obsdate, obsid, band, objtype, frametype,
                **aux):

        f = self.get_file(obsdate, obsid, band)

        hdu_list = pyfits.open(f)
        hdu = hdu_list[0]

        objtype = objtype.lower()

        if objtype == "dark":
            jo, binaries = quicklook.do_dark(hdu, obsdate, obsid, band,
                                             objtype, frametype, **aux)
        elif objtype == "flat":
            jo, binaries = quicklook.do_flat(hdu, obsdate, obsid, band,
                                             objtype, frametype, **aux)
        elif objtype in ["std", "tar"]:
            jo, binaries = quicklook.do_stellar(hdu, obsdate, obsid, band,
                                                objtype, frametype, **aux)
        else:
            raise ValueError("quicklook procedure not known: {}, {}"
                             .format(objtype, frametype))

        self.store_result(hdu,
                          obsdate, obsid, band, objtype, frametype,
                          jo, binaries)


def get_autosync_storage():
    from my_ssh_client import get_sshclient
    from ScpStorage import (LocalStorage,
                            SshStorage,
                            LocalStorageSyncFromRemote)

    local_storage = LocalStorage("/media/igrins128/jjlee/igrins")

    sshclient = get_sshclient()
    ssh_storage = SshStorage(sshclient, "/IGRINS/obsdata")

    auto_sync_storage = LocalStorageSyncFromRemote(ssh_storage,
                                                   local_storage)

    return auto_sync_storage

    # f = auto_sync_storage.open("20170903", "SDCK_20170903_0054.fits")


if __name__ == "__main__":
    from ScpStorage import LocalStorage

    # SDCK_20170830_0001.fits

    obsdate, band = "20170414", "K"
    use_gzip = True
    ff = "/media/igrins128/jjlee/annex/igrins"
    storage = LocalStorage(ff)

    # obsdate, band = "20170904", "K"
    # storage = LocalStorage("/media/igrins128/jjlee/igrins")

    # storage = get_autosync_storage()

    output_storage = LocalStorage("./qlook/public/html")
    # output_storage = LocalStorage("./html")

    ql = QuickLook(storage, output_storage, use_gzip=use_gzip)

    if 1:
        for obsid in range(1, 11):
            objtype, frametype = "DARK", "-"
            ql.process(obsdate, obsid, band, objtype, frametype)

    if 1:
        for obsid in range(11, 21):
            objtype, frametype = "FLAT", "OFF"
            ql.process(obsdate, obsid, band, objtype, frametype)

    if 1:
        for obsid in range(21, 31):
            objtype, frametype = "FLAT", "ON"
            ql.process(obsdate, obsid, band, objtype, frametype)

    if 1:
        for obsid in range(31, 41)[:]:
            objtype, frametype = "TAR", "-"
            ql.process(obsdate, obsid, band, objtype, frametype)
