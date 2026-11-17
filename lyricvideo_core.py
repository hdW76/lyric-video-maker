"""Moteur de génération de vidéo de paroles (sans interface).

Pipeline :
  audio -> tags (titre, artiste, pochette) -> paroles (LRCLIB ou texte collé)
  -> images au format choisi (fond pochette flouté + paroles + titre/artiste)
  -> ffmpeg (images + audio -> MP4)
"""
import io
import os
import re
import subprocess
import sys
import json
import urllib.parse
import urllib.request

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

W, H, FPS = 1280, 720, 30
FADE = 0.25  # secondes de fondu entre deux lignes


def resource_path(rel):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)


# --------------------------------------------------------------------- tags
def read_tags(path):
    """Retourne (titre, artiste, durée_s, octets_pochette|None)."""
    from mutagen import File
    title = artist = None
    cover = None
    audio = File(path)
    duration = float(audio.info.length) if audio is not None else 0.0
    tags = audio.tags if audio is not None else None
    if tags is not None:
        def first(key):
            try:
                v = tags[key]
            except Exception:
                return None
            if isinstance(v, list):
                v = v[0] if v else None
            return v
        keys = []
        try:
            keys = list(tags.keys())
        except Exception:
            pass
        # MP3 / WAV / AIFF (ID3)
        for k in keys:
            if str(k).startswith("APIC") and cover is None:
                cover = tags[k].data
        title = first("TIT2") or first("\xa9nam") or first("title") or first("TITLE")
        artist = first("TPE1") or first("\xa9ART") or first("artist") or first("ARTIST")
        title = str(title) if title else None
        artist = str(artist) if artist else None
        # MP4 / M4A
        c = first("covr")
        if c is not None and cover is None:
            cover = bytes(c)
    pics = getattr(audio, "pictures", None)
    if pics and cover is None:
        cover = pics[0].data
    # OGG / Opus : pochette encodée en base64 dans METADATA_BLOCK_PICTURE
    if cover is None and audio is not None and audio.tags is not None:
        try:
            import base64
            from mutagen.flac import Picture
            for b64 in audio.tags.get("metadata_block_picture", []) or []:
                cover = Picture(base64.b64decode(b64)).data
                break
        except Exception:
            pass
    if cover is None:
        cover = extract_cover_ffmpeg(path)
    if not title:
        title = os.path.splitext(os.path.basename(path))[0]
    return title, artist or "", duration, cover


def _valid_image(data):
    try:
        Image.open(io.BytesIO(data)).verify()
        return True
    except Exception:
        return False


def extract_cover_ffmpeg(path):
    """Dernier recours local : laisse ffmpeg extraire l'image intégrée (tous formats)."""
    try:
        import imageio_ffmpeg
        cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-loglevel", "error", "-i", path,
               "-an", "-frames:v", "1", "-f", "image2pipe", "-c:v", "png", "-"]
        flags = 0x08000000 if os.name == "nt" else 0
        r = subprocess.run(cmd, capture_output=True, timeout=30, creationflags=flags)
        if r.returncode == 0 and r.stdout and _valid_image(r.stdout):
            return r.stdout
    except Exception:
        pass
    return None


def fetch_cover_online(title, artist):
    """Cherche la pochette sur Deezer puis iTunes. Retourne des octets d'image ou None."""
    hdr = {"User-Agent": "LyricVideoMaker/1.0"}

    def get(url, as_json=True):
        req = urllib.request.Request(url, headers=hdr)
        with urllib.request.urlopen(req, timeout=15) as r:
            data = r.read()
        return json.loads(data.decode("utf-8")) if as_json else data

    q = f"{artist} {title}".strip()
    try:
        d = get("https://api.deezer.com/search?" + urllib.parse.urlencode({"q": q, "limit": 1}))
        url = d["data"][0]["album"].get("cover_xl") if d.get("data") else None
        if url:
            img = get(url, as_json=False)
            if _valid_image(img):
                return img
    except Exception:
        pass
    try:
        d = get("https://itunes.apple.com/search?" +
                urllib.parse.urlencode({"term": q, "entity": "song", "limit": 1}))
        if d.get("results"):
            url = d["results"][0]["artworkUrl100"].replace("100x100bb", "1000x1000bb")
            img = get(url, as_json=False)
            if _valid_image(img):
                return img
    except Exception:
        pass
    return None


