#!/usr/bin/env bash
set -euo pipefail
VAULT_ADDR="${VAULT_ADDR:-http://127.0.0.1:8200}"
NS="capstone-abhinav"
SECRET_NAME="cloudledger-vault-secret"
KEY=$(curl -sf -H "X-Vault-Token: ${VAULT_TOKEN}" "${VAULT_ADDR}/v1/secret/data/capstone-abhinav/cloudledger" | jq -r '.data.data.api_signing_key')
kubectl create secret generic "${SECRET_NAME}" -n "${NS}" \
  --from-literal=API_SIGNING_KEY="${KEY}" \
  --dry-run=client -o yaml | kubectl apply -f -
echo "VAULT_SYNC_OK namespace=${NS} secret=${SECRET_NAME}"
