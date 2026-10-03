import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "vm_webapp" / "app"))
import vm_manager


class LoxoneInstallTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {"AZURE_VM_PASSWORD": "test-password", "RDP_SOURCE_HOST": "8.8.8.8"}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.log = patch.object(vm_manager, "log").start()
        self.addCleanup(patch.stopall)

    def test_default_and_empty_values_request_latest(self):
        for value in (None, "", "  ", "latest", " LATEST "):
            with self.subTest(value=value):
                if value is None:
                    os.environ.pop("LOXONE_VERSION", None)
                else:
                    os.environ["LOXONE_VERSION"] = value
                settings = vm_manager.get_loxone_install_settings()
                self.assertTrue(settings["commandToExecute"].endswith("-Version latest"))
                self.assertRegex(
                    settings["fileUris"][0],
                    r"^https://raw\.githubusercontent\.com/SonZions/loxone-install/"
                    r"[0-9a-f]{40}/install-loxone\.ps1$",
                )

    def test_explicit_build_remains_supported(self):
        os.environ["LOXONE_VERSION"] = " 17020828 "
        settings = vm_manager.get_loxone_install_settings()
        self.assertTrue(settings["commandToExecute"].endswith("-Version 17020828"))

    def test_invalid_versions_are_rejected(self):
        for value in ("17.2.8.28", "beta", "17020828;whoami", "17'", "１２３４５６７８"):
            with self.subTest(value=value):
                os.environ["LOXONE_VERSION"] = value
                with self.assertRaises(ValueError):
                    vm_manager.get_loxone_install_settings()

    def test_invalid_version_does_not_create_azure_resources(self):
        os.environ["LOXONE_VERSION"] = "invalid"
        with patch("builtins.open"), patch.object(vm_manager, "run_command") as run:
            with self.assertRaises(ValueError):
                vm_manager.create_vm()
        run.assert_not_called()
        self.assertIn("Erstellung abgebrochen", self.log.call_args.args[0])

    def test_create_vm_passes_installer_settings_to_extension(self):
        with (
            patch("builtins.open"),
            patch.object(vm_manager, "run_command") as run,
        ):
            vm_manager.create_vm()
        commands = [call.args[0] for call in run.call_args_list]
        extension = next(cmd for cmd in commands if isinstance(cmd, list) and cmd[:4] == ["az", "vm", "extension", "set"])
        self.assertEqual(extension[:4], ["az", "vm", "extension", "set"])
        settings = json.loads(extension[extension.index("--settings") + 1])
        self.assertEqual(settings, vm_manager.get_loxone_install_settings())

    def test_myfritz_name_resolves_to_public_ipv4(self):
        with patch("vm_manager.socket.getaddrinfo", return_value=[(None, None, None, None, ("37.138.57.49", 0))]):
            self.assertEqual(vm_manager.get_rdp_source_ip("2xfp9mf8ug3fqsvy.myfritz.net"), "37.138.57.49")

    def test_rdp_source_rejects_private_and_malformed_values(self):
        for value in ("192.168.178.1", "127.0.0.1", "bad host", "example.com;whoami"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                vm_manager.get_rdp_source_ip(value)

    def test_azure_command_does_not_log_vm_password(self):
        with patch("vm_manager.subprocess.run") as run:
            run.return_value.stdout = "ok"
            vm_manager.run_command(["az", "vm", "create", "--admin-password", "test-password"])
        logged = "\n".join(call.args[0] for call in self.log.call_args_list)
        self.assertNotIn("test-password", logged)
        self.assertIn("[REDACTED]", logged)


if __name__ == "__main__":
    unittest.main()
