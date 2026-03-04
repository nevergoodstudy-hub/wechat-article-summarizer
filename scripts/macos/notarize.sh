#!/usr/bin/env bash
# macOS code-sign + notarization helper.
#
# Required environment variables:
#   CODESIGN_IDENTITY    — Developer ID certificate identity
#   APPLE_ID             — Apple ID email
#   APPLE_TEAM_ID        — Apple Developer Team ID
#   APPLE_APP_PASSWORD   — App-specific password for notarytool
#
# Usage:
#   export CODESIGN_IDENTITY="Developer ID Application: My Name (TEAM123)"
#   export APPLE_ID="me@example.com"
#   export APPLE_TEAM_ID="TEAM123"
#   export APPLE_APP_PASSWORD="xxxx-xxxx-xxxx-xxxx"
#   bash scripts/macos/notarize.sh dist/WeChat\ Article\ Summarizer.app

set -euo pipefail

APP_PATH="${1:?Usage: $0 <path-to-app>}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENTITLEMENTS="${SCRIPT_DIR}/entitlements.plist"

echo "🔏 Signing ${APP_PATH} ..."
codesign --force --deep --options runtime \
    --timestamp \
    --entitlements "${ENTITLEMENTS}" \
    --sign "${CODESIGN_IDENTITY}" \
    "${APP_PATH}"

echo "✅ Verifying signature ..."
codesign --verify --deep --strict "${APP_PATH}"

echo "📦 Creating zip for notarization ..."
ZIP_PATH="${APP_PATH%.app}.zip"
ditto -c -k --sequesterRsrc --keepParent "${APP_PATH}" "${ZIP_PATH}"

echo "📤 Submitting to Apple notary service ..."
xcrun notarytool submit "${ZIP_PATH}" \
    --apple-id "${APPLE_ID}" \
    --team-id "${APPLE_TEAM_ID}" \
    --password "${APPLE_APP_PASSWORD}" \
    --wait

echo "📎 Stapling notarization ticket ..."
xcrun stapler staple "${APP_PATH}"

rm -f "${ZIP_PATH}"
echo "🎉 Notarization complete!"
