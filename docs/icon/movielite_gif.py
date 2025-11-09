import numpy as np
import os
import random
from movielite import VideoWriter, TextClip, ImageClip, AlphaVideoClip
from pictex import Canvas, Shadow

WIDTH, HEIGHT = 1200, 250
FPS = 30
DURATION = 5.0
VIDEO_FILENAME = "movielite.mp4"
GIF_FILENAME = "movielite.gif"
FONT_FILE = "FingerPaint-Regular.ttf"
FONT_SIZE = 100
COLORS = ["#42a5f5", "#66bb6a", "#ffa726", "#ef5350", "#ab47bc"]

if __name__ == "__main__":
    writer = VideoWriter(VIDEO_FILENAME, fps=FPS, size=(WIDTH, HEIGHT), duration=DURATION)
    clips = []
    bg_base = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    bg_base[:, :] = [15, 15, 25]
    background = ImageClip(bg_base, duration=DURATION)
    clips.append(background)
    num_particles = 80
    for i in range(num_particles):
        size = random.randint(1, 4)
        start_x = random.randint(0, WIDTH)
        start_y = random.randint(0, HEIGHT)
        speed = random.uniform(20, 60)
        start_time_offset = random.uniform(0, DURATION)
        particle = ImageClip.from_color((255, 255, 255), (size, size), duration=DURATION)
        particle.set_opacity(random.uniform(0.1, 0.5))
        particle.set_position(
            lambda t, sx=start_x, sy=start_y, spd=speed, sto=start_time_offset: (
                int(sx),
                int((sy - (t + sto) * spd) % (HEIGHT + size)) - size
            )
        )
        clips.append(particle)
    word = "MovieLite"
    letter_clips = []
    total_text_width = 0
    for i, letter in enumerate(word):
        color = COLORS[i % len(COLORS)]
        canvas = (
            Canvas()
            .font_family(FONT_FILE)
            .font_size(FONT_SIZE)
            .color(color)
            .background_color("transparent")
            .padding(20)
            .text_shadows(Shadow(offset=(0, 0), blur_radius=10, color=color))
        )
        clip = TextClip(letter, canvas=canvas, duration=DURATION)
        letter_clips.append(clip)
        total_text_width += clip.size[0]
    start_x = (WIDTH - total_text_width) / 2
    current_x = start_x
    for i, clip in enumerate(letter_clips):
        color = COLORS[i % len(COLORS)]
        final_x = current_x
        final_y = (HEIGHT - clip.size[1]) / 2
        clip.set_position((final_x, final_y))
        phase = i * (np.pi / len(word))
        clip.set_scale(lambda t, p=phase: 1.0 + 0.03 * np.sin(2 * np.pi * t / DURATION + p))
        clip.set_opacity(lambda t, p=phase: 0.8 + 0.2 * np.sin(2 * np.pi * t / DURATION + p))
        clips.append(clip)
        current_x += clip.size[0]
        if i == len(word) - 1:
            last_letter_center = (final_x + clip.size[0]/2, final_y + clip.size[1]/2)
  
    writer.add_clips(clips)
    writer.write()
    for clip in clips:
        clip.close()

    # NOTE: here we use ffmpeg to do the convertion from the mp4 generated to the gif
    #  This is because movielite only support rendering .mp4 files for now.
    os.system(f'ffmpeg -y -i {VIDEO_FILENAME} -vf "fps=30,scale=800:-1:flags=lanczos,split[s0][s1];[s0]palettegen=stats_mode=full[p];[s1][p]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle" -loop 0 {GIF_FILENAME}')
