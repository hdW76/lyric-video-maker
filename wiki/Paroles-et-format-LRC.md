# Paroles et format LRC

## Recherche automatique

À l'ajout d'une musique, l'appli interroge [LRCLIB](https://lrclib.net), une base de paroles
synchronisées gratuite et ouverte, avec le **titre**, l'**artiste** et la **durée** :

1. recherche exacte (titre + artiste + durée) ;
2. sinon, recherche large, puis choix du résultat dont la durée est la plus proche.

Seules les paroles **synchronisées** sont retenues. Si rien n'est trouvé : *« Rien trouvé »*.

> Le titre et l'artiste doivent être corrects. Un fichier nommé `track01` ou un titre
> du type `Ma chanson (Official Video) [HD]` ne sera pas trouvé : corrige le titre puis clique
> **Chercher les paroles (LRCLIB)**.

## Le format LRC

Chaque ligne commence par le moment où elle doit apparaître, `[minutes:secondes.centièmes]` :

```
[00:12.30]Première ligne
[00:15.80]Deuxième ligne
[00:19.00]
[00:31.40]Après le solo
```

- Une ligne **vide** (`[00:19.00]` seul) efface l'écran : pratique pour les passages instrumentaux.
- Plusieurs horodatages sur une ligne (`[00:40.00][01:20.00]Refrain`) la répètent à chaque moment.
- Les lignes sans horodatage (ex. `[ar:Artiste]`, commentaires) sont ignorées.
- Une ligne reste affichée jusqu'à la suivante.

### Trouver ou créer un fichier LRC

- Sur [lrclib.net](https://lrclib.net) : cherche la musique et copie les *synced lyrics*.
- Pour en créer un : des éditeurs en ligne permettent de taper sur une touche au rythme de la musique
  (cherche « LRC editor »). Colle ensuite le résultat dans l'appli.

## Texte simple (sans horodatage)

Si tu colles des paroles sans horodatage, une ligne par phrase, l'appli les **répartit à intervalle
régulier** entre le début et la fin du morceau. Ce n'est **pas** synchronisé avec le chant : utile pour
un rendu rapide, mais préfère le LRC pour un résultat propre.

## Accents et caractères spéciaux

La police BBH Bogle n'a pas de lettres accentuées. L'appli dessine elle-même les accents
(é è ê ë à â ä ç î ï ô ö ù û ü…) au-dessus de la lettre de base.
Quelques remplacements : `« »` → `"`, `œ` → `oe`, `æ` → `ae`.
La police est tout en majuscules : c'est son style.

## Lignes longues

Une ligne trop longue est coupée automatiquement sur plusieurs lignes (3 max en horizontal,
5 en vertical) ; si besoin, le texte est réduit pour tenir.
