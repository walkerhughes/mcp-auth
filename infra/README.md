# Supabase infrastructure

This Pulumi project provisions a protected Supabase project and generates its database password.
It exports a secret transaction-pooler connection string for the Horizon deployment and a secret
direct connection string for administrative work from an IPv6-capable network.

## Credentials

Set these only in the shell or CI environment that runs Pulumi:

- `SUPABASE_ACCESS_TOKEN`: Supabase personal access token from Account Preferences > Access Tokens.
- `PULUMI_ACCESS_TOKEN`: Pulumi Cloud token, required when using the default Pulumi Cloud backend.
- `SUPABASE_API_ENDPOINT`: optional override for self-hosted Supabase management APIs. Do not set it
  for hosted Supabase.

The MCP runtime does not need any of those credentials.

## Stack configuration

From this directory:

```bash
npx pulumi install
npx pulumi stack init prod
npx pulumi config set supabaseOrganizationId YOUR_ORGANIZATION_SLUG
npx pulumi config set projectName horizon-notes-prod
npx pulumi config set region us-west-1
npx pulumi config set instanceSize micro
npx pulumi preview
npx pulumi up
```

The organization slug is in Supabase Organization Settings. Choose a region near the Horizon
runtime and an instance size appropriate for your expected workload and Supabase plan.

Always review `pulumi preview` before applying. The database project is protected, so an accidental
`pulumi destroy` or removal from the program cannot delete it until protection is explicitly
removed.

## Horizon environment

After `pulumi up`, copy the secret output without printing it into shell history:

```bash
npx pulumi stack output databaseUrl --show-secrets
```

Store that value as the `DATABASE_URL` secret in the Horizon server configuration. Keep
`FASTMCP_STATELESS_HTTP=true` as the only other production-specific variable.

The transaction pooler is appropriate for Horizon's autoscaling runtime. The application disables
prepared statements for compatibility with Supavisor transaction mode and initializes its `notes`
table automatically.
