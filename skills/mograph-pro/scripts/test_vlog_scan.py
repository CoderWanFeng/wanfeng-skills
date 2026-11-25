#!/usr/bin/env python3
"""Local-only scanner tests: all media and outputs are temporary, tools are mocked."""

import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import vlog_scan


def probe_data(rotation=None, audio=False, duration="10.0", image=False):
    stream = {
        "index": 0, "codec_type": "video", "codec_name": "mjpeg" if image else "h264",
        "width": 1920, "height": 1080, "color_transfer": "bt709",
        "tags": {"creation_time": "2026-01-01T00:00:00Z"},
    }
    if rotation is not None:
        stream["side_data_list"] = [{"side_data_type": "Display Matrix", "rotation": rotation}]
    streams = [stream]
    if audio:
        # AAC is equally compatible with ambience, music and speech; do not infer speech.
        streams.append({"index": 1, "codec_type": "audio", "codec_name": "aac"})
    return {"streams": streams, "format": {"duration": duration}}


class VlogScanTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="test-vlog-scan-")
        self.addCleanup(self.temporary.cleanup)
        # macOS may expose tempfile through /var -> /private/var. Tests pass
        # canonical real paths; explicit symlink cases below use actual links.
        self.root = Path(self.temporary.name).resolve()
        self.source = self.root / "assets with spaces"
        self.source.mkdir()
        self.output = self.root / "review with spaces"
        self.calls = []
        self.real_load_pillow = vlog_scan.load_pillow
        pillow = mock.patch.object(vlog_scan, "load_pillow", return_value=None)
        pillow.start()
        self.addCleanup(pillow.stop)

    def media(self, name="clip.MOV", directory=None):
        path = (directory or self.source) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"original fixture, never modified")
        return path

    def fake_tools(self, data=None, bad_probe=(), bad_thumbnail=False, no_frame=False):
        metadata = data if data is not None else probe_data()

        def run(command, **kwargs):
            self.calls.append((command, kwargs))
            self.assertEqual(kwargs["stdin"], subprocess.DEVNULL)
            self.assertEqual(kwargs["stdout"], subprocess.PIPE)
            self.assertEqual(kwargs["stderr"], subprocess.PIPE)
            self.assertFalse(kwargs["check"])
            self.assertNotIn("shell", kwargs)
            self.assertIn("-protocol_whitelist", command)
            self.assertEqual(command[command.index("-protocol_whitelist") + 1], "file,pipe")
            if command[0] == "ffprobe":
                path = Path(command[-1])
                if path.name in bad_probe:
                    return subprocess.CompletedProcess(command, 1, "", "secret=https://user:credential@host/")
                selected = metadata[path.name] if isinstance(metadata, dict) and "streams" not in metadata else metadata
                return subprocess.CompletedProcess(command, 0, json.dumps(selected), "")
            self.assertEqual(command[0], "ffmpeg")
            self.assertIn("-n", command)
            self.assertNotIn("-y", command)
            self.assertIn("-an", command)
            self.assertEqual(command[command.index("-autorotate") + 1], "-i")
            if bad_thumbnail:
                return subprocess.CompletedProcess(command, 1, "", "private token and decoder failure")
            if not no_frame:
                Path(command[-1]).write_bytes(b"mock thumbnail")
            return subprocess.CompletedProcess(command, 0, "", "")

        return mock.patch.object(vlog_scan.subprocess, "run", side_effect=run)

    def scan(self, **kwargs):
        return vlog_scan.scan(self.source, self.output, **kwargs)

    def invoke(self, argv):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = vlog_scan.main(argv)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(len(stdout.getvalue().splitlines()), 1)
        self.assertNotIn("Traceback", stdout.getvalue())
        return code, json.loads(stdout.getvalue())

    def test_video_rotation_duration_metadata_and_equal_samples(self):
        path = self.media()
        original = path.read_bytes()
        with self.fake_tools(probe_data(rotation=-90, audio=True)):
            inventory, destination = self.scan()
        asset = inventory["assets"][0]
        self.assertEqual(inventory["schema"], vlog_scan.SCHEMA)
        self.assertEqual(inventory["source_root"], str(self.source))
        self.assertEqual(asset["id"], "m001")
        self.assertEqual(asset["path"], str(path))
        self.assertEqual(asset["kind"], "video")
        self.assertEqual(asset["duration"], 10.0)
        self.assertEqual((asset["width"], asset["height"]), (1920, 1080))
        self.assertEqual((asset["display_width"], asset["display_height"]), (1080, 1920))
        self.assertEqual(asset["rotation"], -90)
        self.assertEqual(asset["codec_name"], "h264")
        self.assertEqual(asset["analysis_status"], "needs_visual_review")
        self.assertEqual(asset["creation_time"], "2026-01-01T00:00:00Z")
        self.assertEqual(asset["creation_time_source"], "metadata_not_verified_capture_time")
        for actual, expected in zip([frame["time"] for frame in asset["frames"]], [1, 5, 9]):
            self.assertAlmostEqual(actual, expected)
        for frame in asset["frames"]:
            self.assertTrue(Path(frame["path"]).is_absolute())
            self.assertTrue(Path(frame["path"]).is_file())
            self.assertTrue(vlog_scan.inside(Path(frame["path"]), self.output))
        self.assertEqual(inventory["errors"], [])
        self.assertIsNone(inventory["contact_sheet"])
        self.assertEqual(json.loads(destination.read_text(encoding="utf-8")), inventory)
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual(len(self.calls), 4)
        for command, _ in self.calls[1:]:
            self.assertEqual(command[command.index("-i") + 1], str(path))
            self.assertIn("scale=", command[command.index("-vf") + 1])

    def test_silent_and_non_voice_audio_never_imply_narration(self):
        self.media("silent.mp4")
        self.media("ambient.mp4")
        data = {"silent.mp4": probe_data(audio=False), "ambient.mp4": probe_data(audio=True)}
        with self.fake_tools(data):
            inventory, _ = self.scan(frames=1)
        by_name = {Path(asset["path"]).name: asset for asset in inventory["assets"]}
        self.assertFalse(by_name["silent.mp4"]["has_audio"])
        self.assertTrue(by_name["ambient.mp4"]["has_audio"])
        for asset in inventory["assets"]:
            self.assertEqual(asset["speech_status"], "not_assessed")
            self.assertEqual(asset["audio_note"], "audio_presence_is_not_evidence_of_speech")
            self.assertNotIn("transcript", asset)
            self.assertNotIn("has_voiceover", asset)

    def test_legacy_rotation_tag_and_display_matrix_precedence(self):
        self.media()
        data = probe_data()
        data["streams"][0]["tags"]["rotate"] = "270"
        with self.fake_tools(data):
            metadata = vlog_scan.probe(self.source / "clip.MOV", "video")
        self.assertEqual(metadata["rotation"], 270)
        self.assertEqual(metadata["display_width"], 1080)
        data["streams"][0]["side_data_list"] = [{"rotation": 0}]
        with self.fake_tools(data):
            metadata = vlog_scan.probe(self.source / "clip.MOV", "video")
        self.assertEqual(metadata["rotation"], 0)
        self.assertEqual(metadata["display_width"], 1920)

    def test_hdr_pq_hlg_and_side_metadata(self):
        path = self.media()
        for transfer, sides, expected in (
            ("smpte2084", [], True), ("arib-std-b67", [], True),
            ("bt709", [{"side_data_type": "Mastering display metadata"}], True),
            ("bt709", [{"side_data_type": "DOVI configuration record"}], True),
            ("bt709", [], False), (None, [], False),
        ):
            with self.subTest(transfer=transfer, sides=sides):
                data = probe_data()
                data["streams"][0].update(color_transfer=transfer, side_data_list=sides)
                with self.fake_tools(data):
                    metadata = vlog_scan.probe(path, "video")
                self.assertEqual(metadata["color_transfer"], transfer)
                self.assertEqual(metadata["is_hdr"], expected)
                self.assertEqual(metadata["hdr_status"], "metadata_indicated" if expected else "not_indicated")

    def test_duration_stream_fallback_and_creation_time_format_fallback(self):
        path = self.media()
        data = probe_data(duration="N/A")
        data["streams"][0]["duration"] = "2.5"
        data["streams"][0]["tags"] = {}
        data["format"]["tags"] = {"creation_time": "metadata only"}
        with self.fake_tools(data):
            metadata = vlog_scan.probe(path, "video")
        self.assertEqual(metadata["duration"], 2.5)
        self.assertEqual(metadata["creation_time"], "metadata only")

    def test_attached_cover_is_not_the_video_stream(self):
        path = self.media()
        data = probe_data()
        data["streams"].insert(0, {
            "index": 2, "codec_type": "video", "width": 100, "height": 100,
            "disposition": {"attached_pic": 1},
        })
        with self.fake_tools(data):
            metadata = vlog_scan.probe(path, "video")
        self.assertEqual(metadata["width"], 1920)
        self.assertEqual(metadata["stream_index"], 0)

    def test_images_only_without_script_or_video(self):
        for name in ("still.JPG", "still.png", "still.webp", "still.heic", "still.heif", "still.avif"):
            self.media(name)
        self.media(".env")
        self.media("not-media.txt")
        with self.fake_tools(probe_data(image=True)):
            code, summary = self.invoke(["--assets", str(self.source), "--out", str(self.output)])
        self.assertEqual(code, 0)
        self.assertEqual(summary["videos"], 0)
        self.assertEqual(summary["images"], 6)
        self.assertNotIn("frames", summary)
        inventory = json.loads((self.output / "inventory.json").read_text())
        for asset in inventory["assets"]:
            self.assertEqual(asset["kind"], "image")
            self.assertIsNone(asset["duration"])
            self.assertEqual(asset["frames"][0]["time"], None)
            self.assertEqual(len(asset["frames"]), 1)
        self.assertEqual(len(self.calls), 12)
        for command, _ in self.calls:
            self.assertNotIn(".env", " ".join(command))
            if command[0] == "ffmpeg":
                self.assertNotIn("-ss", command)

    def test_corrupt_file_remains_visible_and_cli_exits_one(self):
        bad = self.media("bad.MOV")
        self.media("good.mp4")
        with self.fake_tools(bad_probe={"bad.MOV"}):
            code, summary = self.invoke(["--assets", str(self.source), "--out", str(self.output)])
        self.assertEqual(code, 1)
        self.assertEqual(summary["errors"], 1)
        self.assertEqual(summary["first_error"]["filename"], "bad.MOV")
        self.assertNotIn("credential", json.dumps(summary))
        self.assertNotIn("frames", summary)
        inventory = json.loads((self.output / "inventory.json").read_text())
        self.assertEqual(len(inventory["assets"]), 2)
        asset = inventory["assets"][0]
        self.assertEqual(asset["path"], str(bad))
        self.assertIsNone(asset["has_audio"])
        self.assertEqual(asset["frames"], [])
        self.assertEqual(inventory["errors"][0]["asset_id"], asset["id"])
        self.assertEqual(inventory["errors"][0]["stage"], "probe")

    def test_thumbnail_failure_retains_metadata(self):
        self.media()
        with self.fake_tools(bad_thumbnail=True):
            inventory, _ = self.scan()
        self.assertEqual(inventory["assets"][0]["duration"], 10)
        self.assertEqual(inventory["assets"][0]["frames"], [])
        self.assertEqual(len(inventory["errors"]), 3)
        self.assertEqual(inventory["errors"][0]["stage"], "thumbnail")
        self.assertNotIn("private token", json.dumps(inventory))

    def test_success_exit_without_actual_frame_is_an_error(self):
        self.media()
        with self.fake_tools(no_frame=True):
            inventory, _ = self.scan(frames=1)
        self.assertEqual(len(inventory["errors"]), 1)
        self.assertIn("no thumbnail", inventory["errors"][0]["reason"])

    def test_invalid_probe_json(self):
        self.media()
        result = subprocess.CompletedProcess([], 0, "not json", "")
        with mock.patch.object(vlog_scan.subprocess, "run", return_value=result):
            inventory, _ = self.scan()
        self.assertEqual(len(inventory["assets"]), 1)
        self.assertIn("invalid JSON", inventory["errors"][0]["reason"])

    def test_missing_tools_and_timeout_have_no_traceback(self):
        self.media()
        for failure in (FileNotFoundError(), subprocess.TimeoutExpired("ffprobe", 120)):
            with self.subTest(failure=type(failure).__name__):
                out = self.root / type(failure).__name__
                with mock.patch.object(vlog_scan.subprocess, "run", side_effect=failure):
                    code, summary = self.invoke(["--assets", str(self.source), "--out", str(out)])
                self.assertEqual(code, 1)
                self.assertEqual(summary["first_error"]["filename"], "clip.MOV")
                self.assertIn("ffprobe", summary["first_error"]["reason"])

    def test_invalid_dimensions_duration_and_missing_video_are_errors(self):
        path = self.media()
        fixtures = [
            {"streams": []}, {"streams": [{"codec_type": "audio"}]},
            probe_data(duration="NaN"), probe_data(duration="0"),
            probe_data(duration="Infinity"), probe_data(duration="N/A"),
        ]
        for value in (0, None, "NaN", "bad", -1):
            data = probe_data()
            data["streams"][0]["width"] = value
            fixtures.append(data)
        for data in fixtures:
            with self.subTest(data=data):
                with self.fake_tools(data):
                    with self.assertRaises(vlog_scan.ScanError):
                        vlog_scan.probe(path, "video")

    def test_default_direct_files_only(self):
        direct = self.media("direct.mp4")
        self.media("nested.mp4", self.source / "nested")
        with self.fake_tools():
            inventory, _ = self.scan()
        self.assertEqual([asset["path"] for asset in inventory["assets"]], [str(direct)])

    def test_recursive_hidden_generated_output_and_symlinks_excluded(self):
        direct = self.media("direct.mp4")
        nested = self.media("nested.WEBM", self.source / "normal")
        self.media(".hidden.mp4")
        self.media("hidden.mp4", self.source / ".hidden")
        for dirname in ("素材检视", "剪辑过程", "发布包", "mograph-task", "mograph-task-old", "outputs", "frames"):
            self.media("generated.mp4", self.source / dirname)
        self.output = self.source / "my-independent-review"
        generated = self.media("earlier-render.mp4", self.output)
        external = self.media("outside.mp4", self.root / "external")
        (self.source / "linked.mp4").symlink_to(external)
        (self.source / "linked-dir").symlink_to(external.parent, target_is_directory=True)
        (self.source / "broken.mp4").symlink_to(self.root / "missing")
        with self.fake_tools():
            inventory, _ = self.scan(recursive=True, frames=1)
        self.assertEqual([asset["path"] for asset in inventory["assets"]], [str(direct), str(nested)])
        self.assertEqual(inventory["errors"], [])
        self.assertEqual(generated.read_bytes(), b"original fixture, never modified")
        self.assertEqual(external.read_bytes(), b"original fixture, never modified")

    def test_generated_mograph_task_prefix_exclusion(self):
        self.media("old.mp4", self.source / "MOGRAPH-TASK-preview")
        keep = self.media("ok.mkv", self.source / "mograph-project")
        errors = []
        self.assertEqual(vlog_scan.discover(self.source, self.output, True, errors), [keep])

    def test_reject_assets_root_ancestor_and_file_outputs_without_tools(self):
        source_file = self.media()
        for out in (self.source, self.root, source_file):
            with self.subTest(out=out), mock.patch.object(vlog_scan.subprocess, "run") as run:
                code, summary = self.invoke(["--assets", str(self.source), "--out", str(out)])
                self.assertEqual(code, 1)
                self.assertTrue(summary["reason"])
                run.assert_not_called()
        self.assertEqual(source_file.read_bytes(), b"original fixture, never modified")

    def test_reject_symlink_roots_outputs_and_ancestor_links(self):
        self.media()
        linked_source = self.root / "source-link"
        linked_source.symlink_to(self.source, target_is_directory=True)
        linked_parent = self.root / "parent-link"
        linked_parent.symlink_to(self.root, target_is_directory=True)
        real_out = self.root / "existing-output"
        real_out.mkdir()
        linked_out = self.root / "out-link"
        linked_out.symlink_to(real_out, target_is_directory=True)
        for source, out in (
            (linked_source, self.output), (self.source, linked_out),
            (self.source, linked_parent / "new-output"),
            (linked_parent / ".." / self.root.name / self.source.name, self.output),
        ):
            with self.subTest(source=source, out=out):
                with self.assertRaises(vlog_scan.ScanError):
                    vlog_scan.scan(source, out)
        self.assertFalse(self.output.exists())
        self.assertEqual(list(real_out.iterdir()), [])

    def test_existing_inventory_frames_and_hardlink_collisions_are_not_overwritten(self):
        original = self.media()
        self.output.mkdir()
        collision = self.output / "inventory.json"
        collision.hardlink_to(original)
        with self.assertRaises(vlog_scan.ScanError):
            self.scan()
        self.assertEqual(original.read_bytes(), b"original fixture, never modified")
        collision.unlink()
        for name in ("frames", "contact_sheet.jpg"):
            target = self.output / name
            target.symlink_to(original)
            with self.subTest(name=name), self.assertRaises(vlog_scan.ScanError):
                self.scan()
            target.unlink()

    def test_second_scan_refuses_to_overwrite_previous_output(self):
        self.media()
        with self.fake_tools():
            _, path = self.scan(frames=1)
        first = path.read_bytes()
        with mock.patch.object(vlog_scan.subprocess, "run") as run:
            with self.assertRaises(vlog_scan.ScanError):
                self.scan()
            run.assert_not_called()
        self.assertEqual(path.read_bytes(), first)

    def test_disappeared_or_replaced_source_remains_an_error_asset(self):
        path = self.media()
        with mock.patch.object(vlog_scan, "check_source", side_effect=FileNotFoundError()):
            inventory, _ = self.scan()
        self.assertEqual(inventory["assets"][0]["path"], str(path))
        self.assertEqual(inventory["errors"][0]["filename"], path.name)
        external = self.media("external.mp4", self.root / "external")
        path.unlink()
        path.symlink_to(external)
        with self.assertRaises(vlog_scan.ScanError):
            vlog_scan.check_source(path, self.source)

    def test_directory_listing_failure_recorded(self):
        self.media()
        with mock.patch.object(vlog_scan.os, "scandir", side_effect=PermissionError()):
            inventory, _ = self.scan()
        self.assertEqual(inventory["assets"], [])
        self.assertEqual(inventory["errors"][0]["stage"], "scan")
        self.assertEqual(inventory["errors"][0]["filename"], self.source.name)

    def test_empty_directory_is_valid_without_tools(self):
        with mock.patch.object(vlog_scan.subprocess, "run") as run:
            inventory, _ = self.scan()
            run.assert_not_called()
        self.assertEqual(inventory["assets"], [])
        self.assertEqual(inventory["errors"], [])
        self.assertIsNone(inventory["contact_sheet"])

    def test_missing_source_fails_before_output_creation(self):
        code, summary = self.invoke(["--assets", str(self.root / "missing"), "--out", str(self.output)])
        self.assertEqual(code, 1)
        self.assertIn("missing", summary["reason"])
        self.assertFalse(self.output.exists())

    def test_cli_required_arguments_and_frame_range(self):
        for argv in (
            [], ["--assets", str(self.source)], ["--out", str(self.output)],
            *[["--assets", str(self.source), "--out", str(self.output), "--frames", value]
              for value in ("0", "6", "-1", "not-an-int", "2.5")],
        ):
            with self.subTest(argv=argv):
                code, summary = self.invoke(argv)
                self.assertEqual(code, 1)
                self.assertFalse(summary["ok"])
                self.assertFalse(self.output.exists())

    def test_frame_counts_one_through_five(self):
        self.media()
        for count in range(1, 6):
            with self.subTest(count=count):
                out = self.root / ("review-" + str(count))
                with self.fake_tools():
                    inventory, _ = vlog_scan.scan(self.source, out, frames=count)
                times = [frame["time"] for frame in inventory["assets"][0]["frames"]]
                self.assertEqual(len(times), count)
                self.assertTrue(all(0 < time < 10 for time in times))
                if count == 1:
                    self.assertEqual(times, [5])
                elif count > 2:
                    gaps = [b - a for a, b in zip(times, times[1:])]
                    self.assertTrue(all(abs(gap - gaps[0]) < 1e-8 for gap in gaps))

    def test_cli_recursive_and_frames_options(self):
        self.media("nested.mp4", self.source / "nested")
        with self.fake_tools():
            code, summary = self.invoke([
                "--assets", str(self.source), "--out", str(self.output),
                "--recursive", "--frames", "5",
            ])
        self.assertEqual(code, 0)
        self.assertEqual(summary["videos"], 1)
        self.assertEqual(len(self.calls), 6)

    def test_no_pillow_returns_single_frame_list(self):
        with mock.patch.dict(sys.modules, {"PIL": None}):
            self.assertIsNone(self.real_load_pillow())
        self.media("photo.jpg")
        with self.fake_tools(probe_data(image=True)):
            inventory, _ = self.scan()
        self.assertIsNone(inventory["contact_sheet"])
        self.assertEqual(len(inventory["assets"][0]["frames"]), 1)

    def test_optional_contact_sheet_has_ascii_filename_and_time_labels(self):
        self.media("中文随拍.mp4")
        with self.fake_tools():
            inventory, _ = self.scan(frames=1)
        Image, ImageDraw = mock.MagicMock(), mock.MagicMock()
        sheet = Image.new.return_value
        sheet.save.side_effect = lambda file, **kwargs: file.write(b"mock contact sheet")
        image = Image.open.return_value.__enter__.return_value.convert.return_value
        image.width, image.height = 100, 100
        with mock.patch.object(vlog_scan, "load_pillow", return_value=(Image, ImageDraw)):
            path = vlog_scan.make_contact_sheet(inventory["assets"], self.output)
        self.assertEqual(path, str(self.output / "contact_sheet.jpg"))
        self.assertTrue(Path(path).is_file())
        labels = [call.args[1] for call in ImageDraw.Draw.return_value.text.call_args_list]
        self.assertTrue(all(label.isascii() for label in labels))
        self.assertIn("m001", labels[0])
        self.assertIn("Time: 5.000s", labels[1])
        sheet.close.assert_called_once()

    def test_contact_sheet_failure_does_not_discard_frames(self):
        self.media()
        with self.fake_tools(), mock.patch.object(vlog_scan, "make_contact_sheet", side_effect=OSError("private diagnostic")):
            inventory, _ = self.scan(frames=1)
        self.assertEqual(len(inventory["assets"][0]["frames"]), 1)
        self.assertEqual(inventory["errors"][0]["stage"], "contact_sheet")
        self.assertNotIn("private diagnostic", json.dumps(inventory))

    def test_unexpected_io_error_is_json_not_traceback(self):
        with mock.patch.object(vlog_scan, "scan", side_effect=PermissionError(13, "private", str(self.output / "inventory.json"))):
            code, summary = self.invoke(["--assets", str(self.source), "--out", str(self.output)])
        self.assertEqual(code, 1)
        self.assertEqual(summary["filename"], "inventory.json")
        self.assertNotIn("private", json.dumps(summary))


if __name__ == "__main__":
    unittest.main()
