# Pochettes

## D'où vient la pochette

L'appli essaie dans cet ordre :

1. **Dans le fichier audio** (tags) : MP3/WAV (ID3), M4A (covr), FLAC, OGG/Opus.
2. **Avec ffmpeg** : dernier recours pour extraire une image intégrée d'un format inhabituel.
3. **En ligne**, si le fichier n'en contient pas, à partir du titre et de l'artiste :
   - **Deezer** (image 1000×1000) ;
   - sinon **iTunes** (image 1000×1000).

Pendant la recherche, la miniature affiche *« Recherche de la pochette… »*.

## Corriger une pochette

- **Mauvaise pochette trouvée en ligne** : corrige le titre / l'artiste, puis
  **Chercher la pochette en ligne**.
- **Utiliser ta propre image** : **Changer la pochette…** (JPG, PNG, WEBP).
- **Aucune pochette** : la vidéo utilise un fond uni sombre.

## Rendu

| Mode | Pochette |
|---|---|
| Avec paroles | plein écran, recadrée pour remplir, floutée et assombrie (pour que le texte reste lisible) |
| Sans paroles | carré net au centre, coins arrondis, ombre ; fond uni de sa couleur dominante |

Les pochettes non carrées sont recadrées au centre en plein écran, et étirées en carré en mode sans paroles.
