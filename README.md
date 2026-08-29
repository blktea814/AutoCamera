# AutoCamera

基于人脸检测的摄像头监控软件，当检测到有人靠近时自动录像，支持 Windows 和 macOS。

## 功能

- **实时监控**：检测到人脸靠近时自动开始录像，离开后自动停止
- **事件记录**：记录所有监控事件，可按日期筛选、删除
- **后台运行**：支持最小化到系统托盘，锁屏状态下继续运行
- **开机自启**：Windows 使用计划任务，macOS 使用用户级 LaunchAgent


## 快速使用

从 [Releases](../../releases) 页面下载对应平台版本：

- Windows 10/11 64 位：`AutoCamera.exe`
- macOS Apple Silicon（arm64）：`AutoCamera-macOS-arm64.zip`

### 系统要求

- Windows 10/11 64位或 macOS Apple Silicon（arm64）
- Windows 运行打包程序需要 Microsoft Visual C++ Redistributable

macOS 首次运行时，需要在“系统设置 -> 隐私与安全性 -> 摄像头”中允许 AutoCamera 访问摄像头。

## 从源码运行（可选）

```bash
# 创建/进入 Conda 环境（推荐）
conda create -n py310 python=3.10
conda activate py310

# 安装依赖
python -m pip install -r requirements.txt
python -m pip install pillow pyinstaller

# 运行
python main.py

# 打包
python build.py
```

在 Windows 上生成单文件 `dist/AutoCamera.exe`；在 macOS 上生成应用包 `dist/AutoCamera.app`。请在目标操作系统上分别构建，不能从 macOS 交叉打包 Windows 程序，反之亦然。
