# FAQ et dépannage

### Windows bloque l'exe (« Windows a protégé votre ordinateur »)
**Informations complémentaires → Exécuter quand même**. Voir [[Installation]].

### Mon antivirus supprime l'exe
Certains antivirus se méfient des exe PyInstaller non signés (faux positif). Ajoute une exception,
ou utilise la version code source (`run.bat`).

### Les paroles ne sont pas trouvées
- Vérifie le **titre** et l'**artiste** (sans « Official Video », « Lyrics », « HD »…), puis
  **Chercher les paroles (LRCLIB)**.
- La musique n'est peut-être pas sur LRCLIB : colle les paroles à la main
  ([[Paroles et format LRC|Paroles-et-format-LRC]]).
- Il faut une connexion internet.

### Les paroles sont décalées
- Les paroles LRCLIB correspondent à une version précise du morceau ; une version radio, live ou
  remasterisée peut être décalée. Corrige les horodatages dans la zone de texte.
- En texte simple, les paroles sont réparties au hasard du temps : utilise du LRC.

### Il n'y a pas la pochette en fond
- La miniature affiche *(pas de pochette)* : rien dans le fichier ni en ligne. Corrige le titre/artiste et
  **Chercher la pochette en ligne**, ou **Changer la pochette…**.
- Mauvaise pochette : même chose.
- En mode sans paroles, la pochette n'est pas en fond mais au centre : c'est voulu
  ([[Mode sans paroles|Mode-sans-paroles]]).

### Des carrés à la place de certains caractères
La police BBH Bogle ne couvre que l'alphabet latin de base. Les accents français sont dessinés par
l'appli, mais d'autres alphabets (cyrillique, japonais, emoji…) ne s'afficheront pas.

### « Erreur ✗ » dans la colonne État
Le récapitulatif de fin donne le message. Causes fréquentes :
- fichier audio abîmé ou protégé (DRM) ;
- dossier de sortie protégé en écriture ou disque plein ;
- fichier audio déplacé ou supprimé pendant le rendu.

### Le PC rame pendant le rendu
Baisse **Vidéos en même temps** (voir [[Plusieurs vidéos en même temps|Plusieurs-videos]]).

### Puis-je publier ces vidéos ?
L'appli ne change rien aux droits : publier une musique qui ne t'appartient pas peut être bloqué ou
démonétisé par les plateformes. Les pochettes et paroles trouvées en ligne appartiennent aussi à leurs auteurs.

### Signaler un bug ou proposer une idée
Ouvre une [issue](https://github.com/hdW76/lyric-video-maker/issues) avec : la version (page Releases),
le format du fichier audio, ce que tu as fait et ce qui s'est passé.
