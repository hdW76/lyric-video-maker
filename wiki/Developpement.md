# Développement

## Structure du dépôt

```
app.py                   interface tkinter (file de musiques, réglages, rendu parallèle)
lyricvideo_core.py       moteur sans interface
fonts/                   BBH Bogle + licence OFL
tests/smoke_engine.py    rendu de tous les formats, avec et sans paroles
tests/smoke_gui.py       pilote la vraie fenêtre : 3 musiques rendues en parallèle
wiki/                    sources de ce wiki
run.bat / build.bat      lancer / construire l'exe sous Windows
.github/workflows/       construction de l'exe, publication du wiki
```

## Le moteur (`lyricvideo_core.py`)

| Fonction | Rôle |
|---|---|
| `read_tags(path)` | → `(titre, artiste, durée, octets_pochette)` ; ID3, MP4, FLAC, Vorbis/Opus, puis ffmpeg |
| `fetch_cover_online(titre, artiste)` | pochette Deezer, puis iTunes |
| `fetch_lrclib(titre, artiste, durée)` | paroles synchronisées LRCLIB (texte LRC) |
| `lyrics_from_text(texte, durée)` | LRC → `[(secondes, ligne)]` ; texte simple → réparti régulièrement |
| `render_video(..., size=, show_lyrics=)` | dessine les images et les envoie à ffmpeg |
| `render_job(id, kwargs, queue, event)` | version « processus fils » utilisée pour le rendu parallèle |
| `RATIOS` | formats proposés : libellé → (largeur, hauteur) |

### Rendu

- Les images sont dessinées avec Pillow + numpy puis envoyées en brut (`rgb24`) à ffmpeg par un tube.
- Le fond est calculé **une seule fois** ; une image n'est recalculée que lorsque la ligne change ou pendant
  un fondu, sinon la précédente est réutilisée : c'est ce qui rend le rendu rapide.
- Les tailles sont exprimées pour un petit côté de 720 px et mises à l'échelle avec `S(x)`.
- ffmpeg vient de `imageio-ffmpeg` (binaire inclus, rien à installer).

### Utiliser le moteur en script

```python
import lyricvideo_core as core

title, artist, duration, cover = core.read_tags("musique.mp3")
cover = cover or core.fetch_cover_online(title, artist)
lyrics = core.lyrics_from_text(core.fetch_lrclib(title, artist, duration), duration)
core.render_video("musique.mp3", "clip.mp4", title, artist, cover, lyrics, duration,
                  size=(1080, 1920), show_lyrics=True)
```

## Rendu parallèle

`app.py` lance chaque vidéo dans un `ProcessPoolExecutor` (un processus par vidéo, car le dessin des
images est en Python). La progression revient par une `Manager().Queue()`, l'annulation par un
`Manager().Event()`. `multiprocessing.freeze_support()` est indispensable pour l'exe PyInstaller.

## Construction et publication

Le workflow `.github/workflows/build-exe.yml` tourne sur Windows à chaque changement du code sur `main` :

1. installe les dépendances ;
2. `tests/smoke_engine.py` puis `tests/smoke_gui.py` ;
3. construit l'exe avec PyInstaller (`--onefile --windowed`, police et ffmpeg inclus) ;
4. teste l'exe : `LyricVideoMaker.exe --selftest <dossier>` rend 4 vidéos en parallèle sans fenêtre ;
5. publie une release `v1.0.N` avec l'exe.

Il peut aussi être lancé à la main : onglet **Actions → Build Windows exe → Run workflow**.

## Modifier le wiki

Les pages sont dans le dossier [`wiki/`](https://github.com/hdW76/lyric-video-maker/tree/main/wiki)
du dépôt. Le workflow `.github/workflows/wiki.yml` les copie dans le wiki GitHub à chaque modification
sur `main`. Ne modifie pas le wiki directement sur GitHub : tes changements seraient écrasés.

Liens entre pages : le texte et le nom de la page (nom du fichier sans `.md`) séparés par une barre verticale, entre doubles crochets. Exemples dans `_Sidebar.md`.

## Licences

Code : GPL v3. Police BBH Bogle : SIL Open Font License 1.1 (voir `fonts/OFL.txt`).
