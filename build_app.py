"""Cross-platform build and packaging script for Gambit Chess (Windows & macOS)."""

import argparse
import os
import shutil
import subprocess
import sys
import zipfile

from chess_utils import generate_app_icon


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

CPP_SOURCES = [
    "main.cpp",
    "Board.cpp",
    "Move.cpp",
    "Pawn.cpp",
    "Knight.cpp",
    "Bishop.cpp",
    "Rook.cpp",
    "Queen.cpp",
    "King.cpp",
    "Evaluation.cpp",
    "Search.cpp",
]


def compile_cpp_engine(target_os, universal_mac=True):
    """Compile the C++17 engine statically where supported for portability."""
    if target_os == "windows":
        out_name = "gambit.exe"
        compiler = shutil.which("g++") or "g++"
        cmd = [
            compiler,
            "-std=c++17",
            "-O2",
            "-static",
            "-static-libgcc",
            "-static-libstdc++",
            *CPP_SOURCES,
            "-o",
            out_name,
        ]
    elif target_os == "macos":
        out_name = "gambit"
        compiler = shutil.which("clang++") or shutil.which("g++") or "clang++"
        cmd = [compiler, "-std=c++17", "-O2"]
        if universal_mac:
            cmd.extend(["-arch", "arm64", "-arch", "x86_64"])
        cmd.extend([*CPP_SOURCES, "-o", out_name])
    else:
        out_name = "gambit"
        compiler = shutil.which("g++") or "g++"
        cmd = [compiler, "-std=c++17", "-O2", *CPP_SOURCES, "-o", out_name]

    print(f"[build] Compiling C++ engine: {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=ROOT_DIR)
    if proc.returncode != 0 and target_os == "macos" and universal_mac:
        print("[build] Universal macOS compile failed; retrying native architecture...")
        fallback = [compiler, "-std=c++17", "-O2", *CPP_SOURCES, "-o", out_name]
        subprocess.run(fallback, cwd=ROOT_DIR, check=True)
    elif proc.returncode != 0:
        raise RuntimeError(f"C++ compilation failed with exit code {proc.returncode}")

    out_path = os.path.join(ROOT_DIR, out_name)
    if target_os != "windows":
        os.chmod(out_path, 0o755)
    return out_path


def package_app(target_os, skip_compile=False, universal_mac=True):
    """Build standalone GambitChess app bundle + shareable archive in dist/."""
    engine_path = (
        os.path.join(ROOT_DIR, "gambit.exe" if target_os == "windows" else "gambit")
        if skip_compile
        else compile_cpp_engine(target_os, universal_mac=universal_mac)
    )
    if not os.path.exists(engine_path):
        raise FileNotFoundError(f"Engine binary not found: {engine_path}")

    ico_path = os.path.join(ROOT_DIR, "assets", "gambit.ico")
    generate_app_icon(ico_path)

    sep = ";" if sys.platform.startswith("win") else ":"
    pyi_cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name",
        "GambitChess",
        "--add-binary",
        f"{engine_path}{sep}.",
        "--add-data",
        f"{ico_path}{sep}assets",
    ]
    if target_os == "windows":
        pyi_cmd.extend(["--onefile", "--icon", ico_path])
    else:
        pyi_cmd.append("--onedir")

    for module_name in ("ai", "chess_utils", "evaluation"):
        pyi_cmd.extend(["--hidden-import", module_name])

    pyi_cmd.append(os.path.join(ROOT_DIR, "ui.py"))

    print(f"[build] Running PyInstaller: {' '.join(pyi_cmd)}")
    subprocess.run(pyi_cmd, cwd=ROOT_DIR, check=True)

    dist_dir = os.path.join(ROOT_DIR, "dist")
    if target_os == "windows":
        exe_path = os.path.join(dist_dir, "GambitChess.exe")
        if not os.path.exists(exe_path):
            raise FileNotFoundError(f"Expected built exe at {exe_path}")
        zip_path = os.path.join(dist_dir, "GambitChess-Windows.zip")
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.write(exe_path, arcname="GambitChess.exe")
        print(f"[build] Windows package ready: {exe_path}")
        print(f"[build] Windows shareable zip ready: {zip_path}")
        return exe_path, zip_path

    if target_os == "macos":
        app_path = os.path.join(dist_dir, "GambitChess.app")
        zip_path = os.path.join(dist_dir, "GambitChess-macOS.zip")
        dmg_path = os.path.join(dist_dir, "GambitChess-macOS.dmg")
        subprocess.run(
            ["ditto", "-c", "-k", "--sequesterRsrc", "--keepParent", app_path, zip_path],
            cwd=ROOT_DIR,
            check=True,
        )
        if shutil.which("hdiutil"):
            subprocess.run(
                [
                    "hdiutil",
                    "create",
                    "-volname",
                    "Gambit Chess",
                    "-srcfolder",
                    app_path,
                    "-ov",
                    "-format",
                    "UDZO",
                    dmg_path,
                ],
                cwd=ROOT_DIR,
                check=False,
            )
        print(f"[build] macOS app ready: {app_path}")
        print(f"[build] macOS shareable zip ready: {zip_path}")
        return app_path, zip_path

    tar_target = os.path.join(dist_dir, "GambitChess")
    archive = shutil.make_archive(
        os.path.join(dist_dir, "GambitChess-Linux"), "gztar", dist_dir, "GambitChess"
    )
    print(f"[build] Linux package ready: {archive}")
    return tar_target, archive


def main():
    parser = argparse.ArgumentParser(description="Build standalone Gambit Chess desktop app.")
    parser.add_argument(
        "--skip-compile",
        action="store_true",
        help="Reuse existing compiled gambit engine binary.",
    )
    parser.add_argument(
        "--native-mac-arch",
        action="store_true",
        help="Compile only current macOS CPU architecture instead of universal2.",
    )
    args = parser.parse_args()

    if sys.platform.startswith("win"):
        target_os = "windows"
    elif sys.platform == "darwin":
        target_os = "macos"
    else:
        target_os = "linux"

    package_app(
        target_os=target_os,
        skip_compile=args.skip_compile,
        universal_mac=not args.native_mac_arch,
    )


if __name__ == "__main__":
    main()
