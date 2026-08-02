import io
import os
import tempfile
import unittest
from unittest import mock

import pwnsafe


class _Channel:
    def __init__(self, status):
        self.status = status

    def recv_exit_status(self):
        return self.status


class _Stream(io.BytesIO):
    def __init__(self, data=b"", status=0):
        super().__init__(data)
        self.channel = _Channel(status)


class _SFTP:
    def __init__(self):
        self.puts = []
        self.closed = False

    def put(self, source, destination):
        self.puts.append((source, destination))

    def close(self):
        self.closed = True


class _SSH:
    def __init__(self, responses, sftp=None):
        self.responses = list(responses)
        self.commands = []
        self.sftp = sftp
        self.closed = False

    def exec_command(self, command):
        self.commands.append(command)
        return self.responses.pop(0)

    def open_sftp(self):
        return self.sftp

    def close(self):
        self.closed = True


def _response(stdout=b"", stderr=b"", status=0):
    return None, _Stream(stdout, status), _Stream(stderr)


def _backend(ssh):
    backend = object.__new__(pwnsafe.BackupRestoreApp)
    backend.ssh_connect = lambda *args, **kwargs: ssh
    backend.messages = []
    backend.states = []
    backend.log_message = lambda message, level="INFO", **kwargs: backend.messages.append(
        (level, message)
    )
    backend.update_status = lambda message, *args: None
    backend.show_toast = lambda message, level="info": None
    backend.set_connection_state = lambda state, message=None: backend.states.append(
        (state, message)
    )
    return backend


