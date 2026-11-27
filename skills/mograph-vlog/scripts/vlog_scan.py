#!/usr/bin/env python3
"""Read-only local media inventory; visual interpretation is intentionally deferred."""

import argparse
import json
import math
import os
from pathlib import Path
import stat
import subprocess
import sys


SCHEMA = "mograph-vlog.inventory/v1"
VIDEO_SUFFIXES = frozenset({
    ".mov", ".mp4", ".m4v", ".mkv", ".webm", ".avi", ".mts", ".m2ts",
    ".mpg", ".mpeg", ".3gp", ".3g2", ".ts",
})
IMAGE_SUFFIXES = frozenset({
    ".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".avif",
    ".bmp", ".tif", ".tiff", ".gif",
})
GENERATED_DIRS = frozenset({
    "素材检视", "剪辑过程", "发布包", "mograph-task", "frames", "thumbnails",
    "renders", "render", "outputs", "output", "__pycache__", "node_modules",
})
TIMEOUT = 120


class ScanError(Exception):
    """Expected, safe-to-print error (never includes subprocess output)."""


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ScanError(message)


def frame_count(value):
    try:
        number = int(value)
    except (ValueError, TypeError):
        raise argparse.ArgumentTypeError("--frames must be an integer from 1 to 5")
    if not 1 <= number <= 5:
        raise argparse.ArgumentTypeError("--frames must be from 1 to 5")
    return number


def absolute_no_symlinks(value):
    # Inspect before resolving: resolving first would hide symlinks, including
    # a symlink followed by '..'. Reject links in ancestors as well as leaves.
    path = Path(value).expanduser().absolute()
    for part in reversed((path, *path.parents)):
        if part.is_symlink():
            raise ScanError("symbolic links are not allowed: " + part.name)
    return path.resolve()


def inside(path, directory):
    return path == directory or directory in path.parents


def validate_paths(assets, out):
    source = absolute_no_symlinks(assets)
    output = absolute_no_symlinks(out)
    if not source.is_dir():
        raise ScanError("assets directory does not exist: " + source.name)
    if inside(source, output):
        raise ScanError("output must not be the assets root or its ancestor")
    if output.exists() and not output.is_dir():
        raise ScanError("output is not a directory: " + output.name)
    # Never replace an earlier inventory, frames, original, or a hard link.
    for name in ("inventory.json", "frames", "contact_sheet.jpg"):
        target = output / name
        if target.exists() or target.is_symlink():
            raise ScanError("output collision; use a fresh output directory: " + name)
    return source, output


def error_record(path, reason, stage, asset_id=None):
    result = {
        "path": str(path), "filename": path.name,
        "stage": stage, "reason": reason,
    }
    if asset_id is not None:
        result["asset_id"] = asset_id
    return result


def discover(source, output, recursive, errors):
    found = []

    def visit(directory):
        try:
            with os.scandir(directory) as entries:
                children = sorted(entries, key=lambda item: (item.name.casefold(), item.name))
        except OSError as exc:
            errors.append(error_record(directory, "cannot list directory: " +
                                       type(exc).__name__, "scan"))
            return
        for entry in children:
            path = Path(entry.path)
            if entry.name.startswith(".") or inside(path, output):
                continue
            try:
                if entry.is_symlink():
                    continue
                if entry.is_dir(follow_symlinks=False):
                    name = entry.name.casefold()
                    generated = name in GENERATED_DIRS or name.startswith("mograph-task-")
                    if recursive and not generated:
                        visit(path)
                elif entry.is_file(follow_symlinks=False):
                    if path.suffix.casefold() in VIDEO_SUFFIXES | IMAGE_SUFFIXES:
                        found.append(path)
            except OSError as exc:
                errors.append(error_record(path, "cannot inspect file: " +
                                           type(exc).__name__, "scan"))

    visit(source)
    return sorted(found, key=lambda path: (str(path.relative_to(source)).casefold(),
                                          str(path.relative_to(source))))


def run_tool(command):
    tool = command[0]
    try:
        result = subprocess.run(
            command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace",
            timeout=TIMEOUT, check=False,
        )
    except FileNotFoundError:
        raise ScanError(tool + " is unavailable; install it separately")
    except subprocess.TimeoutExpired:
        raise ScanError(tool + " timed out")
    except OSError as exc:
        raise ScanError(tool + " cannot run: " + type(exc).__name__)
    if result.returncode:
        # Untrusted stderr can contain URLs, credentials or arbitrary metadata.
        raise ScanError(tool + " failed (exit " + str(result.returncode) + ")")
    return result.stdout


