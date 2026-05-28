# AutoCamera

基于人脸检测的智能摄像头监控软件，当检测到有人靠近时自动录像。

## 功能

- **实时监控**：基于 MediaPipe 人脸检测，自动识别靠近的人
- **自动录像**：检测到人脸靠近时自动开始录像，离开后自动停止
- **事件记录**：记录所有监控事件，支持按日期筛选、删除
- **录像回放**：内置视频播放器，可直接回放录像
- **后台运行**：支持最小化到系统托盘，锁屏状态下继续运行
- **开机自启**：一键设置开机自动启动（Windows 计划任务）
- **自定义存储目录**：可设置录像文件保存位置
- **可调阈值**：调整人脸检测的触发距离（0.03 - 0.15）

## 快速使用

从 [Releases](../../releases) 页面下载 `AutoCamera.exe`，双击即可运行，无需安装。

### 系统要求

- Windows 10/11 64位
- 摄像头
- Microsoft Visual C++ Redistributable（大多数系统已预装）

## 从源码运行

```bash
# 安装依赖
pip install -r requirements.txt

# 运行
python main.py

# 打包为 exe
python build.py
```

## 技术栈

- Python 3.10
- PyQt6（GUI）
- OpenCV（摄像头与视频处理）
- MediaPipe（人脸检测）
- SQLite（事件记录）
- PyInstaller（打包）

## 作者

by BLKTEA  
小黑盒ID：68344144
