#!/bin/bash
# Full instrument pass for one site. Usage: ./run-site.sh <tag> <homeUrl> [pdpUrl] [collectionUrl]
cd /home/user/Shopify-theme
TAG=$1; shift
node audit/compare/c-recon.mjs "$TAG" "$@"
node audit/compare/c-perf.mjs "$TAG"
node audit/compare/c-a11y.mjs "$TAG"
node audit/compare/c-commerce.mjs "$TAG"
node audit/compare/c-journeys.mjs "$TAG"
echo "=== $TAG complete ==="
