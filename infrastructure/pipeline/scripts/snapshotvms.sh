#!/usr/bin/env bash
# Create named snapshots of test VMs via Proxmox VE API.
# Used to capture a known-good state after manual VM setup.
#
# Requires: PROXMOX_HOST, PROXMOX_TOKEN_ID, PROXMOX_TOKEN_SECRET env vars

set -euo pipefail

PROXMOX_API="https://${PROXMOX_HOST}:8006/api2/json"
AUTH_HEADER="Authorization: PVEAPIToken=${PROXMOX_TOKEN_ID}=${PROXMOX_TOKEN_SECRET}"
SNAPSHOT_NAME="${1:-clean-state}"
DESCRIPTION="${2:-Automated snapshot $(date -Iseconds)}"

VM_IDS=(${VM_IDS:-100 101 102 103 104 105 106 107 108 109 110 111})

snapshot_vm() {
    local vmid=$1
    echo "[$(date -Iseconds)] Creating snapshot '${SNAPSHOT_NAME}' for VM ${vmid}"

    curl -sf -X POST \
        -H "$AUTH_HEADER" \
        -d "snapname=${SNAPSHOT_NAME}" \
        -d "description=${DESCRIPTION}" \
        -d "vmstate=1" \
        "${PROXMOX_API}/nodes/pve/qemu/${vmid}/snapshot" \
        || { echo "ERROR: Failed to snapshot VM ${vmid}"; return 1; }
}

echo "Creating snapshot '${SNAPSHOT_NAME}' on ${#VM_IDS[@]} VMs"

for vmid in "${VM_IDS[@]}"; do
    snapshot_vm "$vmid" &
done

wait
echo "All snapshots created"
