import paramiko


def get_sshclient():
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.WarningPolicy())

    ssh_client.connect("localhost", username="igrins", port=5022)

    return ssh_client
