# MacPhone

MacPhone 是一个面向 Apple 芯片 Mac 的安卓手机控制工具。通过 USB 或 Wi-Fi 连接手机，在 Mac 上查看画面、操作应用、管理文件，还可以录制常用流程，或通过视觉模型和 MCP 控制已授权的设备。

## 功能

- **手机控制**：选择并命名多台手机，在截图预览上点击、拖动、输入文字，或返回手机主页。
- **连接向导**：按首次连接、Wi-Fi 配对、安装 App 和安装辅助分组，引导完成 ADB 调试与助手授权。
- **文件管理**：浏览手机共享存储、发送文件、拷贝到 Mac，以及安装 APK。
- **个人任务**：按手机保存操作步骤，设置执行间隔、定时和可选的截图判断。
- **AI 助手**：接入支持图像的 Chat Completions 兼容模型，选择自动执行或逐步确认，并查看任务结果。
- **MCP 接入**：在设置中复制 stdio 配置，供 Hermes 等同一台 Mac 上的客户端调用。

## 使用

Mac 端面向 Apple 芯片和 macOS 26 或更高版本。安卓助手需要 Android 8 或更高版本。首次使用请打开 MacPhone 的“向导”，用数据线连接手机，在手机上开启 USB 调试并确认授权。随后可按向导设置无线调试和无障碍助手。扫码用于助手身份配对，ADB 和无障碍权限仍需在手机上授权。

预览使用定时截图。有安全锁屏时需要用户解锁。配置视觉模型后，执行 AI 任务时，截图和任务内容会发送到你配置的服务。API Key 保存在 macOS 钥匙串，个人任务保存在本机。

## 从源码构建

1. 安装 Xcode Command Line Tools、Homebrew 的 `python@3.13`、Android Studio，以及 Android SDK Platform 36.1 和 Build Tools 36.1.0。若 SDK 安装在非默认位置，设置 `ANDROID_SDK_ROOT`。
2. 将 [scrcpy 5.0.1 源码](https://github.com/Genymobile/scrcpy/tree/v5.0.1) 放在项目根目录下的 `scrcpy/`，将同版本 [Apple Silicon 发布包](https://github.com/Genymobile/scrcpy/releases/tag/v5.0.1) 解压到同级的 `scrcpy-macos-aarch64-v5.0.1/`。
3. 在项目根目录运行：

   ```sh
   zsh android/build.sh
   zsh app/build.sh
   zsh app/package_dmg.sh
   ```

应用、安卓助手和 DMG 输出到 `dist/`。构建会打包 Python 和 ADB，使用本地签名。Mac 应用尚未经过 Apple 公证。

运行测试：

```sh
python3 -m unittest discover -s tests
```

MacPhone 使用 [scrcpy](https://github.com/Genymobile/scrcpy) 提供的安卓控制与连接能力，随应用附带其 Apache 2.0 许可证。
