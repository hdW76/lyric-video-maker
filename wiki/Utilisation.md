# Utilisation

## Fenêtre principale

```
┌ Musiques ───────────────────────────────────────────────────────────┐
│ [Ajouter des musiques…] [Retirer] [Vider]   [Appliquer … à toutes]  │
│ Musique                     Format   Paroles         État           │
│ Ma chanson — Artiste        16:9     Synchronisées   En attente     │
│ Autre son                   9:16     Désactivées     Rendu 42 %     │
└─────────────────────────────────────────────────────────────────────┘
┌ Réglages de la musique sélectionnée ────────────────────────────────┐
│ [pochette]  Titre   [__________]        [Changer la pochette…]      │
│             Artiste [__________]        [Chercher la pochette…]     │
│             Format  [16:9 - YouTube ▼]                              │
│ [x] Afficher les paroles  [Chercher les paroles (LRCLIB)]           │
│ ┌ paroles ──────────────────────────────────────────────────────┐   │
│ │ [00:12.30] Première ligne                                     │   │
└─────────────────────────────────────────────────────────────────────┘
 Vidéos en même temps [2]  [Créer toutes les vidéos] [Annuler] ▓▓▓░░
```

## Pas à pas

1. **Ajouter des musiques…** — choisis un ou plusieurs fichiers audio.
   Pour chacun, l'appli lit le titre, l'artiste et la pochette, puis cherche en tâche de fond
   la pochette manquante et les paroles. La colonne *Paroles* indique le résultat.
2. **Clique sur une musique** pour voir et modifier ses réglages. Chaque musique a les siens.
3. **Vérifie le titre et l'artiste** : ils s'affichent dans la vidéo. S'ils étaient faux, corrige-les puis
   relance **Chercher les paroles** et/ou **Chercher la pochette en ligne**.
4. **Choisis le format** ([[Formats vidéo|Formats-video]]) et si les paroles doivent s'afficher
   ([[Mode sans paroles|Mode-sans-paroles]]).
5. **Créer toutes les vidéos** → choisis un dossier. Suis l'avancement dans la colonne *État*.

## Ce que contient la vidéo

**Avec paroles**
- fond : la pochette, agrandie pour remplir l'écran, floutée et assombrie ;
- au centre : la ligne en cours, en grand, blanche avec une ombre douce ;
- juste dessous : la ligne suivante, plus petite et plus pâle ;
- en bas au centre : titre et artiste ;
- chaque nouvelle ligne apparaît avec un court fondu (0,25 s).

**Sans paroles** : voir [[Mode sans paroles|Mode-sans-paroles]].

## Noms des fichiers créés

La vidéo prend le nom du fichier audio : `ma musique.mp3` → `ma musique.mp4`.
Si ce fichier existe déjà, l'appli crée `ma musique (2).mp4` au lieu d'écraser.

## Combien de temps ça prend ?

Le rendu est en général plusieurs fois plus rapide que la durée de la musique
(un morceau de 3 min prend souvent moins d'une minute), et plus rapide encore sans paroles.
