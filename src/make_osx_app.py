#!/usr/bin/env python3
"""
build_veragrid_app.py

End-to-end macOS build script that:

- Copies a system Python distribution into the app bundle
- Installs veragrid into the embedded Python
- Creates a Terminal-launching .app (using a fixed launcher contract)
- Codesigns the app
- Builds a DMG installer

All configuration is defined below.
"""

from pathlib import Path
import plistlib
import shutil
import stat
import subprocess
import sys
from VeraGrid.__version__ import __VeraGrid_VERSION__

# =============================================================================
# CONFIGURATION (EDIT ONLY THIS SECTION)
# =============================================================================

APP_NAME = "VeraGrid"
BUNDLE_ID = "com.eroots.veragrid"
VERSION = __VeraGrid_VERSION__
MIN_MACOS = "13.0"

# System Python distribution to copy
SYSTEM_PYTHON_ROOT = Path(
    "../osx_resources/python_3.13.11_standalone"
)

# Name of the directory inside Resources
EMBEDDED_PYTHON_DIRNAME = "3.13"

# Package to install in embedded Python
PIP_INSTALL_TARGET = "veragrid"

# App icon (.png or .icns)
ICON_PATH = Path("../pics/VeraGrid_icon.png")

# Build/output directories
BUILD_ROOT = Path("osx_dist")
OUTPUT_DIR = BUILD_ROOT / "output"
DMG_NAME = f"VeraGrid_{__VeraGrid_VERSION__}.dmg"

# Behaviour flags
CLEAN_BUILD = True
ENABLE_CODESIGN = True

# =============================================================================


def run(cmd, *, cwd=None):
    print(">>", " ".join(map(str, cmd)))
    subprocess.check_call(cmd, cwd=cwd)


def ensure_macos():
    if sys.platform != "darwin":
        raise RuntimeError("This script must be run on macOS")


def make_executable(path: Path):
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


# -----------------------------------------------------------------------------
# Info.plist
# -----------------------------------------------------------------------------

def write_info_plist(plist_path: Path, icon_name: str | None):
    plist = {
        "CFBundleName": APP_NAME,
        "CFBundleDisplayName": APP_NAME,
        "CFBundleIdentifier": BUNDLE_ID,
        "CFBundleVersion": VERSION,
        "CFBundleShortVersionString": VERSION,
        "CFBundleExecutable": APP_NAME,
        "CFBundlePackageType": "APPL",
        "LSMinimumSystemVersion": MIN_MACOS,
        "NSHighResolutionCapable": True,
    }

    if icon_name:
        plist["CFBundleIconFile"] = icon_name

    with plist_path.open("wb") as f:
        plistlib.dump(plist, f, sort_keys=False)


# -----------------------------------------------------------------------------
# Icon handling
# -----------------------------------------------------------------------------

def create_icns_from_png(png: Path, icns: Path):
    iconset = icns.parent / f"{icns.stem}.iconset"
    iconset.mkdir(parents=True, exist_ok=True)

    sizes = [
        (16, "icon_16x16.png"),
        (32, "icon_16x16@2x.png"),
        (32, "icon_32x32.png"),
        (64, "icon_32x32@2x.png"),
        (128, "icon_128x128.png"),
        (256, "icon_128x128@2x.png"),
        (256, "icon_256x256.png"),
        (512, "icon_256x256@2x.png"),
        (512, "icon_512x512.png"),
        (1024, "icon_512x512@2x.png"),
    ]

    for px, name in sizes:
        run([
            "sips", "-z", str(px), str(px),
            str(png), "--out", str(iconset / name)
        ])

    run(["iconutil", "-c", "icns", str(iconset), "-o", str(icns)])
    shutil.rmtree(iconset, ignore_errors=True)


# -----------------------------------------------------------------------------
# Python distribution handling
# -----------------------------------------------------------------------------

def copy_python_distribution(dst: Path):
    print(f">> Copying Python distribution to {dst}")
    shutil.copytree(
        SYSTEM_PYTHON_ROOT,
        dst,
        symlinks=True
    )







