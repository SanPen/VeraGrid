# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import os
import sys
import subprocess
import pathlib
import shutil


def convert_svgs(folder: str, backup: bool = True):
    """
    Convert all SVG files in a folder to 'plain SVG' using Inkscape CLI.

    Args:
        folder: Path to the folder containing SVG files.
        backup: Whether to keep a backup of the original files (.bak).
    """
    folder_path = pathlib.Path(folder)

    if not folder_path.exists():
        print(f"❌ Folder not found: {folder}")
        return

    for svg_file in folder_path.rglob("*.svg"):
        out_file = svg_file.with_suffix(".tmp.svg")

        print(f"Converting {svg_file} -> {out_file}")
        try:
            subprocess.run(
                [
                    "inkscape",
                    str(svg_file),
                    "--export-type=svg",
                    f"--export-filename={out_file}"
                ],
                check=True
            )

            if backup:
                backup_file = svg_file.with_suffix(svg_file.suffix + ".bak")
                shutil.move(svg_file, backup_file)
                print(f"  Backup saved: {backup_file}")

            shutil.move(out_file, svg_file)
            print(f"  ✅ Replaced {svg_file} with plain SVG")

        except subprocess.CalledProcessError as e:
            print(f"  ❌ Failed to convert {svg_file}: {e}")
        except Exception as e:
            print(f"  ⚠️ Error with {svg_file}: {e}")


def convert_to_png(root_folder: str, size: int = 64, overwrite: bool = False):
    """
    Recursively converts all SVG files in a folder (and subfolders) to PNGs using Inkscape.
    - root_folder: starting directory
    - size: output width and height in pixels
    - overwrite: overwrite existing PNGs if True
    """
    # Locate inkscape
    inkscape_exe = os.environ.get("INKSCAPE", "inkscape")
    try:
        subprocess.run([inkscape_exe, "--version"], check=True, capture_output=True)
    except Exception:
        if sys.platform == "darwin":
            print("❌ Inkscape not found. On macOS try:")
            print("   export INKSCAPE='/Applications/Inkscape.app/Contents/MacOS/inkscape'")
        else:
            print("❌ Inkscape not found. Add it to PATH or set $INKSCAPE.")
        return

    total, converted, failed = 0, 0, 0

    for dirpath, _, filenames in os.walk(root_folder):
        for fname in filenames:
            if not fname.lower().endswith(".svg"):
                continue
            total += 1
            svg_path = os.path.join(dirpath, fname)
            png_path = os.path.splitext(svg_path)[0] + ".png"

            if os.path.exists(png_path) and not overwrite:
                print(f"⏭️  Skipping existing {png_path}")
                continue

            print(f"🖼️  {svg_path} -> {png_path}")
            try:
                subprocess.run(
                    [
                        inkscape_exe,
                        svg_path,
                        "--export-type=png",
                        f"--export-filename={png_path}",
                        f"--export-width={size}",
                        f"--export-height={size}",
                    ],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                print(f"  ✅ Converted")
                converted += 1
            except subprocess.CalledProcessError:
                print(f"  ❌ Failed")
                failed += 1

    print(f"\n--- Summary ---")
    print(f"Total SVGs   : {total}")
    print(f"Converted PNG: {converted}")
    print(f"Failed       : {failed}")


if __name__ == "__main__":
    dir_path = os.path.dirname(os.path.realpath(__file__))
    # convert_svgs("icons")
    convert_to_png(dir_path)
