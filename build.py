"""
打包脚本 - 将项目编译为单个 exe 文件
使用方法: python build.py
"""
import subprocess
import sys
import os


def generate_icon():
    from PIL import Image, ImageDraw
    sizes = [16, 32, 48, 64, 128, 256]
    images = []
    for size in sizes:
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        m = size // 16
        draw.ellipse([2*m, 2*m, size-2*m, size-2*m], fill=(76, 175, 80))
        draw.ellipse([5*m, 5*m, size-5*m, size-5*m], fill=(255, 255, 255))
        draw.ellipse([6*m, 6*m, size-6*m, size-6*m], fill=(33, 33, 33))
        images.append(img)
    ico_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.ico')
    images[0].save(ico_path, format='ICO', sizes=[(s, s) for s in sizes], append_images=images[1:])
    print(f"图标已生成: {ico_path}")
    return ico_path


def build():
    excludes = [
        "tensorflow", "tensorflow_intel", "tensorboard", "keras",
        "torch", "torchvision", "torchaudio",
        "ultralytics", "onnx", "onnxruntime",
        "scipy", "pandas", "sklearn", "scikit-learn",
        "IPython", "jupyter", "notebook",
        "pytest",
        "tkinter", "wx",
        "transformers", "huggingface_hub",
    ]

    custom_ico = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist', 'favicon.ico')
    if os.path.exists(custom_ico):
        ico_path = custom_ico
        print(f"使用自定义图标: {ico_path}")
    else:
        ico_path = generate_icon()

    import cv2
    cv2_dir = os.path.dirname(cv2.__file__)
    ffmpeg_dlls = [f for f in os.listdir(cv2_dir) if 'ffmpeg' in f.lower()]

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "AutoCamera",
        "--onefile",
        "--windowed",
        "--icon", ico_path,
        "--add-data", "config.json;.",
        "--hidden-import", "mediapipe",
        "--hidden-import", "mediapipe.python._framework_bindings",
        "--collect-submodules", "mediapipe",
        "--collect-data", "mediapipe",
    ]

    for dll in ffmpeg_dlls:
        cmd.extend(["--add-binary", f"{os.path.join(cv2_dir, dll)};."])

    for ex in excludes:
        cmd.extend(["--exclude-module", ex])

    cmd.append("main.py")
    
    print("正在打包 AutoCamera.exe ...")
    print(f"排除模块: {', '.join(excludes)}")
    subprocess.run(cmd, check=True)
    
    print("\n打包完成！")
    print("  输出: dist/AutoCamera.exe")
    print("\n运行 install_service.bat (以管理员身份) 可注册开机自启+锁屏运行")


if __name__ == "__main__":
    if not os.path.exists("config.json"):
        from utils.config import load_config
        load_config()
    build()
