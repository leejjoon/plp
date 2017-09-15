import os
import gzip
# import scpclient as scp

from scp import SCPClient


# with scp.closing(scp.Read(ssh_client.get_transport(),
#                           '.')) as s:
#     s.receive("fn.list")


class LocalStorage(object):
    def __init__(self, root):
        self.root = root

    def exists(self, bucket_name, object_name):
        p = self.get_path(bucket_name, object_name)
        return os.path.exists(p)

    def ensure_dir(self, bucket_name, object_name):
        p = self.get_path(bucket_name, object_name)
        dir_name = os.path.dirname(p)
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

    def open(self, bucket_name, object_name, mode="rb", use_gzip=False):
        "return File-like object"
        p = self.get_path(bucket_name, object_name)
        if use_gzip:
            return gzip.open(p, mode)
        else:
            return open(p, mode)

    def get_path(self, bucket_name, object_name):
        return os.path.join(self.root, bucket_name, object_name)


class SshStorage(object):
    def __init__(self, ssh_client, root):
        self.ssh_client = ssh_client
        self.root = root

        self.scp = SCPClient(self.ssh_client.get_transport())

    def get_path(self, bucket_name, object_name):
        return os.path.join(self.root, bucket_name, object_name)

    def copy(self, bucket_name, object_name, local_path):
        p = self.get_path(bucket_name, object_name)
        self.scp.get(remote_path=p, local_path=local_path)


class LocalStorageSyncFromRemote():
    def __init__(self, remote_storage, local_storage):
        self.remote = remote_storage
        self.local = local_storage

    def open(self, bucket_name, object_name):
        """
        If file is locally not found, copy from the remote location.
        """
        if not self.local.exists(bucket_name, object_name):
            self.local.ensure_dir(bucket_name, object_name)
            p = self.local.get_path(bucket_name, object_name)
            # save remote file to local path (p)
            self.remote.copy(bucket_name, object_name, p)
            print("file copied")

        return self.local.open(bucket_name, object_name)


if __name__ == "__main__":
    # SDCK_20170830_0001.fits
    obsdate, band = "20170830", "K"

    local_storage = LocalStorage("/media/igrins128/jjlee/igrins")

    sshclient = get_sshclient()
    ssh_storage = SshStorage(sshclient, "/IGRINS/obsdata")

    auto_sync_storage = LocalStorageSyncFromRemote(ssh_storage,
                                                   local_storage)

    f = auto_sync_storage.open("20170903", "SDCK_20170903_0054.fits")
    # output_storage = LocalStorage("./html")
