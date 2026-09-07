# Moving this into its own repository

This directory arrived on a branch of the CROOKS Shopify theme repository because that was the
only push target the session had. It is self-contained and belongs somewhere else.

```bash
# On the Mac, from a checkout of the branch:
cp -R crooks-assistant ~/crooks-assistant
cd ~/crooks-assistant

git init
git add .
git commit -m "CROOKS Assistant: portable build from the Rev 3 plan"

# Optional — a private GitHub repo:
# gh repo create crooks-assistant --private --source=. --push
```

Then check `.gitignore` still covers `credentials.json`, `token.json`, `.env` and `bench/audio/`
before the first push, and delete the `crooks-assistant/` directory from the theme repo branch
so the assistant has exactly one home.

The theme repository itself is unaffected: nothing outside `crooks-assistant/` was touched, and
the branch was never merged to `main`.
