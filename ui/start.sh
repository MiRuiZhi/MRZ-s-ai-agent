
#!/bin/bash
set -euo pipefail

PNPM_VERSION="10.25.0"

if ! command -v node >/dev/null 2>&1; then
  echo "Node.js is required. Install Node.js 20+ first."
  exit 1
fi

NODE_MAJOR="$(node -p "Number(process.versions.node.split('.')[0])")"
if [ "$NODE_MAJOR" -lt 20 ]; then
  echo "Node.js 20+ is required. Current version: $(node -v)"
  exit 1
fi

if ! command -v corepack >/dev/null 2>&1; then
  echo "Corepack is required. Use the official Node.js 20+ installer or enable your Node package manager tooling."
  exit 1
fi

corepack enable
corepack prepare "pnpm@${PNPM_VERSION}" --activate

pnpm install --frozen-lockfile
pnpm run dev

echo "front end code start success"
