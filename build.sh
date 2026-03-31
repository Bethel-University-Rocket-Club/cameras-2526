#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CUSTOMPIOS_DIR="${SCRIPT_DIR}/CustomPiOS"
SRC_DIR="${SCRIPT_DIR}/src"
IMAGE_DIR="${SRC_DIR}/image"
MODULE_DIR="${SRC_DIR}/modules/cameras"

# ── 1. Ensure submodule is initialized ───────────────────────────────────────
git -C "${SCRIPT_DIR}" submodule update --init --recursive

# ── 2. Download base image ────────────────────────────────────────────────────
BASE_URL="$(cat "${SCRIPT_DIR}/image.url")"
IMAGE_FILE="${IMAGE_DIR}/$(basename "${BASE_URL}")"

mkdir -p "${IMAGE_DIR}"

if [[ ! -f "${IMAGE_FILE}" ]]; then
    echo "Downloading base image from ${BASE_URL}..."
    wget -O "${IMAGE_FILE}" "${BASE_URL}"
else
    echo "Base image already present: ${IMAGE_FILE}"
fi

# ── 3. Create CustomPiOS src layout ──────────────────────────────────────────
MODULE_DIR="${SCRIPT_DIR}/modules/cameras"
mkdir -p "${MODULE_DIR}/filesystem"
mkdir -p "${SCRIPT_DIR}/workspace"

# ── 4. Write src/config ───────────────────────────────────────────────────────
cat > "${SCRIPT_DIR}/config" <<EOF
export DIST_NAME="cameras"
export MODULES="base(cameras)"
export BASE_ZIP_IMG="${IMAGE_FILE}"
export BASE_IMAGE_ENLARGEROOT=800
export BASE_IMAGE_RESIZEROOT=200
export BASE_USER=burockets
export BASE_USER_PASSWORD=burockets1
EOF

# ── 5. Sync root filesystem overlay ──────────────────────────────────────────
rsync -a --delete "${SCRIPT_DIR}/root/" "${MODULE_DIR}/filesystem/root/"

# ── 6. Generate start_chroot_script ──────────────────────────────────────────
cat > "${MODULE_DIR}/start_chroot_script" <<'CHROOT_HEADER'
#!/usr/bin/env bash
set -euo pipefail
source /common.sh
echo "### cameras module starting ###"

### filesystem overlay ###
unpack /filesystem/root / root

CHROOT_HEADER

for conf in apt tailscale systemctl permissions; do
    echo "### ${conf} ###" >> "${MODULE_DIR}/start_chroot_script"
    cat "${SCRIPT_DIR}/conf/${conf}.conf" >> "${MODULE_DIR}/start_chroot_script"
    echo >> "${MODULE_DIR}/start_chroot_script"
done

cat >> "${MODULE_DIR}/start_chroot_script" <<'CHROOT_FOOTER'

echo "### cameras module done ###"
CHROOT_FOOTER

chmod +x "${MODULE_DIR}/start_chroot_script"

# ── 7. Symlink all CustomPiOS src internals into src/ ────────────────────────
mkdir -p "${SRC_DIR}"
for item in "${CUSTOMPIOS_DIR}/src/"*; do
    name="$(basename "${item}")"
    # Don't clobber our own modules or config
    if [[ "${name}" == "modules" || "${name}" == "config" ]]; then
        continue
    fi
    ln -sf "${item}" "${SRC_DIR}/${name}"
done
# Symlink just the base module, preserving our own modules dir
ln -sf "${CUSTOMPIOS_DIR}/src/modules/base" "${SRC_DIR}/modules/base" 2>/dev/null || true

# ── 8. Build ──────────────────────────────────────────────────────────────────
echo "Starting CustomPiOS build..."
sudo modprobe loop
cd "${SRC_DIR}"
sudo -E env "PATH=$PATH" "DIST_PATH=${SCRIPT_DIR}" "CUSTOM_PI_OS_PATH=${CUSTOMPIOS_DIR}/src" bash -x ./build_custom_os
