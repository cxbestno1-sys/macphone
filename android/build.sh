#!/bin/zsh
set -eu
cd "${0:A:h}"
SDK="${ANDROID_SDK_ROOT:-$HOME/Library/Android/sdk}"
TOOLS="$SDK/build-tools/36.1.0"
JAVA="/Applications/Android Studio.app/Contents/jbr/Contents/Home/bin"
PLATFORM="$SDK/platforms/android-36.1/android.jar"
mkdir -p build/classes build/dex ../dist
"$TOOLS/aapt2" compile --dir res -o build/resources.zip
"$TOOLS/aapt2" link -o build/base.apk -I "$PLATFORM" --manifest AndroidManifest.xml build/resources.zip
"$JAVA/javac" -source 8 -target 8 -classpath "$PLATFORM" -d build/classes src/local/macphone/companion/*.java
"$JAVA/jar" cf build/classes.jar -C build/classes .
JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home" "$TOOLS/d8" --lib "$PLATFORM" --min-api 26 --output build/dex build/classes.jar
cp build/base.apk build/unsigned.apk
(cd build/dex && zip -q ../unsigned.apk classes.dex)
"$TOOLS/zipalign" -f 4 build/unsigned.apk build/aligned.apk
if [[ ! -f build/development.keystore ]]; then
 "$JAVA/keytool" -genkeypair -keystore build/development.keystore -storepass android -keypass android -alias macphone -keyalg RSA -keysize 2048 -validity 10000 -dname 'CN=MacPhone Development'
fi
JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home" "$TOOLS/apksigner" sign --ks build/development.keystore --ks-pass pass:android --out ../dist/MacPhone-Companion.apk build/aligned.apk
JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home" "$TOOLS/apksigner" verify ../dist/MacPhone-Companion.apk
