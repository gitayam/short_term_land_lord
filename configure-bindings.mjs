#!/usr/bin/env node
/**
 * Configure Cloudflare Pages project bindings
 * Uses CF_API_TOKEN environment variable
 */

const ACCOUNT_ID = "04eac09ae835290383903273f68c79b0";
const PROJECT_NAME = "short-term-landlord";

const config = {
  deployment_configs: {
    production: {
      d1_databases: {
        DB: {
          id: "fb1bde66-9837-4358-8c71-19be2a88cfee"
        }
      },
      kv_namespaces: {
        KV: {
          namespace_id: "48afc9fe53a3425b8757e9dc526c359e"
        }
      },
      r2_buckets: {
        BUCKET: {
          name: "short-term-landlord-files"
        }
      },
      env_vars: {
        ENVIRONMENT: {
          value: "production"
        },
        FRONTEND_URL: {
          value: "https://short-term-landlord.pages.dev"
        },
        EMAIL_PROVIDER: {
          value: "ses"
        },
        EMAIL_FROM: {
          value: "no-reply@irregularchat.com"
        }
      }
    }
  }
};

const apiToken = process.env.CF_API_TOKEN;
if (!apiToken) {
  console.error("Error: CF_API_TOKEN environment variable not set");
  console.error("\nTo create an API token:");
  console.error("1. Go to https://dash.cloudflare.com/profile/api-tokens");
  console.error("2. Create a token with 'Edit Cloudflare Pages' permissions");
  console.error("3. Export it: export CF_API_TOKEN='your-token-here'");
  console.error("4. Run this script again");
  process.exit(1);
}

const url = `https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/pages/projects/${PROJECT_NAME}`;

console.log("Configuring bindings for Pages project...");
console.log("Project:", PROJECT_NAME);

try {
  const response = await fetch(url, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${apiToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(config)
  });

  const data = await response.json();

  if (!response.ok) {
    console.error("Error configuring bindings:");
    console.error(JSON.stringify(data, null, 2));
    process.exit(1);
  }

  console.log("\n✅ Bindings configured successfully!");
  console.log("\nConfigured:");
  console.log("  - D1 Database: DB");
  console.log("  - KV Namespace: KV");
  console.log("  - R2 Bucket: BUCKET");
  console.log("  - Environment variables: ENVIRONMENT, FRONTEND_URL, EMAIL_PROVIDER, EMAIL_FROM");
  console.log("\nYou may need to trigger a new deployment for changes to take effect.");
} catch (error) {
  console.error("Error:", error.message);
  process.exit(1);
}
