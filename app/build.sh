#!/bin/zsh
set -eu
cd "${0:A:h}/.."
OUT="$PWD/dist/MacPhone.app"
mkdir -p "$OUT/Contents/MacOS" "$OUT/Contents/Resources/runtime"
mkdir -p "$OUT/Contents/Resources/assets"
cp app/assets/icon.png "$OUT/Contents/Resources/assets/icon.png"
cp app/assets/AppIcon.icns "$OUT/Contents/Resources/AppIcon.icns"
cp dist/MacPhone-Companion.apk "$OUT/Contents/Resources/"
cp app/lan_pairing.py app/transfers.py app/device_profiles.py app/task_guard.py app/ai_actions.py app/tasks.py app/backend.py app/index.html app/mcp_server.py "$OUT/Contents/Resources/"
cp scrcpy-macos-aarch64-v5.0.1/{adb,scrcpy,scrcpy-server,LICENSE} "$OUT/Contents/Resources/runtime/"
cp scrcpy/LICENSE "$OUT/Contents/Resources/SCRCPY-LICENSE"
/usr/bin/python3 app/package_runtime.py "$OUT/Contents/Resources/python"
swiftc app/Main.swift -o "$OUT/Contents/MacOS/MacPhone" -framework AppKit -framework WebKit
cat > "$OUT/Contents/Info.plist" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd"><plist version="1.0"><dict><key>CFBundleIconFile</key><string>AppIcon</string><key>LSMinimumSystemVersion</key><string>26.0</string><key>CFBundleExecutable</key><string>MacPhone</string><key>CFBundleIdentifier</key><string>local.macphone.app</string><key>CFBundleName</key><string>MacPhone</string><key>CFBundlePackageType</key><string>APPL</string><key>CFBundleShortVersionString</key><string>0.1.0</string><key>NSAppTransportSecurity</key><dict><key>NSAllowsLocalNetworking</key><true/></dict></dict></plist>
EOF
codesign --force --deep --sign - "$OUT"
