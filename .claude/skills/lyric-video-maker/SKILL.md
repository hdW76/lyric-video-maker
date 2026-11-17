---
name: lyric-video-maker
description: Génère une vidéo de paroles (lyric video MP4) à partir d'un fichier audio avec le moteur du repo hdW76/lyric-video-maker (pochette floutée en fond, paroles synchronisées LRC, titre/artiste, formats 16:9, 9:16, 1:1, 4:5). À utiliser dès que l'utilisateur veut une lyric video, un clip de paroles, une vidéo TikTok/Reels/Shorts/YouTube à partir d'une musique, ou veut modifier/déboguer/publier l'appli Lyric Video Maker, même s'il ne cite pas le repo.
---

# Lyric Video Maker

Ce repo contient une appli Windows (tkinter) et un moteur Python utilisable sans interface. Ce skill sert à produire une vidéo de paroles avec ce moteur, ou à faire évoluer le projet.

## Mise en place

Si le repo n'est pas déjà le dossier courant :

```bash
GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 https://github.com/hdW76/lyric-video-maker /home/claude/lyric-video-maker
pip install --break-system-packages mutagen Pillow numpy imageio-ffmpeg
```

Ne pas installer `pyinstaller` pour un simple rendu : il ne sert qu'à fabriquer l'exe Windows. L'ffmpeg vient de `imageio-ffmpeg`, rien d'autre à installer.

## Produire une vidéo

Fichiers : `lyricvideo_core.py` (moteur), `app.py` (interface), `fonts/` (police BBH Bogle, requise : le moteur la cherche via `resource_path`, donc lancer depuis le dossier cloné ou y ajouter le chemin avec `sys.path`).

```python
import sys; sys.path.insert(0, "/home/claude/lyric-video-maker")
import lyricvideo_core as core

title, artist, duration, cover = core.read_tags("musique.mp3")   # cover = octets ou None
lrc = core.fetch_lrclib(title, artist, duration)                  # "" si rien trouvé
lyrics = core.lyrics_from_text(lrc or open("paroles.lrc").read(), duration)
core.render_video("musique.mp3", "clip.mp4", title, artist, cover, lyrics, duration,
                  size=core.RATIOS["9:16 - TikTok / Reels / Shorts (1080x1920)"])
```

Formats (`core.RATIOS`) : 16:9 1920x1080, 9:16 1080x1920, 1:1 1080x1080, 4:5 1080x1350. Sortie MP4 H.264 CRF 20 + AAC 192k, 30 i/s, durée = tout le morceau.

## Points d'attention

- **Paroles** : LRCLIB (`lrclib.net`) peut être bloqué par la liste d'autorisation réseau du bac à sable. Si `fetch_lrclib` renvoie vide, demander à l'utilisateur de fournir les paroles : au format LRC (`[01:23.45] ligne`, synchro exacte, ligne vide `[02:10.00]` = pause) ou en texte simple (répartition régulière, approximative : le prévenir).
- **Droits** : rappeler brièvement qu'il faut les droits sur la musique avant de publier.
- **Accents** : la police BBH Bogle n'a pas d'accents ; le moteur les dessine à la main (`split_marks` / `draw_text`) et remplace `«»` par `"`, `œ` par `oe`. Le texte s'affiche toujours en majuscules : c'est normal, ne pas "corriger".
- **Vérifier le résultat** : avant de livrer, extraire une image au milieu du morceau (`ffmpeg -ss 30 -i clip.mp4 -frames:v 1 f.png`, ffmpeg via `imageio_ffmpeg.get_ffmpeg_exe()`) et la regarder : texte lisible, pas de débordement, accents corrects.
- **Test rapide** : pour valider une modif du moteur, générer un sinus de 5 s (`ffmpeg -f lavfi -i sine=frequency=440:duration=5 test.mp3`) et rendre les 4 formats, comme le fait le workflow CI.

## Modifier ou publier le projet

- Structure : `app.py` (UI), `lyricvideo_core.py` (tags, LRC, rendu, ffmpeg), `run.bat`/`build.bat` (Windows), `.github/workflows/build-exe.yml`.
- La CI (GitHub Actions, windows-latest) teste le moteur puis construit `LyricVideoMaker.exe` et publie une release `v1.0.N` à chaque push sur `main` touchant `app.py`, `lyricvideo_core.py`, `fonts/**`, `requirements.txt` ou le workflow. Ne pas toucher ces fichiers sans intention de republier.
- Garder la licence GPL v3 et l'OFL de la police dans toute redistribution.
