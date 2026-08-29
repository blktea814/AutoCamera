"""Build a platform-native AutoCamera application with PyInstaller."""
import subprocess
import sys
import os
import plistlib


def generate_windows_icon():
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


def patch_macos_plist(project_dir):
    plist_path = os.path.join(project_dir, "dist", "AutoCamera.app", "Contents", "Info.plist")
    if not os.path.exists(plist_path):
        return
    with open(plist_path, "rb") as f:
        plist = plistlib.load(f)
    plist.update({
        "NSCameraUsageDescription": "AutoCamera 需要访问摄像头，以检测有人靠近并自动录像。",
        "CFBundleDisplayName": "AutoCamera",
    })
    with open(plist_path, "wb") as f:
        plistlib.dump(plist, f, sort_keys=False)
    print(f"已写入 macOS 摄像头权限声明: {plist_path}")


def resign_macos_app(project_dir):
    app_path = os.path.join(project_dir, "dist", "AutoCamera.app")
    result = subprocess.run(
        ["codesign", "--force", "--deep", "--sign", "-", app_path,
         "--timestamp=none"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print(f"已完成 macOS ad-hoc 签名: {app_path}")
    else:
        print(f"警告：macOS 签名失败，请手动签名后分发：{result.stderr.strip()}")


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

    project_dir = os.path.dirname(os.path.abspath(__file__))
    custom_ico = os.path.join(project_dir, "dist", "favicon.ico")
    custom_icns = os.path.join(project_dir, "dist", "favicon.icns")
    if sys.platform == "darwin":
        icon_path = custom_icns if os.path.exists(custom_icns) else None
        if icon_path:
            print(f"使用自定义图标: {icon_path}")
    else:
        icon_path = custom_ico if os.path.exists(custom_ico) else generate_windows_icon()

    import cv2
    import mediapipe
    package_mode = "--onedir" if sys.platform == "darwin" else "--onefile"
    mediapipe_dir = os.path.dirname(mediapipe.__file__)
    face_detection_dir = os.path.join(mediapipe_dir, "modules", "face_detection")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "AutoCamera",
        package_mode,
        "--windowed",
        "--noconfirm",
        "--add-data", f"config.json{os.pathsep}.",
        "--hidden-import", "mediapipe",
        "--hidden-import", "mediapipe.python._framework_bindings",
        "--hidden-import", "mediapipe.python._framework_bindings.calculator_graph",
        "--hidden-import", "mediapipe.python._framework_bindings.image_frame",
        "--hidden-import", "mediapipe.python._framework_bindings.packet",
        "--hidden-import", "mediapipe.python._framework_bindings.resource_util",
        "--hidden-import", "mediapipe.python._framework_bindings.validated_graph_config",
        "--hidden-import", "mediapipe.python.solutions.face_detection",
        "--hidden-import", "mediapipe.python.solution_base",
        "--hidden-import", "mediapipe.modules.face_detection.face_detection_pb2",
        "--add-data", f"{os.path.join(face_detection_dir, 'face_detection_short_range.tflite')}{os.pathsep}mediapipe/modules/face_detection",
        "--add-data", f"{os.path.join(face_detection_dir, 'face_detection_short_range_cpu.binarypb')}{os.pathsep}mediapipe/modules/face_detection",
    ]

    if icon_path:
        cmd.extend(["--icon", icon_path])
    if sys.platform == "darwin":
        cmd.extend(["--osx-bundle-identifier", "com.blktea814.autocamera"])
        for ex in ("jax", "jaxlib", "sentencepiece"):
            cmd.extend(["--exclude-module", ex])

    if sys.platform == "win32":
        cv2_dir = os.path.dirname(cv2.__file__)
        for dll in os.listdir(cv2_dir):
            if "ffmpeg" in dll.lower():
                cmd.extend(["--add-binary", f"{os.path.join(cv2_dir, dll)}{os.pathsep}."])

    for ex in excludes:
        cmd.extend(["--exclude-module", ex])

    cmd.append("main.py")
    
    output_name = "AutoCamera.app" if sys.platform == "darwin" else "AutoCamera.exe"
    print(f"正在打包 {output_name} ...")
    print(f"排除模块: {', '.join(excludes)}")
    subprocess.run(cmd, check=True)

    if sys.platform == "darwin":
        patch_macos_plist(project_dir)
        resign_macos_app(project_dir)
    
    print("\n打包完成！")
    if sys.platform == "darwin":
        print("  输出: dist/AutoCamera.app")
        print("  首次运行请在系统设置 -> 隐私与安全性 -> 摄像头中允许 AutoCamera")
    else:
        print("  输出: dist/AutoCamera.exe")
        print("  可在程序中启用开机自启+锁屏运行")


if __name__ == "__main__":
    if not os.path.exists("config.json"):
        from utils.config import load_config
        load_config()
    build()
