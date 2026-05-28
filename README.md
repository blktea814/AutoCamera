# AutoCamera

基于人脸检测的摄像头监控软件，当检测到有人靠近时自动录像。

## 功能

- **实时监控**：检测到人脸靠近时自动开始录像，离开后自动停止
- **事件记录**：记录所有监控事件，可按日期筛选、删除
- **后台运行**：支持最小化到系统托盘，锁屏状态下继续运行
- **开机自启**：可设置开机自动启动（Windows计划任务）


## 快速使用

从 [Releases](../../releases) 页面下载 `AutoCamera.exe`。

### 系统要求

- Windows 10/11 64位
- Microsoft Visual C++ Redistributable

## 从源码运行

```bash
# 安装依赖
pip install -r requirements.txt

# 运行
python main.py

# 打包为 exe
python build.py
```
