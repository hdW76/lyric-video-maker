# Installation

## Option 1 — l'exe (recommandé)

1. Ouvre la page **[Releases](https://github.com/hdW76/lyric-video-maker/releases/latest)**.
2. Télécharge **`LyricVideoMaker.exe`** (~70 Mo).
3. Double-clique dessus. C'est tout : Python, ffmpeg et la police sont inclus.

### « Windows a protégé votre ordinateur »

L'exe n'est pas signé numériquement (un certificat coûte cher), donc SmartScreen peut le bloquer au premier lancement :
clique sur **Informations complémentaires → Exécuter quand même**.

L'exe est construit automatiquement par GitHub à partir du code public du dépôt
(voir l'onglet [Actions](https://github.com/hdW76/lyric-video-maker/actions)), tu peux donc vérifier ce qu'il contient.

### Démarrage un peu lent ?

C'est normal : l'exe « tout-en-un » se décompresse dans un dossier temporaire à chaque lancement (quelques secondes).

## Option 2 — depuis le code source

Utile pour modifier l'appli, ou sur macOS / Linux.

1. Installe **Python 3.10+** depuis [python.org](https://www.python.org/downloads/) en cochant **Add Python to PATH**.
2. Télécharge le code : **Code → Download ZIP**, puis dézippe.
3. Windows : double-clique **`run.bat`**.
   Autres systèmes :
   ```
   pip install -r requirements.txt
   python app.py
   ```
   (sous Linux, installe aussi `python3-tk`).

Pour créer ton propre exe : **`build.bat`** → `dist\LyricVideoMaker.exe`.

## Mise à jour

Il n'y a pas de mise à jour automatique : retélécharge simplement le dernier exe depuis
[Releases](https://github.com/hdW76/lyric-video-maker/releases/latest) et remplace l'ancien.
