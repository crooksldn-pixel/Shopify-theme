# Shopify Theme

Theme code for `5wn03t-nm.myshopify.com`, pulled from the live "Horizon" theme (#196747034967).

## Setup

1. Install [Node.js](https://nodejs.org) 18+ and the [Shopify CLI](https://shopify.dev/docs/api/shopify-cli):
   ```
   npm install
   ```
2. Log in to the store (opens a browser for auth):
   ```
   npx shopify auth login --store=5wn03t-nm.myshopify.com
   ```

## Workflow

- **`npm run dev`** — uploads the theme as a temporary development theme and serves it locally with live reload. Preview and editor URLs are printed to the terminal. Changes on disk sync to the store instantly; nothing is published.
- **`npm run check`** — runs [Theme Check](https://shopify.dev/docs/storefronts/themes/tools/theme-check) (linting) against the theme.
- **`npm run pull`** — downloads the latest theme files from the store, in case changes were made in the theme editor.
- **`npm run push`** — pushes local changes to the store. You'll be prompted to pick which theme (never push straight to `[live]` unless you mean to).

## Structure

Standard Shopify Online Store 2.0 theme layout: `layout/`, `templates/`, `sections/`, `blocks/`, `snippets/`, `assets/`, `config/`, `locales/`.
