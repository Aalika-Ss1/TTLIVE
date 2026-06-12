import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tournament_os.domain.enums import RegistrationStatus
from tournament_os.domain.serializers import (
    RegistrationRecord,
    public_registration_dict,
)


class SerializerTests(unittest.TestCase):
    def test_public_registration_excludes_private_fields(self) -> None:
        public_data = public_registration_dict(
            RegistrationRecord(
                id="reg_1",
                display_name="Player A",
                in_game_name="PlayerA",
                game_uid="123456789",
                status=RegistrationStatus.APPROVED,
                contact_method="discord",
                contact_value="private_handle",
                review_note="private admin note",
            )
        )

        self.assertNotIn("contact_method", public_data)
        self.assertNotIn("contact_value", public_data)
        self.assertNotIn("review_note", public_data)
        self.assertEqual(public_data["display_name"], "Player A")


if __name__ == "__main__":
    unittest.main()
