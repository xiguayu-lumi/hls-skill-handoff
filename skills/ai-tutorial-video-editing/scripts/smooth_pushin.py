"""Render a silent image push-in with float sampling. Requires Pillow and FFmpeg."""
import argparse
import math
from pathlib import Path
import subprocess
from PIL import Image, ImageOps


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('image', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--duration', type=float, default=5)
    p.add_argument('--ramp', type=float, default=3)
    p.add_argument('--zoom', type=float, default=2.5)
    p.add_argument('--width', type=int, default=1080)
    p.add_argument('--height', type=int, default=1920)
    p.add_argument('--fps', type=int, default=30)
    a = p.parse_args()
    if a.image.resolve() == a.output.resolve():
        p.error('Output must not overwrite input')
    if (a.duration <= 0 or a.ramp <= 0 or a.zoom < 1 or a.fps <= 0
            or min(a.width, a.height) < 2 or a.width % 2 or a.height % 2):
        p.error('Use positive times/fps, zoom >= 1 and positive even dimensions')
    frames = round(a.duration * a.fps)
    if frames < 2:
        p.error('At least two frames are required')
    with Image.open(a.image) as src:
        base = ImageOps.exif_transpose(src).convert('RGB')
    bw, bh = base.size
    # Fit by center crop; affine matrix maps destination to source coordinates.
    scale = min(bw / a.width, bh / a.height)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'rawvideo',
           '-pix_fmt', 'rgb24', '-s', f'{a.width}x{a.height}', '-r', str(a.fps),
           '-i', '-', '-an', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18',
           '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(a.output)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for i in range(frames):
            t = min(1., (i / a.fps) / min(a.ramp, (frames - 1) / a.fps))
            z = 1 + (a.zoom - 1) * (1 - math.cos(math.pi * t)) / 2
            s = scale / z
            matrix = (s, 0, (bw - a.width * s) / 2,
                      0, s, (bh - a.height * s) / 2)
            frame = base.transform((a.width, a.height), Image.Transform.AFFINE,
                                   matrix, resample=Image.Resampling.BICUBIC)
            proc.stdin.write(frame.tobytes())
        proc.stdin.close()
        if proc.wait() != 0:
            raise RuntimeError('FFmpeg failed')
    except BaseException:
        proc.kill()
        proc.wait()
        raise
    print(f'Rendered {frames} frames')


if __name__ == '__main__':
    main()
