import unittest

from database_url import add_password


class DatabaseUrlTests(unittest.TestCase):
    def test_adds_encoded_password_and_requires_tls(self) -> None:
        template = (
            "postgresql://postgres.project:[YOUR-PASSWORD]@"
            "aws-0-us-west-1.pooler.supabase.com:6543/postgres"
        )

        result = add_password(template, "safe/password")

        self.assertEqual(
            result,
            "postgresql://postgres.project:safe%2Fpassword@"
            "aws-0-us-west-1.pooler.supabase.com:6543/postgres?sslmode=require",
        )

    def test_rejects_an_invalid_template(self) -> None:
        with self.assertRaises(ValueError):
            add_password("not-a-postgres-url", "password")


if __name__ == "__main__":
    unittest.main()