class BackupRestoreWorkerTests(unittest.TestCase):
    def test_setup_ssh_key_generates_and_installs_authorized_key(self):
        ssh = _SSH([_response(status=0)])
        backend = _backend(None)

        class FakeKey:
            def get_name(self):
                return "ssh-rsa"

            def get_base64(self):
                return "AAAATESTKEY"

            def write_private_key_file(self, path):
                with open(path, "w", encoding="utf-8") as key_file:
                    key_file.write("private")

        class AuthManager:
            def __init__(self, _log_callback):
                pass

            def _load_private_key(self, _path, _passphrase):
                return None

            def connect(self, **_options):
                return ssh

        with tempfile.TemporaryDirectory() as directory, \
                mock.patch("pwnsafe.os.path.expanduser", return_value=directory), \
                mock.patch("pwnsafe.platform.system", return_value="Windows"), \
                mock.patch.object(pwnsafe, "SSHAuthManager", AuthManager), \
                mock.patch.object(pwnsafe.paramiko.RSAKey, "generate", return_value=FakeKey()):
            key_path = backend.setup_ssh_key(
                "10.0.0.2", "pi", "raspberry"
            )

            self.assertTrue(os.path.isfile(key_path))
            self.assertTrue(os.path.isfile(key_path + ".pub"))

        self.assertIn("authorized_keys", ssh.commands[0])
        self.assertIn("grep -qF", ssh.commands[0])
        self.assertTrue(ssh.closed)

    @mock.patch("ctypes.windll.shell32.IsUserAnAdmin", return_value=True)
    @mock.patch("pwnsafe.subprocess.run")
    def test_windows_adapter_configuration_uses_static_ip_without_gateway(
        self, run, _is_admin
    ):
        run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
        backend = _backend(None)
        backend.pwnagotchi_adapter_name = "Ethernet 2"
        backend._windows_adapter_has_expected_ip = lambda: True

        self.assertTrue(backend._configure_windows_adapter_ip())

        command = run.call_args.args[0]
        self.assertEqual(command[0], "netsh.exe")
        self.assertIn("name=Ethernet 2", command)
        self.assertIn("address=10.0.0.1", command)
        self.assertIn("mask=255.255.255.0", command)
        self.assertIn("gateway=none", command)
        self.assertNotIn("shell", run.call_args.kwargs)

    @mock.patch("pwnsafe.socket.create_connection")
    def test_windows_configuration_skips_netsh_when_address_is_already_set(
        self, create_connection
    ):
        create_connection.return_value = mock.Mock()
        backend = _backend(None)
        backend.pwnagotchi_adapter_name = "Ethernet 2"
        backend.pwnagotchi_ip = "10.0.0.2"
        backend.pwnagotchi_detected = False
        backend._windows_adapter_has_expected_ip = lambda: True
        backend._configure_windows_adapter_ip = mock.Mock()
        backend.auto_configure_pwnagotchi = lambda: None

        self.assertTrue(backend.configure_pwnagotchi_windows())
        backend._configure_windows_adapter_ip.assert_not_called()

    def test_ssh_connect_delegates_explicit_credentials(self):
        captured = {}

        class AuthManager:
            def __init__(self, log_callback):
                captured["log_callback"] = log_callback

            def connect(self, **options):
                captured.update(options)
                return "ssh-client"

        backend = object.__new__(pwnsafe.BackupRestoreApp)
        backend.log_message = lambda *args: None
        with mock.patch.object(pwnsafe, "SSHAuthManager", AuthManager):
            result = backend.ssh_connect(
                "10.0.0.2", "pi", "secret", "ssh_key", "id_ed25519", "phrase"
            )

        self.assertEqual(result, "ssh-client")
        self.assertEqual(captured["host"], "10.0.0.2")
        self.assertEqual(captured["username"], "pi")
        self.assertEqual(captured["auth_method"], "ssh_key")
        self.assertEqual(captured["ssh_key_path"], "id_ed25519")

    def test_device_inspection_reports_hostname_and_verified_sharing(self):
        ssh = _SSH(
            [
                _response(b"pwnagotchi-lab\n"),
                _response(b"8.8.8.8 via 10.0.0.1 dev usb0 src 10.0.0.2\n"),
                _response(status=0),
            ]
        )
        backend = _backend(ssh)

        result = backend.inspect_device_connection(
            "10.0.0.2", "pi", "raspberry"
        )

        self.assertEqual(result["hostname"], "pwnagotchi-lab")
        self.assertTrue(result["internet_shared"])
        self.assertTrue(
            any(
                level == "SUCCESS" and "Internet sharing verified" in message
                for level, message in backend.messages
            )
        )
        self.assertTrue(ssh.closed)

    def test_device_inspection_does_not_claim_sharing_on_another_route(self):
        ssh = _SSH(
            [
                _response(b"pwnagotchi\n"),
                _response(b"8.8.8.8 via 192.168.1.1 dev wlan0\n"),
            ]
        )
        backend = _backend(ssh)

        result = backend.inspect_device_connection(
            "10.0.0.2", "pi", "raspberry"
        )

        self.assertFalse(result["internet_shared"])
        self.assertFalse(any("ping -c" in command for command in ssh.commands))
        self.assertTrue(
            any("default route does not use 10.0.0.1" in message for _, message in backend.messages)
        )

    @mock.patch("ctypes.windll.shell32.IsUserAnAdmin", return_value=False)
    @mock.patch("pwnsafe.time.sleep")
    @mock.patch("pwnsafe.os.path.isfile", return_value=True)
    @mock.patch("pwnsafe.subprocess.run")
    def test_internet_sharing_requests_uac_with_bundled_script(
        self, run, _isfile, _sleep, _is_admin
    ):
        run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
        backend = _backend(None)
        backend.is_windows = True
        backend.pwnagotchi_adapter_name = "Ethernet 2"
        backend.pwnagotchi_ip = "10.0.0.2"
        backend.pwnagotchi_user = "pi"
        backend.pwnagotchi_pass = "raspberry"
        backend.get_resource_path = lambda _path: r"C:\Program Files\PwnSafe\scripts\win_connection_share.ps1"
        backend.inspect_device_connection = mock.Mock(
            return_value={"hostname": "pwnagotchi", "internet_shared": True}
        )

        self.assertTrue(
            backend.setup_internet_sharing_windows(
                host="10.0.0.2", username="pi", password="raspberry"
            )
        )

        command = run.call_args.args[0]
        self.assertEqual(command[:4], ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command"])
        self.assertIn("Start-Process", command[-1])
        self.assertIn("Ethernet 2", command[-1])
        self.assertNotIn("shell", run.call_args.kwargs)
        backend.inspect_device_connection.assert_called_once()

    def test_backup_checks_status_before_replacing_destination(self):
        ssh = _SSH([_response(b"archive", b"tar error", 2)])
        backend = _backend(ssh)

        with tempfile.TemporaryDirectory() as directory:
            destination = os.path.join(directory, "backup.tgz")
            backend._backup_worker(destination, "host", "user", "password")
            self.assertFalse(os.path.exists(destination))
            self.assertFalse(os.path.exists(destination + ".part"))

        self.assertTrue(any("exit code 2" in message for _, message in backend.messages))
        self.assertTrue(ssh.closed)

    def test_backup_streams_to_a_partial_file_then_replaces_it(self):
        ssh = _SSH([_response(b"archive", status=0)])
        backend = _backend(ssh)

        with tempfile.TemporaryDirectory() as directory:
            destination = os.path.join(directory, "backup.tgz")
            backend._backup_worker(destination, "host", "user", "password")
            with open(destination, "rb") as backup_file:
                self.assertEqual(backup_file.read(), b"archive")
            self.assertFalse(os.path.exists(destination + ".part"))

        self.assertIn("-czf -", ssh.commands[0])
        self.assertNotIn("| gzip", ssh.commands[0])
        self.assertTrue(ssh.closed)

    def test_restore_streams_with_sftp_and_removes_remote_file(self):
        sftp = _SFTP()
        ssh = _SSH(
            [
                _response(b"/tmp/pwnsafe.123\n"),
                _response(status=0),
            ],
            sftp,
        )
        backend = _backend(ssh)

        with tempfile.NamedTemporaryFile() as source:
            backend._restore_worker(source.name, "host", "user", "password")
            self.assertEqual(sftp.puts, [(os.path.abspath(source.name), "/tmp/pwnsafe.123")])

        self.assertIn("&& rm -f", ssh.commands[1])
        self.assertTrue(sftp.closed)
        self.assertTrue(ssh.closed)

    def test_restore_failure_attempts_remote_cleanup(self):
        sftp = _SFTP()
        ssh = _SSH(
            [
                _response(b"/tmp/pwnsafe.456\n"),
                _response(stderr=b"bad archive", status=2),
                _response(status=0),
            ],
            sftp,
        )
        backend = _backend(ssh)

        with tempfile.NamedTemporaryFile() as source:
            backend._restore_worker(source.name, "host", "user", "password")

        self.assertTrue(ssh.commands[-1].startswith("rm -f "))
        self.assertTrue(any("exit code 2" in message for _, message in backend.messages))


if __name__ == "__main__":
    unittest.main()
