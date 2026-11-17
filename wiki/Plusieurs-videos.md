# Plusieurs vidéos en même temps

## Préparer la liste

- **Ajouter des musiques…** accepte plusieurs fichiers d'un coup (Ctrl/Maj + clic). Tu peux ajouter
  d'autres fichiers plus tard.
- **Retirer** supprime les musiques sélectionnées de la liste (pas du disque) ; **Vider** retire tout.
- Chaque musique garde **ses propres réglages** : titre, artiste, pochette, paroles, format, avec/sans paroles.
- Les nouvelles musiques reprennent le format et le mode avec/sans paroles affichés au moment de l'ajout.
- **Appliquer ce format et ce mode à toutes** copie ces deux réglages sur toute la liste.

## Lancer

1. Règle **Vidéos en même temps**.
2. **Créer toutes les vidéos** → choisis un dossier : toutes les vidéos y sont enregistrées.
3. La colonne **État** affiche pour chaque musique : *En attente*, *Rendu NN %*, *Terminé ✓*,
   *Annulé* ou *Erreur ✗*. La barre en bas montre l'avancement global.
4. À la fin, un récapitulatif liste les vidéos créées et les éventuelles erreurs.

Pendant le rendu, les réglages sont verrouillés. **Annuler** arrête toutes les vidéos en cours et en attente
(les fichiers déjà terminés sont conservés).

## Combien en même temps ?

Chaque vidéo tourne dans **son propre processus** et utilise un cœur du processeur pour dessiner les images,
plus ffmpeg pour l'encodage.

- Valeur par défaut : la moitié des cœurs du PC (4 au maximum).
- Sur un PC portable récent, **2 à 4** est un bon réglage.
- Au-delà du nombre de cœurs, chaque vidéo ralentit et on ne gagne plus rien au total ;
  la mémoire utilisée augmente aussi (quelques centaines de Mo par vidéo en cours).
