#!/bin/zsh
cd "${0:A:h}/scrcpy-macos-aarch64-v5.0.1"
export PATH="$PWD:$PATH"
./scrcpy --keyboard=uhid --mouse=uhid --max-size=1920 --max-fps=60
if [[ $? -ne 0 ]]; then
  echo '请开启手机 USB 调试，并在手机上允许此电脑。小米手机如无法点击，请开启 USB 调试（安全设置）。'
  read '?按回车关闭'
fi