def numeric(value):
    try:
        number = float(value)
    except (ValueError, TypeError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def positive_dimension(value, name):
    number = numeric(value)
    if number is None or number <= 0 or not number.is_integer():
        raise ScanError("ffprobe returned invalid " + name)
    return int(number)


def probe(path, kind):
    text = run_tool([
        "ffprobe", "-v", "error", "-protocol_whitelist", "file,pipe",
        "-show_streams", "-show_format", "-of", "json", str(path),
    ])
    try:
        data = json.loads(text)
    except (ValueError, TypeError):
        raise ScanError("ffprobe returned invalid JSON")
    if not isinstance(data, dict) or not isinstance(data.get("streams"), list):
        raise ScanError("ffprobe returned no streams")
    streams = [item for item in data["streams"] if isinstance(item, dict)]
    visual = [item for item in streams if item.get("codec_type") == "video"
              and not (kind == "video" and
                       (item.get("disposition") or {}).get("attached_pic"))]
    if not visual:
        raise ScanError("ffprobe found no visual stream")
    stream = visual[0]
    width = positive_dimension(stream.get("width"), "width")
    height = positive_dimension(stream.get("height"), "height")
    tags = stream.get("tags") or {}
    side_data = stream.get("side_data_list") or []
    rotation = None
    for side in side_data:
        if isinstance(side, dict):
            candidate = numeric(side.get("rotation"))
            if candidate is not None:
                rotation = candidate
                break
    if rotation is None:
        rotation = numeric(tags.get("rotate")) or 0.0
    if rotation.is_integer():
        rotation = int(rotation)
    display_width, display_height = width, height
    if math.isclose(abs(rotation) % 180, 90, abs_tol=0.01):
        display_width, display_height = height, width
    format_data = data.get("format") or {}
    duration = None
    if kind == "video":
        # Container duration is the timeline length; fall back to visual stream.
        duration = numeric(format_data.get("duration"))
        if duration is None or duration <= 0:
            duration = numeric(stream.get("duration"))
        if duration is None or duration <= 0:
            raise ScanError("ffprobe returned no positive video duration")
    transfer = stream.get("color_transfer")
    hdr_side_types = ("mastering display", "content light", "dovi", "hdr10")
    hdr = str(transfer).casefold() in {"smpte2084", "arib-std-b67"} or any(
        any(marker in str(side.get("side_data_type", "")).casefold()
            for marker in hdr_side_types)
        for side in side_data if isinstance(side, dict)
    )
    format_tags = format_data.get("tags") or {}
    creation_time = tags.get("creation_time") or format_tags.get("creation_time")
    return {
        "duration": duration, "codec_name": stream.get("codec_name"),
        "stream_index": stream.get("index", 0),
        "width": width, "height": height,
        "display_width": display_width, "display_height": display_height,
        "rotation": rotation,
        "has_audio": any(item.get("codec_type") == "audio" for item in streams),
        "color_transfer": transfer, "is_hdr": hdr,
        "hdr_status": "metadata_indicated" if hdr else "not_indicated",
        "creation_time": creation_time,
        "creation_time_source": "metadata_not_verified_capture_time",
    }


def sample_times(duration, count):
    """Interior samples avoid blank/end-of-stream frames; 3 => 10%, 50%, 90%."""
    if count == 1:
        return [duration * 0.5]
    return [duration * (0.1 + 0.8 * index / (count - 1)) for index in range(count)]


def check_source(path, source):
    safe = absolute_no_symlinks(path)
    if not inside(safe, source) or not stat.S_ISREG(safe.stat().st_mode):
        raise ScanError("source is no longer a regular file inside assets")


def thumbnail(path, target, time, stream_index):
    if target.exists() or target.is_symlink():
        raise ScanError("thumbnail output already exists: " + target.name)
    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-n",
        "-protocol_whitelist", "file,pipe", "-autorotate", "-i", str(path),
    ]
    if time is not None:
        # Output seeking decodes the actual timestamp, including rotated footage.
        command.extend(["-ss", format(time, ".9f")])
    command.extend([
        "-map", "0:" + str(stream_index), "-frames:v", "1", "-an", "-sn", "-dn",
        "-vf", "scale=480:480:force_original_aspect_ratio=decrease:force_divisible_by=2,setsar=1",
        "-q:v", "3", "-update", "1", str(target),
    ])
    run_tool(command)
    if target.is_symlink() or not target.is_file() or target.stat().st_size == 0:
        raise ScanError("ffmpeg produced no thumbnail: " + target.name)


def load_pillow():
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return None
    return Image, ImageDraw


