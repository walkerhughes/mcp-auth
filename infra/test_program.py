import runpy
import unittest
from pathlib import Path

import pulumi


class InfrastructureMocks(pulumi.runtime.Mocks):
    def new_resource(self, args: pulumi.runtime.MockResourceArgs):
        outputs = dict(args.inputs)
        resource_id = f"{args.name}-id"
        if args.typ == "random:index/randomPassword:RandomPassword":
            outputs["result"] = "generatedpassword"
        if args.typ == "supabase:index/project:Project":
            resource_id = "project-ref"
        return [resource_id, outputs]

    def call(self, args: pulumi.runtime.MockCallArgs):
        if args.token == "supabase:index/getPooler:getPooler":
            return {
                "projectRef": args.args["projectRef"],
                "url": {
                    "transaction": (
                        "postgresql://postgres.project-ref:[YOUR-PASSWORD]@"
                        "aws-0-us-west-1.pooler.supabase.com:6543/postgres"
                    )
                },
            }
        return args.args


class PulumiProgramTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        pulumi.runtime.set_mocks(
            InfrastructureMocks(),
            project="horizon-notes-infra",
            stack="test",
            preview=False,
        )
        pulumi.runtime.set_all_config(
            {
                "horizon-notes-infra:supabaseOrganizationId": "test-org",
                "horizon-notes-infra:region": "us-west-1",
            }
        )
        self.program = runpy.run_path(str(Path(__file__).with_name("__main__.py")))

    @pulumi.runtime.test
    def test_database_url_uses_the_transaction_pooler(self):
        database = self.program["database"]

        def check(database_url: str) -> None:
            self.assertIn("pooler.supabase.com:6543", database_url)
            self.assertIn("generatedpassword", database_url)
            self.assertIn("sslmode=require", database_url)

        return database.database_url.apply(check)


if __name__ == "__main__":
    unittest.main()
