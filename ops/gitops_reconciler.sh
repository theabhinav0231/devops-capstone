#!/usr/bin/env bash
set -euo pipefail
NS="capstone-abhinav"
DEPLOY="cloudledger-stable"
DESIRED=$(grep -E '^  replicas:' k8s/deployment-stable.yaml | awk '{print $2}')
LIVE=$(kubectl get deploy "${DEPLOY}" -n "${NS}" -o jsonpath='{.spec.replicas}')
echo "[gitops] Git HEAD desired_replicas=${DESIRED} | live_replicas=${LIVE}"
if [ "${DESIRED}" != "${LIVE}" ]; then
  echo "[gitops] DRIFT_DETECTED live=${LIVE} != git=${DESIRED} -> reconciling from Git SSOT"
  kubectl apply -f k8s/deployment-stable.yaml
  kubectl rollout status deploy/"${DEPLOY}" -n "${NS}" --timeout=60s
  echo "[gitops] DRIFT_SELF_HEALED replicas=${DESIRED}"
else
  echo "[gitops] IN_SYNC replicas=${LIVE}"
fi