def make_contact_sheet(assets, output):
    modules = load_pillow()
    frames = [(asset, frame) for asset in assets for frame in asset["frames"]]
    if modules is None or not frames:
        return None
    Image, ImageDraw = modules
    cell_width, cell_height, columns = 288, 220, min(4, len(frames))
    rows = math.ceil(len(frames) / columns)
    sheet = Image.new("RGB", (columns * cell_width, rows * cell_height), "#202020")
    draw = ImageDraw.Draw(sheet)
    try:
        for index, (asset, frame) in enumerate(frames):
            x, y = index % columns * cell_width, index // columns * cell_height
            with Image.open(frame["path"]) as image:
                image = image.convert("RGB")
                image.thumbnail((cell_width - 12, 172))
                sheet.paste(image, (x + (cell_width - image.width) // 2, y + 4))
            # ASCII labels work with Pillow's bundled font, without installing fonts.
            filename = Path(asset["path"]).name.encode("ascii", "backslashreplace").decode("ascii")
            label = asset["id"] + " " + filename
            time = "Image" if frame["time"] is None else "Time: %.3fs" % frame["time"]
            draw.text((x + 6, y + 180), label[:43], fill="white")
            draw.text((x + 6, y + 198), time, fill="white")
        target = output / "contact_sheet.jpg"
        with target.open("xb") as file:
            sheet.save(file, format="JPEG", quality=85)
        return str(target)
    finally:
        sheet.close()


def scan(assets, out, recursive=False, frames=3):
    if not isinstance(frames, int) or isinstance(frames, bool) or not 1 <= frames <= 5:
        raise ScanError("--frames must be from 1 to 5")
    source, output = validate_paths(assets, out)
    inventory = {
        "schema": SCHEMA, "source_root": str(source), "assets": [],
        "errors": [], "contact_sheet": None,
    }
    paths = discover(source, output, recursive, inventory["errors"])
    output.mkdir(parents=True, exist_ok=True)
    frame_dir = output / "frames"
    frame_dir.mkdir(exist_ok=False)
    for index, path in enumerate(paths, 1):
        kind = "video" if path.suffix.casefold() in VIDEO_SUFFIXES else "image"
        asset = {
            "id": "m%03d" % index, "path": str(path), "kind": kind,
            "duration": None, "width": None, "height": None,
            "display_width": None, "display_height": None, "rotation": None,
            "has_audio": None, "codec_name": None, "color_transfer": None,
            "is_hdr": None, "hdr_status": "unknown", "creation_time": None,
            "creation_time_source": "metadata_not_verified_capture_time",
            "speech_status": "not_assessed",
            "audio_note": "audio_presence_is_not_evidence_of_speech",
            "analysis_status": "needs_visual_review", "frames": [],
        }
        inventory["assets"].append(asset)  # Keep broken files visible in inventory.
        try:
            check_source(path, source)
            metadata = probe(path, kind)
            stream_index = metadata.pop("stream_index")
            asset.update(metadata)
        except (ScanError, OSError, ValueError, TypeError, AttributeError) as exc:
            reason = str(exc) if isinstance(exc, ScanError) else "invalid media metadata or file: " + type(exc).__name__
            inventory["errors"].append(error_record(path, reason, "probe", asset["id"]))
            continue
        times = sample_times(asset["duration"], frames) if kind == "video" else [None]
        for frame_index, time in enumerate(times, 1):
            target = frame_dir / (asset["id"] + "_%02d.jpg" % frame_index)
            try:
                check_source(path, source)
                thumbnail(path, target, time, stream_index)
                asset["frames"].append({"time": time, "path": str(target)})
            except (ScanError, OSError) as exc:
                reason = str(exc) if isinstance(exc, ScanError) else "cannot export thumbnail: " + type(exc).__name__
                inventory["errors"].append(error_record(path, reason, "thumbnail", asset["id"]))
    try:
        inventory["contact_sheet"] = make_contact_sheet(inventory["assets"], output)
    except Exception as exc:
        inventory["errors"].append(error_record(
            output / "contact_sheet.jpg", "contact sheet failed: " + type(exc).__name__, "contact_sheet"))
    with (output / "inventory.json").open("x", encoding="utf-8") as file:
        json.dump(inventory, file, ensure_ascii=False, indent=2, allow_nan=False)
        file.write("\n")
    return inventory, output / "inventory.json"


def main(argv=None):
    parser = JsonArgumentParser(description=__doc__)
    parser.add_argument("--assets", required=True, help="Local source directory (read-only)")
    parser.add_argument("--out", required=True, help="Independent output directory; existing scan files are never replaced")
    parser.add_argument("--recursive", action="store_true", help="Include non-hidden subdirectories, without following symlinks")
    parser.add_argument("--frames", type=frame_count, default=3, help="Samples per video, 1..5 (default: 3)")
    try:
        args = parser.parse_args(argv)
        inventory, inventory_path = scan(args.assets, args.out, args.recursive, args.frames)
        error_count = len(inventory["errors"])
        summary = {
            "ok": not error_count, "inventory": str(inventory_path),
            "assets": len(inventory["assets"]),
            "videos": sum(asset["kind"] == "video" for asset in inventory["assets"]),
            "images": sum(asset["kind"] == "image" for asset in inventory["assets"]),
            "errors": error_count, "contact_sheet": inventory["contact_sheet"],
        }
        if error_count:
            # Full per-file diagnostics live in inventory, not an unbounded stdout dump.
            summary["first_error"] = {key: inventory["errors"][0][key]
                                      for key in ("filename", "stage", "reason")}
        code = 1 if error_count else 0
    except ScanError as exc:
        summary, code = {"ok": False, "errors": 1, "reason": str(exc)}, 1
    except Exception as exc:
        filename = getattr(exc, "filename", None)
        summary = {"ok": False, "errors": 1, "reason": "scan failed: " + type(exc).__name__}
        if filename:
            summary["filename"] = Path(filename).name
        code = 1
    except KeyboardInterrupt:
        summary, code = {"ok": False, "errors": 1, "reason": "scan interrupted"}, 1
    print(json.dumps(summary, ensure_ascii=False, allow_nan=False))
    return code


if __name__ == "__main__":
    sys.exit(main())
