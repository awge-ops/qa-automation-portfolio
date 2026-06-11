#!/usr/bin/env bash
# Reset test VMs to clean snapshot via Proxmox VE API.
# Called by CI pipeline before each test run to ensure deterministic state.
#
# Requires: PROXMOX_HOST, PROXMOX_TOKEN_ID, PROXMOX_TOKEN_SECRET env vars

set -euo pipefail

PROXMOX_API="https://${PROXMOX_HOST}:8006/api2/json"
AUTH_HEADER="Authorization: PVEAPIToken=${PROXMOX_TOKEN_ID}=${PROXMOX_TOKEN_SECRET}"
SNAPSHOT_NAME="${SNAPSHOT_NAME:-clean-state}"

VM_IDS=(${VM_IDS:-100 101 102 103 104 105 106 107 108 109 110 111})

rollback_vm() {
    local vmid=$1
    echo "[$(date -Iseconds)] Rolling back VM ${vmid} to snapshot '${SNAPSHOT_NAME}'"

    curl -sf -X POST \
        -H "$AUTH_HEADER" \
        "${PROXMOX_API}/nodes/pve/qemu/${vmid}/snapshot/${SNAPSHOT_NAME}/rollback" \
        || { echo "ERROR: Failed to rollback VM ${vmid}"; return 1; }

    echo "[$(date -Iseconds)] Starting VM ${vmid}"
    curl -sf -X POST \
        -H "$AUTH_HEADER" \
        "${PROXMOX_API}/nodes/pve/qemu/${vmid}/status/start" \
        || { echo "ERROR: Failed to start VM ${vmid}"; return 1; }
}

echo "Resetting ${#VM_IDS[@]} VMs to snapshot '${SNAPSHOT_NAME}'"

for vmid in "${VM_IDS[@]}"; do
    rollback_vm "$vmid" &
done

wait
echo "All VMs reset successfully"
