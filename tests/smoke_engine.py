"""Test du moteur : rendu de chaque format, avec et sans paroles."""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import imageio_ffmpeg  # noqa: E402
import lyricvideo_core as c  # noqa: E402

if __name__ == "__main__":
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                    "sine=frequency=440:duration=5", "test.mp3"], check=True)
    t, a, d, cov = c.read_tags("test.mp3")
    ly = c.lyrics_from_text("[00:01.00]Été à Noël\n[00:03.00]Dernière ligne", d)
    for size in c.RATIOS.values():
        for show in (True, False):
            c.render_video("test.mp3", "test.mp4", t, a, cov, ly, d, size=size, show_lyrics=show)
    print("moteur OK")
