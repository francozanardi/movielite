"""
Performance comparison between movielite and moviepy.

This script compares movielite against moviepy 1.0.3 (classic version) on common video editing tasks.
Results are saved to benchmark_results.json with visual outputs for comparison.

Usage:
    python compare_moviepy_v1.py --input <input_dir>

The input directory should contain:
    - video.mp4 (main test video)
    - image1.png, image2.png, image3.png (test images)
    - overlay_video.mp4 (video for overlay tests)
    - alpha_video.mp4 (transparent video for alpha overlay)
"""

import time
import json
import os
import argparse
from pathlib import Path
import movielite as ml
from moviepy.editor import (
    VideoFileClip, ImageClip, TextClip,
    CompositeVideoClip, concatenate_videoclips
)
from moviepy.video.fx.all import fadein, fadeout, resize, loop
from pictex import Canvas


def benchmark_task(name: str, func, *args, **kwargs):
    """Benchmark a single task and return execution time."""
    print(f"Running: {name}...", end=" ", flush=True)
    start = time.time()
    try:
        func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"✓ {elapsed:.2f}s")
        return {"success": True, "time": elapsed, "error": None}
    except Exception as e:
        elapsed = time.time() - start
        print(f"✗ FAILED ({elapsed:.2f}s): {e}")
        return {"success": False, "time": elapsed, "error": str(e)}


# ===================== Test 1: No Processing =====================
def test_no_processing_movielite(input_path: str, output_path: str):
    """Process video without any changes using movielite."""
    clip = ml.VideoClip(input_path)

    writer = ml.VideoWriter(output_path, fps=clip.fps)
    writer.add_clip(clip)
    writer.write()

    clip.close()


def test_no_processing_moviepy(input_path: str, output_path: str):
    """Process video without any changes using moviepy."""
    clip = VideoFileClip(input_path)
    clip.write_videofile(
        output_path,
        preset="veryfast",
        ffmpeg_params=["-crf", "21"],
        codec='libx264',
        audio_codec='aac'
    )

    clip.close()

# ===================== Test 2: Video with Zoom =====================
def test_video_zoom_movielite(input_path: str, output_path: str):
    """Apply zoom effect using movielite."""
    clip = ml.VideoClip(input_path)

    # Zoom from 1.0 to 1.5x over the video duration
    def zoom_scale(t):
        progress = min(t / clip.duration, 1.0)
        return 1.0 + 0.5 * progress

    clip.set_scale(zoom_scale)

    writer = ml.VideoWriter(output_path, fps=clip.fps, size=clip.size)
    writer.add_clip(clip)
    writer.write()

    clip.close()


def test_video_zoom_moviepy(input_path: str, output_path: str):
    """Apply zoom effect using moviepy."""
    clip = VideoFileClip(input_path)

    # Zoom from 1.0 to 1.5x over the video duration
    def zoom_scale(t):
        progress = min(t / clip.duration, 1.0)
        return 1.0 + 0.5 * progress

    clip = clip.resize(zoom_scale)
    clip.write_videofile(
        output_path,
        preset="veryfast",
        ffmpeg_params=["-crf", "21"],
        codec='libx264',
        audio_codec='aac'
    )

    clip.close()


# ===================== Test 3: Fade In/Out =====================
def test_fade_movielite(input_path: str, output_path: str):
    """Apply fade in/out effects using movielite."""
    clip = ml.VideoClip(input_path)
    clip.add_effect(ml.vfx.FadeIn(1.0)).add_effect(ml.vfx.FadeOut(1.0))

    writer = ml.VideoWriter(output_path, fps=clip.fps)
    writer.add_clip(clip)
    writer.write()

    clip.close()


def test_fade_moviepy(input_path: str, output_path: str):
    """Apply fade in/out effects using moviepy."""
    clip = VideoFileClip(input_path)
    clip = clip.fx(fadein, 1).fx(fadeout, 1)
    clip.write_videofile(
        output_path,
        preset="veryfast",
        ffmpeg_params=["-crf", "21"],
        codec='libx264',
        audio_codec='aac'
    )

    clip.close()


