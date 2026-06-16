"""
PyInstaller 打包脚本
运行: python build.py
"""
import os
import sys

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(ROOT_DIR, "src")
ASSETS_DIR = os.path.join(ROOT_DIR, "assets")

os.makedirs(ASSETS_DIR, exist_ok=True)

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--name=CryptoMemoPet",
    "--onefile",
    "--noconsole",
    f"--add-data={ASSETS_DIR};assets",
    "--hidden-import=PIL._tkinter_finder",
    f"--distpath={os.path.join(ROOT_DIR, 'dist')}",
    f"--workpath={os.path.join(ROOT_DIR, 'build')}",
    f"--specpath={ROOT_DIR}",
    os.path.join(SRC_DIR, "main.py"),
]

print("Building CryptoMemoPet.exe...")
print(" ".join(cmd))
os.execv(sys.executable, cmd)
