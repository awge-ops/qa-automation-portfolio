#!/usr/bin/env bash
# Gracefully stop test VMs after pipeline completion.
# Called in CI pipeline's after_script to free hypervisor resources.
#
# Requires: PROXMOX_HOST, PROXMOX_TOKEN_ID, PROXMOX_TOKEN_SECRET env vars

set -euo pipefail

PROXMOX_API="https://${PROXMOX_HOST}:8006/api2/json"
AUTH_HEADER="Authorization: PVEAPIToken=${PROXMOX_TOKEN_ID}=${PROXMOX_TOKEN_SECRET}"

VM_IDS=(${VM_IDS:-100 101 102 103 104 105 106 107 108 109 110 111})

stop_vm() {
    local vmid=$1
    echo "[$(date -Iseconds)] Stopping VM ${vmid}"

    curl -sf -X POST \
        -H "$AUTH_HEADER" \
        "${PROXMOX_API}/nodes/pve/qemu/${vmid}/status/stop" \
        || { echo "WARNING: Failed to stop VM ${vmid}"; return 0; }
}

echo "Stopping ${#VM_IDS[@]} VMs"

for vmid in "${VM_IDS[@]}"; do
    stop_vm "$vmid" &
done

wait
echo "All VMs stopped"