def install_veragrid(python_bin: Path):
    run([python_bin, "-m", "pip", "install", "--upgrade", "pip"])

    run([
        python_bin, "-m", "pip", "install",
        "--no-user",
        "--no-cache-dir",
        "--disable-pip-version-check",
        PIP_INSTALL_TARGET
    ])


# -----------------------------------------------------------------------------
# Launcher (EXACT CONTRACT AS REQUESTED)
# -----------------------------------------------------------------------------

def create_launcher(launcher_path: Path):
    script = f"""#!/bin/bash

APP_DIR="$(cd "$(dirname "$0")" && pwd)"

PYTHON="$APP_DIR/../Resources/python/bin/python"

CMD="$PYTHON -c 'from VeraGrid.ExecuteVeraGrid import runVeraGrid; runVeraGrid()'; exec \\$SHELL"

/usr/bin/osascript <<EOF
tell application "Terminal"
    activate
    do script "$CMD"
end tell
EOF
"""
    launcher_path.write_text(script, encoding="utf-8")
    make_executable(launcher_path)


# -----------------------------------------------------------------------------
# Codesigning
# -----------------------------------------------------------------------------

def codesign_app(app_path: Path):
    run(["codesign", "--force", "--deep", "--sign", "-", str(app_path)])
    run(["codesign", "--verify", "--verbose", str(app_path)])


# -----------------------------------------------------------------------------
# DMG creation
# -----------------------------------------------------------------------------

def create_dmg(app_path: Path, dmg_path: Path):
    dmg_root = BUILD_ROOT / "dmg_root"
    if dmg_root.exists():
        shutil.rmtree(dmg_root)

    dmg_root.mkdir()
    shutil.copytree(
        app_path,
        dmg_root / app_path.name,
        symlinks=True,
        ignore_dangling_symlinks=True
    )
    (dmg_root / "Applications").symlink_to("/Applications")

    run([
        "hdiutil", "create",
        "-volname", APP_NAME,
        "-srcfolder", dmg_root,
        "-ov",
        "-format", "UDZO",
        dmg_path
    ])

    shutil.rmtree(dmg_root)


# -----------------------------------------------------------------------------
# Main build routine
# -----------------------------------------------------------------------------

def main():
    ensure_macos()

    if CLEAN_BUILD and BUILD_ROOT.exists():
        shutil.rmtree(BUILD_ROOT)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    app_path = OUTPUT_DIR / f"{APP_NAME}.app"
    contents = app_path / "Contents"
    macos_dir = contents / "MacOS"
    resources = contents / "Resources"
    python_dst = resources / EMBEDDED_PYTHON_DIRNAME

    macos_dir.mkdir(parents=True)
    resources.mkdir(parents=True)

    # Copy Python
    python_base = resources / "python"

    copy_python_distribution(python_base)

    python_bin = python_base / "bin" / "python3"

    run([
        python_bin, "-c",
        "import sys, site; print(sys.executable); print(sys.prefix); print(site.getsitepackages())"
    ])

    if not python_bin.exists():
        raise RuntimeError("Embedded python binary not found")

    # Install veragrid
    install_veragrid(python_bin)

    # Icon
    icon_name = None
    if ICON_PATH:
        icns = resources / f"{APP_NAME}.icns"
        if ICON_PATH.suffix.lower() == ".icns":
            shutil.copy2(ICON_PATH, icns)
        else:
            create_icns_from_png(ICON_PATH, icns)
        icon_name = APP_NAME

    # Info.plist
    write_info_plist(contents / "Info.plist", icon_name)

    # Launcher
    create_launcher(macos_dir / APP_NAME)

    # Codesign
    if ENABLE_CODESIGN:
        codesign_app(app_path)

    # DMG
    dmg_path = OUTPUT_DIR / DMG_NAME
    create_dmg(app_path, dmg_path)

    print("\nBUILD COMPLETE")
    print(f"App : {app_path}")
    print(f"DMG : {dmg_path}")


if __name__ == "__main__":
    main()