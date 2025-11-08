# MovieLite vs MoviePy Performance Benchmarks

Comprehensive performance comparison between MovieLite and MoviePy on common video editing tasks.

## Setup

### 1. Install Dependencies

```bash
pip install moviepy
pip install movielite  # or install locally: pip install -e .
```

### 2. Prepare Input Assets

Create a directory with the following files:

```
input/
├── video.mp4           # Main test video (any resolution, recommended: 1920x1080)
├── image1.png          # Test image 1
├── image2.png          # Test image 2
├── image3.png          # Test image 3
├── overlay_video.mp4   # Video for overlay tests (can be same as video.mp4)
└── alpha_video.mp4     # Transparent video (video with alpha channel)
```

#### Creating a transparent video (alpha_video.mp4)

You can create a simple transparent video with text using ffmpeg:

```bash
ffmpeg -f lavfi -i color=c=black@0:s=640x480:d=5 -vf \
  "drawtext=text='TRANSPARENT':fontsize=60:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2" \
  -c:v libvpx-vp9 -pix_fmt yuva420p input/alpha_video.mp4
```

Or use any video with transparency (green screen keyed out, etc.).

## Running the Benchmarks

```bash
cd benchmarks
python compare_moviepy.py --input /path/to/input --output ./output
```

### Options

- `--input`: Directory containing input assets (required)
- `--output`: Directory for output videos (default: `output`)

## Test Cases

### 1. **No Processing**
Process a video without any changes - baseline performance test.

### 2. **Process Images**
Create a video from 3 static images (3 seconds each).

### 3. **Video with Zoom**
Apply a progressive zoom effect (1.0x to 1.5x) over the video duration.

### 4. **Fade In/Out**
Apply fade in (1s) and fade out (1s) effects.

### 5. **Text Overlay**
Add a text overlay on top of the video.

### 6. **Video Overlay**
Overlay one video on top of another (scaled to 1/4 size, positioned in corner).

### 7. **Alpha Video Overlay**
Overlay a transparent video (with alpha channel) on the main video.

### 8. **Complex Mix**
Combined test with:
- Main video with zoom and fade effects
- 3 image clips with fade in
- Text overlay
- Small video overlay in corner
- All composed into a single output

## Output

The script generates:

1. **Output videos**: Side-by-side comparison (MovieLite vs MoviePy)
   - `out_ml_*.mp4` - MovieLite outputs
   - `out_mp_*.mp4` - MoviePy outputs

2. **benchmark_results.json**: Detailed timing results with speedup calculations

3. **Console output**: Real-time progress and summary statistics

## Example Output

```
============================================================
Test 1: Process video without any changes
============================================================
Running: movielite - no processing... ✓ 12.34s
Running: moviepy - no processing... ✓ 23.45s

============================================================
PERFORMANCE SUMMARY
============================================================

No Processing:
  movielite:    12.34s
  moviepy:      23.45s
  speedup:       1.90x 🚀

...

============================================================
TOTAL TIME:
  movielite:    45.67s
  moviepy:     123.45s
  Overall speedup:  2.70x
============================================================
```

## Notes

- All tests use the same ffmpeg settings for fair comparison:
  - Preset: `veryfast`
  - CRF: `21`
  - Codec: `libx264` (video), `aac` (audio)

- Tests are run sequentially to avoid resource contention

- Output videos allow visual quality comparison between the two libraries

- Speedup > 1.0 means MovieLite is faster
