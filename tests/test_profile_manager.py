import json
import os
import tempfile
import unittest

import profile_manager


class ProfileManagerTests(unittest.TestCase):
    def test_saving_encrypts_a_copy_not_the_live_passphrase(self):
        manager = object.__new__(profile_manager.ProfileManager)
        manager.encryption_key = profile_manager.Fernet.generate_key()
        manager.profiles_data = {
            "profiles": {"Default": {"ssh_key_passphrase": "secret"}}
        }

        with tempfile.TemporaryDirectory() as directory:
            manager.profiles_file = os.path.join(directory, "profiles.json")
            manager.save_profiles()
            with open(manager.profiles_file, encoding="utf-8") as profile_file:
                saved = json.load(profile_file)

        self.assertEqual(
            manager.profiles_data["profiles"]["Default"]["ssh_key_passphrase"],
            "secret",
        )
        self.assertNotEqual(
            saved["profiles"]["Default"]["ssh_key_passphrase"], "secret"
        )


if __name__ == "__main__":
    unittest.main()
