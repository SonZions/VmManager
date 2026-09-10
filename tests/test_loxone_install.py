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
        self.env = patch.dict(os.environ, {"AZURE_VM_PASSWORD": "test-password"}, clear=True)
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
            vm_manager.create_vm()
        run.assert_not_called()
        self.assertIn("Erstellung abgebrochen", self.log.call_args.args[0])

    def test_create_vm_passes_installer_settings_to_extension(self):
        with (
            patch("builtins.open"),
            patch.object(vm_manager, "get_my_ip", return_value="192.0.2.10"),
            patch.object(vm_manager, "run_command") as run,
        ):
            vm_manager.create_vm()
        commands = [call.args[0] for call in run.call_args_list]
        extension = next(cmd for cmd in commands if isinstance(cmd, list))
        self.assertEqual(extension[:4], ["az", "vm", "extension", "set"])
        settings = json.loads(extension[extension.index("--settings") + 1])
        self.assertEqual(settings, vm_manager.get_loxone_install_settings())


if __name__ == "__main__":
    unittest.main()