# ------------------------------------------------------------------ paroles
LRC_RE = re.compile(r"\[(\d+):(\d+(?:\.\d+)?)\]")


def parse_lrc(text):
    """Texte LRC -> liste triée [(secondes, ligne)]. Renvoie [] si pas de timestamps."""
    out = []
    for raw in text.splitlines():
        stamps = LRC_RE.findall(raw)
        if not stamps:
            continue
        line = LRC_RE.sub("", raw).strip()
        for m, s in stamps:
            out.append((int(m) * 60 + float(s), line))
    out.sort(key=lambda x: x[0])
    return out


def spread_plain(text, duration):
    """Paroles sans timestamps : répartition régulière (approximative)."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if not lines:
        return []
    start = min(8.0, duration * 0.05)
    end = duration - min(6.0, duration * 0.05)
    step = (end - start) / len(lines)
    return [(start + i * step, l) for i, l in enumerate(lines)]


def lyrics_from_text(text, duration):
    synced = parse_lrc(text)
    return synced if synced else spread_plain(text, duration)


def fetch_lrclib(title, artist, duration):
    """Cherche des paroles synchronisées sur LRCLIB. Retourne du texte LRC ou ''."""
    hdr = {"User-Agent": "LyricVideoMaker/1.0"}

    def get(url):
        req = urllib.request.Request(url, headers=hdr)
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode("utf-8"))

    base = "https://lrclib.net/api/"
    try:
        q = urllib.parse.urlencode({"track_name": title, "artist_name": artist,
                                    "duration": int(round(duration))})
        d = get(base + "get?" + q)
        if d.get("syncedLyrics"):
            return d["syncedLyrics"]
    except Exception:
        pass
    try:
        q = urllib.parse.urlencode({"track_name": title, "artist_name": artist})
        res = get(base + "search?" + q)
        res = [r for r in res if r.get("syncedLyrics")]
        if res:
            res.sort(key=lambda r: abs((r.get("duration") or 0) - duration))
            return res[0]["syncedLyrics"]
    except Exception:
        pass
    return ""


# ------------------------------------------------------------------- rendu
RATIOS = {
    "16:9 - YouTube (1920x1080)": (1920, 1080),
    "9:16 - TikTok / Reels / Shorts (1080x1920)": (1080, 1920),
    "1:1 - Carré (1080x1080)": (1080, 1080),
    "4:5 - Post Instagram (1080x1350)": (1080, 1350),
}


def set_size(w, h):
    global W, H
    W, H = w, h


def S(x):
    """Taille relative : x est donné pour une vidéo de 720 px de petit côté."""
    return max(1, int(round(x * min(W, H) / 720)))


def load_font(size):
    for p in (resource_path("fonts/BBHBogle-Regular.ttf"),
              r"C:\Windows\Fonts\segoeuib.ttf", "DejaVuSans-Bold.ttf"):
        try:
            f = ImageFont.truetype(p, size)
            f._bogle = p.endswith("BBHBogle-Regular.ttf")
            return f
        except Exception:
            continue
    return ImageFont.load_default()


# ------------------------------------------------- accents (BBH Bogle n'en a pas)
_MARKS = {"\u0301": "acute", "\u0300": "grave", "\u0302": "circ",
          "\u0308": "diaer", "\u0327": "ced"}
_REPL = {"«": '"', "»": '"', "œ": "oe", "Œ": "OE", "æ": "ae", "Æ": "AE"}


def split_marks(text):
    """'Été' -> ('Ete', [(0,'acute'), (2,'acute')])"""
    import unicodedata
    base, marks = [], []
    for ch in "".join(_REPL.get(c, c) for c in text):
        for c in unicodedata.normalize("NFD", ch):
            if c in _MARKS and base:
                marks.append((len(base) - 1, _MARKS[c]))
            elif unicodedata.combining(c):
                continue
            else:
                base.append(c)
    return "".join(base), marks


def tlen(draw, text, font):
    if getattr(font, "_bogle", False):
        text = split_marks(text)[0]
    return draw.textlength(text, font=font)


def draw_text(draw, xy, text, font, fill):
    if not getattr(font, "_bogle", False):
        draw.text(xy, text, font=font, fill=fill)
        return
    base, marks = split_marks(text)
    x, y = xy
    draw.text((x, y), base, font=font, fill=fill)
    s = font.size
    th = max(2, int(round(s * 0.085)))
    for i, kind in marks:
        x0 = x + draw.textlength(base[:i], font=font)
        bl, bt, br, bb = font.getbbox(base[i])
        l, t, r, b = x0 + bl, y + bt, x0 + br, y + bb
        cx, w = (l + r) / 2, (r - l)
        gap, h = s * 0.07, s * 0.15
        if kind == "acute":
            draw.line([(cx - w * 0.12, t - gap), (cx + w * 0.2, t - gap - h)], fill=fill, width=th)
        elif kind == "grave":
            draw.line([(cx + w * 0.12, t - gap), (cx - w * 0.2, t - gap - h)], fill=fill, width=th)
        elif kind == "circ":
            draw.line([(cx - w * 0.3, t - gap), (cx, t - gap - h), (cx + w * 0.3, t - gap)],
                      fill=fill, width=th, joint="curve")
        elif kind == "diaer":
            d = th * 0.75
            sp = max(w * 0.22, d * 1.6)
            for dx in (-sp, sp):
                cy = t - gap - h * 0.45
                draw.rectangle([cx + dx - d, cy - d, cx + dx + d, cy + d], fill=fill)
        elif kind == "ced":
            draw.line([(cx, b), (cx, b + s * 0.08), (cx - w * 0.18, b + s * 0.17)],
                      fill=fill, width=max(2, int(th * 0.8)), joint="curve")


def make_background(cover_bytes, title, artist):
    img = None
    if cover_bytes:
        try:
            img = Image.open(io.BytesIO(cover_bytes)).convert("RGB")
        except Exception:
            img = None
    if img is None:
        img = Image.new("RGB", (W, H), (25, 25, 35))
    s = max(W / img.width, H / img.height)
    img = img.resize((int(img.width * s) + 1, int(img.height * s) + 1), Image.LANCZOS)
    l, t = (img.width - W) // 2, (img.height - H) // 2
    img = img.crop((l, t, l + W, t + H))
    img = img.filter(ImageFilter.GaussianBlur(S(14)))      # flou léger
    img = ImageEnhance.Brightness(img).enhance(0.55)        # lisibilité
    d = ImageDraw.Draw(img)
    f_t, f_a = load_font(S(34)), load_font(S(24))
    y = H - S(90) - (S(40) if H > W else 0)
    for txt, f, col in ((title, f_t, (255, 255, 255)), (artist, f_a, (220, 220, 230))):
        if not txt:
            continue
        w = tlen(d, txt, f)
        draw_text(d, ((W - w) / 2 + S(2), y + S(2)), txt, f, (0, 0, 0))
        draw_text(d, ((W - w) / 2, y), txt, f, col)
        y += f.size + S(8)
    return np.asarray(img, dtype=np.float32)


def wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if tlen(draw, t, font) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def text_layer(line_cur, line_next):
    """Calque (couleur, alpha) : ligne courante en blanc + ombre douce, suivante en pâle."""
    pad = S(70)
    max_w = W - 2 * pad
    probe = ImageDraw.Draw(Image.new("L", (1, 1)))
    cur = Image.new("L", (W, H), 0)
    dim = Image.new("L", (W, H), 0)
    dc, dd = ImageDraw.Draw(cur), ImageDraw.Draw(dim)

    fb = load_font(S(60))
    wl = wrap(probe, line_cur, fb, max_w) if line_cur else []
    max_lines = 5 if H > W else 3
    while len(wl) > max_lines and fb.size > S(34):
        fb = load_font(fb.size - S(4))
        wl = wrap(probe, line_cur, fb, max_w)
    lh = int(fb.size * 1.4)
    y0 = H // 2 - S(40) - (len(wl) * lh) // 2
    for i, ln in enumerate(wl):
        w = tlen(dc, ln, fb)
        draw_text(dc, ((W - w) / 2, y0 + i * lh), ln, fb, 255)
    if line_next:
        fs = load_font(S(32))
        sl = wrap(probe, line_next, fs, max_w)[:2]
        y1 = y0 + len(wl) * lh + S(30)
        for i, ln in enumerate(sl):
            w = tlen(dd, ln, fs)
            draw_text(dd, ((W - w) / 2, y1 + i * int(fs.size * 1.35)), ln, fs, 255)

    core = np.asarray(cur, np.float32) / 255
    nxt = np.asarray(dim, np.float32) / 255 * 0.5
    off = S(3)
    sh_img = Image.new("L", (W, H), 0)
    sh_img.paste(Image.fromarray(np.maximum(np.asarray(cur), np.asarray(dim))), (off, off))
    shadow = np.asarray(sh_img.filter(ImageFilter.GaussianBlur(S(5))), np.float32) / 255 * 0.7

    alpha = 1 - (1 - core) * (1 - nxt) * (1 - shadow)
    premul = core * 255 + nxt * 255 * (1 - core)
    with np.errstate(divide="ignore", invalid="ignore"):
        col = np.where(alpha > 1e-3, premul / np.maximum(alpha, 1e-3), 0)
    col = np.repeat(np.clip(col, 0, 255)[..., None], 3, axis=2)
    return col, alpha


def composite(bg, layer):
    col, a = layer
    return np.clip(bg * (1 - a[..., None]) + col * a[..., None], 0, 255)


def to_bytes(arr):
    return arr.astype(np.uint8).tobytes()


def render_video(audio_path, out_path, title, artist, cover, lyrics, duration,
                 progress=None, cancel=None, size=(1920, 1080)):
    """lyrics : [(t, ligne)]. progress(float 0..1, texte). cancel() -> bool."""
    import imageio_ffmpeg
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    set_size(*size)
    bg = make_background(cover, title, artist)
    bg_bytes = to_bytes(bg)

    # une entrée par ligne ; ligne vide = pause instrumentale
    items = [(t, l) for t, l in lyrics]
    layer_cache = {}

    def layer(i):
        if i not in layer_cache:
            cur = items[i][1] if 0 <= i < len(items) else ""
            nxt = items[i + 1][1] if 0 <= i + 1 < len(items) else ""
            layer_cache.clear() if len(layer_cache) > 3 else None
            layer_cache[i] = text_layer(cur, nxt) if (cur or nxt) else None
        return layer_cache[i]

    times = [t for t, _ in items]
    n_frames = int(duration * FPS) + 1

    cmd = [ffmpeg, "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", audio_path, "-map", "0:v", "-map", "1:a",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out_path]
    flags = 0x08000000 if os.name == "nt" else 0  # pas de fenêtre console
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE,
                            creationflags=flags)

    import bisect
    last_key, last_bytes = None, None
    try:
        for f in range(n_frames):
            if cancel and cancel():
                proc.kill()
                return False
            t = f / FPS
            i = bisect.bisect_right(times, t) - 1  # ligne courante
            # fondu d'entrée de la ligne i, sinon image stable
            since = t - times[i] if i >= 0 else 99
            alpha_in = min(1.0, since / FADE) if i >= 0 else 1.0
            key = (i, round(alpha_in, 2) if alpha_in < 1 else 1)
            if key != last_key:
                if i < 0 or layer(i) is None:
                    frame = bg_bytes
                else:
                    L = layer(i)
                    if alpha_in < 1:
                        L = (L[0], L[1] * alpha_in)
                    frame = to_bytes(composite(bg, L))
                last_key, last_bytes = key, frame
            proc.stdin.write(last_bytes)
            if progress and f % 15 == 0:
                progress(f / n_frames, f"Rendu {f}/{n_frames} images")
        proc.stdin.close()
        err = proc.stderr.read().decode(errors="ignore")
        proc.wait()
        if proc.returncode != 0:
            raise RuntimeError("ffmpeg a échoué :\n" + err[-800:])
    except BrokenPipeError:
        err = proc.stderr.read().decode(errors="ignore")
        raise RuntimeError("ffmpeg s'est arrêté :\n" + err[-800:])
    if progress:
        progress(1.0, "Terminé")
    return True
