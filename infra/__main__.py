from __future__ import annotations

from urllib.parse import quote

import pulumi
import pulumi_random as random
import pulumi_supabase as supabase

from database_url import add_password


class SupabaseDatabase(pulumi.ComponentResource):
    def __init__(
        self,
        name: str,
        *,
        organization_id: str,
        project_name: str,
        region: str,
        instance_size: str,
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        super().__init__("horizon-notes:database:SupabaseDatabase", name, None, opts)

        password = random.RandomPassword(
            f"{name}-password",
            length=32,
            special=False,
            opts=pulumi.ResourceOptions(
                parent=self,
                additional_secret_outputs=["result"],
            ),
        )
        project = supabase.Project(
            name,
            organization_id=organization_id,
            name=project_name,
            database_password=password.result,
            region=region,
            instance_size=instance_size,
            opts=pulumi.ResourceOptions(
                parent=self,
                protect=True,
                additional_secret_outputs=["database_password"],
            ),
        )
        pooler = supabase.get_pooler_output(
            project_ref=project.id,
            opts=pulumi.InvokeOutputOptions(parent=self),
        )

        self.project_ref = project.id
        self.database_url = pulumi.Output.secret(
            pulumi.Output.all(pooler.url, password.result).apply(
                lambda values: add_password(values[0]["transaction"], values[1])
            )
        )
        self.direct_database_url = pulumi.Output.secret(
            pulumi.Output.all(project.id, password.result).apply(
                lambda values: (
                    "postgresql://postgres:"
                    f"{quote(values[1], safe='')}@db.{values[0]}.supabase.co:5432/"
                    "postgres?sslmode=require"
                )
            )
        )
        self.register_outputs(
            {
                "projectRef": self.project_ref,
                "databaseUrl": self.database_url,
                "directDatabaseUrl": self.direct_database_url,
            }
        )


config = pulumi.Config()
database = SupabaseDatabase(
    "notes-prod",
    organization_id=config.require("supabaseOrganizationId"),
    project_name=config.get("projectName") or "horizon-notes-prod",
    region=config.require("region"),
    instance_size=config.get("instanceSize") or "micro",
)

pulumi.export("projectRef", database.project_ref)
pulumi.export("databaseUrl", database.database_url)
pulumi.export("directDatabaseUrl", database.direct_database_url)
