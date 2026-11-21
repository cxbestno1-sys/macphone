#!/bin/zsh
set -eu
cd "${0:A:h}/.."
STAGE=$(mktemp -d /tmp/macphone-dmg.XXXXXX)
trap 'rm -rf "$STAGE"' EXIT
codesign --verify --deep --strict dist/MacPhone.app
ditto dist/MacPhone.app "$STAGE/MacPhone.app"
ln -s /Applications "$STAGE/Applications"
cp dist/MacPhone-Companion.apk "$STAGE/MacPhone-Companion.apk"
cp 'app/安装说明.txt' "$STAGE/安装说明.txt"
hdiutil create -volname 'MacPhone 安装' -srcfolder "$STAGE" -format UDZO -fs HFS+ -ov 'dist/MacPhone-AppleSilicon-macOS26.dmg'
hdiutil verify 'dist/MacPhone-AppleSilicon-macOS26.dmg'
shasum -a 256 'dist/MacPhone-AppleSilicon-macOS26.dmg' > 'dist/MacPhone-AppleSilicon-macOS26.dmg.sha256'