# ===================== Test 4: Text Overlay =====================
def test_text_overlay_movielite(input_path: str, output_path: str):
    """Add text overlay using movielite."""
    video = ml.VideoClip(input_path)

    canvas = Canvas().font_size("Arial").font_size(60).color("white")
    text = ml.TextClip("hello world", start=0, duration=video.duration, canvas=canvas)
    text.set_position((video.size[0] // 2 - text.size[0] // 2, 100))

    writer = ml.VideoWriter(output_path, fps=video.fps, size=video.size)
    writer.add_clips([video, text])
    writer.write()

    video.close()


def test_text_overlay_moviepy(input_path: str, output_path: str):
    """Add text overlay using moviepy."""
    video = VideoFileClip(input_path)

    text = TextClip("hello world", fontsize=60, color='white', font='Arial')
    text = text.set_duration(video.duration).set_position(('center', 100))

    final = CompositeVideoClip([video, text])
    final.write_videofile(
        output_path,
        preset="veryfast",
        ffmpeg_params=["-crf", "21"],
        codec='libx264',
        audio_codec='aac'
    )

    video.close()
    final.close()


# ===================== Test 5: Video Overlay =====================
def test_video_overlay_movielite(main_video: str, overlay_video: str, output_path: str):
    """Overlay one video on top of another using movielite."""
    main = ml.VideoClip(main_video)
    overlay = ml.VideoClip(overlay_video, duration=main.duration)
    overlay.set_opacity(0.3)
    overlay.set_size(main.size[0], main.size[1])
    overlay.loop(True)

    writer = ml.VideoWriter(output_path, fps=main.fps, size=main.size, duration=main.duration)
    writer.add_clips([main, overlay])
    writer.write()

    main.close()
    overlay.close()


def test_video_overlay_moviepy(main_video: str, overlay_video: str, output_path: str):
    """Overlay one video on top of another using moviepy."""
    main = VideoFileClip(main_video)
    overlay = VideoFileClip(overlay_video)
    overlay = overlay.set_opacity(0.3)
    overlay = overlay.resize(main.size)
    overlay = overlay.fx(loop, duration=main.duration)
    overlay = overlay.set_duration(main.duration)

    final = CompositeVideoClip([main, overlay])
    final.write_videofile(
        output_path,
        preset="veryfast",
        ffmpeg_params=["-crf", "21"],
        codec='libx264',
        audio_codec='aac'
    )

    main.close()
    overlay.close()
    final.close()


# ===================== Test 6: Alpha Video Overlay =====================
def test_alpha_overlay_movielite(main_video: str, alpha_video: str, output_path: str):
    """Overlay transparent video using movielite."""
    main = ml.VideoClip(main_video)
    alpha = ml.AlphaVideoClip(alpha_video)

    # Center the alpha video
    alpha.set_position(
        ((main.size[0] - alpha.size[0]) // 2, (main.size[1] - alpha.size[1]) // 2)
    )
    alpha.set_duration(main.duration)
    alpha.loop(True)

    writer = ml.VideoWriter(output_path, fps=main.fps, size=main.size)
    writer.add_clips([main, alpha])
    writer.write()

    main.close()
    alpha.close()


def test_alpha_overlay_moviepy(main_video: str, alpha_video: str, output_path: str):
    """Overlay transparent video using moviepy."""
    main = VideoFileClip(main_video)
    alpha = VideoFileClip(alpha_video, has_mask=True)

    # Center the alpha video
    alpha = alpha.set_position('center')
    alpha = alpha.fx(loop, duration=main.duration)
    alpha = alpha.set_duration(main.duration)

    final = CompositeVideoClip([main, alpha])
    final.write_videofile(
        output_path,
        preset="veryfast",
        ffmpeg_params=["-crf", "21"],
        codec='libx264',
        audio_codec='aac'
    )

    main.close()
    alpha.close()
    final.close()


# ===================== Test 7: Complex Mix =====================
def test_complex_mix_movielite(
    video_path: str,
    img1: str,
    img2: str,
    img3: str,
    overlay_video: str,
    output_path: str
):
    """Complex test: videos + images + text + overlay + zoom + fade."""
    # Main video with zoom and fade
    main_video = ml.VideoClip(video_path)

    # Zoom effect
    def zoom_scale(t):
        progress = min(t / main_video.duration, 1.0)
        return 1.0 + 0.3 * progress

    main_video.set_scale(zoom_scale)
    main_video.add_effect(ml.vfx.FadeIn(1.0)).add_effect(ml.vfx.FadeOut(1.0))

    # Image clips with durations
    img_duration = 5
    img_clip1 = ml.ImageClip(img1, start=main_video.end, duration=img_duration)
    img_clip2 = ml.ImageClip(img2, start=img_clip1.end, duration=img_duration)
    img_clip3 = ml.ImageClip(img3, start=img_clip2.end, duration=img_duration)

    # Add fade to images
    img_clip1.add_effect(ml.vfx.FadeIn(1.5))
    img_clip2.add_effect(ml.vfx.FadeIn(1.5))
    img_clip3.add_effect(ml.vfx.FadeIn(1.5))

    # Text overlay
    canvas = Canvas().font_family("Arial").font_size(80).color("yellow")
    text = ml.TextClip(
        "MovieLite Demo",
        start=0,
        duration=img_clip3.end,
        canvas=canvas
    )
    text.set_position((main_video.size[0] // 2 - text.size[0] // 2, 50))

    # Video overlay
    overlay = ml.VideoClip(overlay_video, duration=img_clip3.end)
    overlay.set_opacity(0.3)
    overlay.set_size(main_video.size[0], main_video.size[1])
    overlay.loop(True)

    writer = ml.VideoWriter(
        output_path,
        fps=main_video.fps,
        size=main_video.size,
    )
    writer.add_clips([main_video, img_clip1, img_clip2, img_clip3, overlay, text])
    writer.write()

    main_video.close()
    overlay.close()


def test_complex_mix_moviepy(
    video_path: str,
    img1: str,
    img2: str,
    img3: str,
    overlay_video: str,
    output_path: str
):
    """Complex test: videos + images + text + overlay + zoom + fade."""
    # Main video with zoom and fade
    main_video = VideoFileClip(video_path)

    # Zoom effect
    def zoom_scale(t):
        progress = min(t / main_video.duration, 1.0)
        return 1.0 + 0.3 * progress

    main_video = main_video.resize(zoom_scale)
    main_video = main_video.fx(fadein, 1).fx(fadeout, 1)

    # Image clips with durations
    img_duration = 5
    img_clip1 = ImageClip(img1).set_duration(img_duration).fx(fadein, 1.5)
    img_clip2 = ImageClip(img2).set_duration(img_duration).fx(fadein, 1.5)
    img_clip3 = ImageClip(img3).set_duration(img_duration).fx(fadein, 1.5)

    # Concatenate main video with images
    main_sequence = concatenate_videoclips([main_video, img_clip1, img_clip2, img_clip3])

    # Text overlay
    text = TextClip("MoviePy Demo", fontsize=80, color='yellow', font='Arial')
    text = text.set_duration(main_sequence.duration).set_position(('center', 50))

    # Video overlay
    overlay = VideoFileClip(overlay_video)
    overlay = overlay.set_opacity(0.3)
    overlay = overlay.resize(main_video.size)
    overlay = overlay.fx(loop, duration=main_sequence.duration)
    overlay = overlay.set_start(0)
    overlay = overlay.set_duration(main_sequence.duration)

    final = CompositeVideoClip([main_sequence, overlay, text])
    final.write_videofile(
        output_path,
        preset="veryfast",
        ffmpeg_params=["-crf", "21"],
        codec='libx264',
        audio_codec='aac'
    )

    main_video.close()
    overlay.close()
    final.close()


def run_benchmarks(input_dir: str, output_dir: str):
    """Run all benchmarks and save results."""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Input files
    video = str(input_path / "video.mp4")
    img1 = str(input_path / "image1.png")
    img2 = str(input_path / "image2.png")
    img3 = str(input_path / "image3.png")
    overlay_video = str(input_path / "overlay_video.mp4")
    alpha_video = str(input_path / "alpha_video.mov")

    # Verify input files exist
    required_files = [video, img1, img2, img3, overlay_video, alpha_video]
    missing_files = [f for f in required_files if not os.path.exists(f)]

    if missing_files:
        print("ERROR: Missing required input files:")
        for f in missing_files:
            print(f"  - {f}")
        print("\nRequired files:")
        print("  - video.mp4 (main test video)")
        print("  - image1.png, image2.png, image3.png (test images)")
        print("  - overlay_video.mp4 (video for overlay tests)")
        print("  - alpha_video.mov (transparent video for alpha overlay)")
        return

    results = {}

    # Test 1: No Processing
    print("\n" + "="*60)
    print("Test 1: Process video without any changes")
    print("="*60)
    results["no_processing"] = {
        "movielite": benchmark_task(
            "movielite - no processing",
            test_no_processing_movielite,
            video,
            str(output_path / "out_ml_no_processing.mp4")
        ),
        "moviepy": benchmark_task(
            "moviepy - no processing",
            test_no_processing_moviepy,
            video,
            str(output_path / "out_mp_no_processing.mp4")
        )
    }

    # Test 2: Video with Zoom
    print("\n" + "="*60)
    print("Test 2: Apply zoom effect to video")
    print("="*60)
    results["video_zoom"] = {
        "movielite": benchmark_task(
            "movielite - video zoom",
            test_video_zoom_movielite,
            video,
            str(output_path / "out_ml_zoom.mp4")
        ),
        "moviepy": benchmark_task(
            "moviepy - video zoom",
            test_video_zoom_moviepy,
            video,
            str(output_path / "out_mp_zoom.mp4")
        )
    }

    # Test 3: Fade In/Out
    print("\n" + "="*60)
    print("Test 3: Apply fade in/out effects")
    print("="*60)
    results["fade"] = {
        "movielite": benchmark_task(
            "movielite - fade",
            test_fade_movielite,
            video,
            str(output_path / "out_ml_fade.mp4")
        ),
        "moviepy": benchmark_task(
            "moviepy - fade",
            test_fade_moviepy,
            video,
            str(output_path / "out_mp_fade.mp4")
        )
    }

    # Test 4: Text Overlay
    print("\n" + "="*60)
    print("Test 4: Add text overlay")
    print("="*60)
    results["text_overlay"] = {
        "movielite": benchmark_task(
            "movielite - text overlay",
            test_text_overlay_movielite,
            video,
            str(output_path / "out_ml_text.mp4")
        ),
        "moviepy": benchmark_task(
            "moviepy - text overlay",
            test_text_overlay_moviepy,
            video,
            str(output_path / "out_mp_text.mp4")
        )
    }

    # Test 5: Video Overlay
    print("\n" + "="*60)
    print("Test 5: Overlay video on top of another")
    print("="*60)
    results["video_overlay"] = {
        "movielite": benchmark_task(
            "movielite - video overlay",
            test_video_overlay_movielite,
            video, overlay_video,
            str(output_path / "out_ml_video_overlay.mp4")
        ),
        "moviepy": benchmark_task(
            "moviepy - video overlay",
            test_video_overlay_moviepy,
            video, overlay_video,
            str(output_path / "out_mp_video_overlay.mp4")
        )
    }

    # Test 6: Alpha Video Overlay
    print("\n" + "="*60)
    print("Test 6: Overlay transparent video")
    print("="*60)
    results["alpha_overlay"] = {
        "movielite": benchmark_task(
            "movielite - alpha overlay",
            test_alpha_overlay_movielite,
            video, alpha_video,
            str(output_path / "out_ml_alpha.mp4")
        ),
        "moviepy": benchmark_task(
            "moviepy - alpha overlay",
            test_alpha_overlay_moviepy,
            video, alpha_video,
            str(output_path / "out_mp_alpha.mp4")
        )
    }

    # Test 7: Complex Mix
    print("\n" + "="*60)
    print("Test 7: Complex mix (videos + images + text + overlay + zoom + fade)")
    print("="*60)
    results["complex_mix"] = {
        "movielite": benchmark_task(
            "movielite - complex mix",
            test_complex_mix_movielite,
            video, img1, img2, img3, overlay_video,
            str(output_path / "out_ml_complex.mp4")
        ),
        "moviepy": benchmark_task(
            "moviepy - complex mix",
            test_complex_mix_moviepy,
            video, img1, img2, img3, overlay_video,
            str(output_path / "out_mp_complex.mp4")
        )
    }

    # Calculate speedups and display summary
    print("\n" + "="*60)
    print("PERFORMANCE SUMMARY")
    print("="*60)

    total_ml_time = 0
    total_mp_time = 0

    for test_name, test_results in results.items():
        ml = test_results["movielite"]
        mp = test_results["moviepy"]

        if ml["success"] and mp["success"]:
            speedup = mp["time"] / ml["time"]
            print(f"\n{test_name.replace('_', ' ').title()}:")
            print(f"  movielite: {ml['time']:>8.2f}s")
            print(f"  moviepy:   {mp['time']:>8.2f}s")
            print(f"  speedup:   {speedup:>8.2f}x {'🚀' if speedup > 1 else '⚠️'}")
            results[test_name]["speedup"] = speedup

            total_ml_time += ml["time"]
            total_mp_time += mp["time"]
        else:
            print(f"\n{test_name.replace('_', ' ').title()}: ⚠️ One or both tests failed")
            if not ml["success"]:
                print(f"  movielite error: {ml['error']}")
            if not mp["success"]:
                print(f"  moviepy error: {mp['error']}")

    if total_ml_time > 0 and total_mp_time > 0:
        overall_speedup = total_mp_time / total_ml_time
        print("\n" + "="*60)
        print(f"TOTAL TIME:")
        print(f"  movielite: {total_ml_time:>8.2f}s")
        print(f"  moviepy:   {total_mp_time:>8.2f}s")
        print(f"  Overall speedup: {overall_speedup:>8.2f}x")
        print("="*60)

    # Save results
    results_file = output_path / "benchmark_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✓ Results saved to {results_file}")
    print(f"✓ Output videos saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark movielite vs moviepy 1.0.3",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Input directory should contain:
  - video.mp4 (main test video)
  - image1.png, image2.png, image3.png (test images)
  - overlay_video.mp4 (video for overlay tests)
  - alpha_video.mov (transparent video for alpha overlay)
        """
    )
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Directory containing input assets'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='output',
        help='Directory for output videos (default: output)'
    )

    args = parser.parse_args()

    run_benchmarks(args.input, args.output)


if __name__ == "__main__":
    main()
