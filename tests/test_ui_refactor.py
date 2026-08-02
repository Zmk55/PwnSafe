import unittest
from types import SimpleNamespace
from unittest import mock

from ui_refactor import ConnState, PwnSafeCompactUI


class SSHLauncherTests(unittest.TestCase):
    def test_terminal_forwards_control_and_arrow_keys(self):
        channel = mock.Mock(closed=False)
        ui = SimpleNamespace(
            _terminal_channel=channel,
            show_toast=mock.Mock(),
            _append_terminal=mock.Mock(),
        )

        control_c = SimpleNamespace(keysym="c", state=0x4, char="\x03")
        arrow_up = SimpleNamespace(keysym="Up", state=0, char="")

        PwnSafeCompactUI._send_terminal_key(ui, control_c)
        PwnSafeCompactUI._send_terminal_key(ui, arrow_up)

        self.assertEqual(
            channel.send.call_args_list,
            [mock.call("\x03"), mock.call("\x1b[A")],
        )

    @mock.patch("ui_refactor.platform.system", return_value="Windows")
    def test_internet_sharing_is_available_without_ssh_credentials(self, _system):
        button = mock.Mock()
        ui = SimpleNamespace(
            backup_button=mock.Mock(),
            restore_button=mock.Mock(),
            ssh_button=mock.Mock(),
            internet_sharing_button=button,
            _conn_state=ConnState.IDLE,
            _sharing_busy=False,
            _terminal_connecting=False,
            get_connection_options=lambda: {
                "host": "",
                "username": "",
                "password": "",
                "auth_method": "password",
            },
            _credentials_ready=lambda _options: False,
            log_service=mock.Mock(),
        )

        PwnSafeCompactUI._update_action_buttons(ui)

        button.configure.assert_called_once_with(state="normal")

    def test_terminal_worker_opens_paramiko_shell(self):
        options = {
            "host": "10.0.0.2",
            "username": "pi",
            "password": "raspberry",
            "auth_method": "password",
            "ssh_key_path": "",
            "ssh_key_passphrase": "",
            "use_ssh_agent": False,
        }
        transport = mock.Mock()
        channel = mock.Mock()
        client = mock.Mock()
        client.get_transport.return_value = transport
        client.invoke_shell.return_value = channel
        app = mock.Mock()
        app.ssh_connect.return_value = client
        connected = mock.Mock()
        ui = SimpleNamespace(
            app=app,
            after=lambda _delay, callback: callback(),
            _terminal_connected=connected,
            _terminal_connection_failed=mock.Mock(),
            _request_key_setup_password=mock.Mock(),
        )

        PwnSafeCompactUI._terminal_connect_worker(ui, options)

        app.ssh_connect.assert_called_once_with(**options)
        client.invoke_shell.assert_called_once_with(term="xterm", width=120, height=36)
        connected.assert_called_once_with(client, channel, options, "")

    def test_failed_key_auth_runs_password_wizard_then_connects(self):
        options = {
            "host": "10.0.0.2",
            "username": "pi",
            "password": "",
            "auth_method": "ssh_key",
            "ssh_key_path": "missing-key",
            "ssh_key_passphrase": "",
            "use_ssh_agent": False,
        }
        client = mock.Mock()
        client.get_transport.return_value = mock.Mock()
        client.invoke_shell.return_value = mock.Mock()
        app = mock.Mock()
        app.ssh_connect.side_effect = [None, client]
        app.setup_ssh_key.return_value = r"C:\Users\Tim\.ssh\pwnsafe_id_rsa"
        connected = mock.Mock()
        ui = SimpleNamespace(
            app=app,
            after=lambda _delay, callback: callback(),
            _terminal_connected=connected,
            _terminal_connection_failed=mock.Mock(),
            _request_key_setup_password=mock.Mock(return_value="raspberry"),
        )

        with mock.patch("ui_refactor.os.path.isfile", return_value=True):
            PwnSafeCompactUI._terminal_connect_worker(ui, options)

        app.setup_ssh_key.assert_called_once_with(
            "10.0.0.2", "pi", "raspberry", "missing-key"
        )
        reconnect_options = app.ssh_connect.call_args.kwargs
        self.assertEqual(
            reconnect_options["ssh_key_path"],
            r"C:\Users\Tim\.ssh\pwnsafe_id_rsa",
        )
        self.assertEqual(reconnect_options["auth_method"], "ssh_key")
        self.assertEqual(app.ssh_connect.call_count, 2)
        connected.assert_called_once()


if __name__ == "__main__":
    unittest.main()
