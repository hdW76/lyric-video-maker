"""Lyric Video Maker - interface Windows (tkinter)."""
import io
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

import lyricvideo_core as core


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Lyric Video Maker")
        self.geometry("820x680")
        self.audio = None
        self.cover = None
        self.duration = 0.0
        self.cancel_flag = False

        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")
        ttk.Button(top, text="Choisir une musique…", command=self.pick).pack(side="left")
        self.path_lbl = ttk.Label(top, text="Aucun fichier", padding=(10, 0))
        self.path_lbl.pack(side="left")

        info = ttk.Frame(self, padding=(10, 0))
        info.pack(fill="x")
        self.thumb = ttk.Label(info)
        self.thumb.grid(row=0, column=0, rowspan=2, padx=(0, 10))
        self.title_var, self.artist_var = tk.StringVar(), tk.StringVar()
        ttk.Label(info, text="Titre").grid(row=0, column=1, sticky="e")
        ttk.Entry(info, textvariable=self.title_var, width=50).grid(row=0, column=2, pady=2)
        ttk.Label(info, text="Artiste").grid(row=1, column=1, sticky="e")
        ttk.Entry(info, textvariable=self.artist_var, width=50).grid(row=1, column=2, pady=2)
        ttk.Button(info, text="Changer la pochette…", command=self.pick_cover).grid(
            row=0, column=3, padx=10, sticky="ew")
        ttk.Button(info, text="Chercher la pochette en ligne",
                   command=lambda: (setattr(self, "cover", None), self.find_cover())).grid(
            row=1, column=3, padx=10, sticky="ew")
        ttk.Label(info, text="Format").grid(row=2, column=1, sticky="e")
        self.ratio_var = tk.StringVar(value=list(core.RATIOS)[0])
        ttk.Combobox(info, textvariable=self.ratio_var, values=list(core.RATIOS),
                     state="readonly", width=47).grid(row=2, column=2, pady=2)

        lf = ttk.LabelFrame(self, text="Paroles (format LRC [mm:ss.xx] ou texte simple)", padding=8)
        lf.pack(fill="both", expand=True, padx=10, pady=10)
        bar = ttk.Frame(lf)
        bar.pack(fill="x")
        self.lyrics_on = tk.BooleanVar(value=True)
        ttk.Checkbutton(bar, text="Afficher les paroles", variable=self.lyrics_on,
                        command=self.toggle_lyrics).pack(side="left", padx=(0, 12))
        self.search_btn = ttk.Button(bar, text="Chercher les paroles (LRCLIB)", command=self.search)
        self.search_btn.pack(side="left")
        self.lyr_status = ttk.Label(bar, text="", padding=(10, 0))
        self.lyr_status.pack(side="left")
        self.text = tk.Text(lf, wrap="word", height=14)
        self.text.pack(fill="both", expand=True, pady=(6, 0))

        bot = ttk.Frame(self, padding=10)
        bot.pack(fill="x")
        self.go = ttk.Button(bot, text="Créer la vidéo", command=self.generate)
        self.go.pack(side="left")
        self.stop = ttk.Button(bot, text="Annuler", command=self.cancel, state="disabled")
        self.stop.pack(side="left", padx=6)
        self.bar = ttk.Progressbar(bot, length=400)
        self.bar.pack(side="left", padx=10)
        self.status = ttk.Label(bot, text="")
        self.status.pack(side="left")

    # ---------------------------------------------------------- actions
    def toggle_lyrics(self):
        on = self.lyrics_on.get()
        self.text.config(state="normal" if on else "disabled",
                         foreground="black" if on else "gray")
        self.search_btn.config(state="normal" if on else "disabled")
        if not on:
            self.lyr_status.config(text="Sans paroles : pochette nette au centre, titre et artiste dessous.")
        else:
            self.lyr_status.config(text="")

    def pick(self):
        p = filedialog.askopenfilename(
            filetypes=[("Audio", "*.mp3 *.m4a *.flac *.wav *.ogg *.aac"), ("Tous", "*.*")])
        if not p:
            return
        try:
            title, artist, dur, cover = core.read_tags(p)
        except Exception as e:
            messagebox.showerror("Erreur", f"Lecture impossible : {e}")
            return
        self.audio, self.duration, self.cover = p, dur, cover
        self.path_lbl.config(text=os.path.basename(p))
        self.title_var.set(title)
        self.artist_var.set(artist)
        self.show_thumb()
        if cover is None:
            self.find_cover()
        self.search()

    def find_cover(self):
        self.thumb.config(image="", text="Recherche\nde la\npochette…")
        t, a = self.title_var.get(), self.artist_var.get()

        def work():
            img = core.fetch_cover_online(t, a)
            self.after(0, lambda: self.on_cover(img))
        threading.Thread(target=work, daemon=True).start()

    def on_cover(self, img):
        if img and self.cover is None:
            self.cover = img
        self.show_thumb()
        if self.cover is None:
            messagebox.showinfo(
                "Pochette",
                "Aucune pochette dans le fichier ni en ligne.\n"
                "Utilise « Changer la pochette… » pour en choisir une.")

    def pick_cover(self):
        p = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.jpeg *.png *.webp")])
        if p:
            with open(p, "rb") as f:
                self.cover = f.read()
            self.show_thumb()

    def show_thumb(self):
        if self.cover:
            try:
                im = Image.open(io.BytesIO(self.cover)).convert("RGB")
                im.thumbnail((80, 80))
                self._tk = ImageTk.PhotoImage(im)
                self.thumb.config(image=self._tk, text="")
                return
            except Exception:
                self.cover = None
        if True:
            self.thumb.config(image="", text="(pas de\npochette)")

    def search(self):
        if not self.audio:
            return
        self.lyr_status.config(text="Recherche…")
        t, a, d = self.title_var.get(), self.artist_var.get(), self.duration

        def work():
            res = core.fetch_lrclib(t, a, d)
            self.after(0, lambda: self.on_lyrics(res))
        threading.Thread(target=work, daemon=True).start()

    def on_lyrics(self, res):
        if res:
            st = self.text.cget("state")
            self.text.config(state="normal")
            self.text.delete("1.0", "end")
            self.text.insert("1.0", res)
            self.text.config(state=st)
            self.lyr_status.config(text="Paroles synchronisées trouvées.")
        else:
            self.lyr_status.config(
                text="Rien trouvé : colle les paroles (réparties régulièrement) ou laisse vide.")

    def generate(self):
        if not self.audio:
            messagebox.showinfo("Musique", "Choisis d'abord une musique.")
            return
        base = os.path.splitext(os.path.basename(self.audio))[0] + ".mp4"
        out = filedialog.asksaveasfilename(defaultextension=".mp4", initialfile=base,
                                           filetypes=[("Vidéo MP4", "*.mp4")])
        if not out:
            return
        lyrics = core.lyrics_from_text(self.text.get("1.0", "end"), self.duration)
        self.cancel_flag = False
        self.go.config(state="disabled")
        self.stop.config(state="normal")
        args = (self.audio, out, self.title_var.get(), self.artist_var.get(),
                self.cover, lyrics, self.duration)
        size = core.RATIOS[self.ratio_var.get()]
        show_lyrics = self.lyrics_on.get()

        def prog(v, txt):
            self.after(0, lambda: (self.bar.config(value=v * 100), self.status.config(text=txt)))

        def work():
            try:
                ok = core.render_video(*args, progress=prog, cancel=lambda: self.cancel_flag,
                                       size=size, show_lyrics=show_lyrics)
                msg = ("Vidéo enregistrée :\n" + out) if ok else "Annulé."
                self.after(0, lambda: messagebox.showinfo("Lyric Video Maker", msg))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Erreur", str(e)))
            finally:
                self.after(0, lambda: (self.go.config(state="normal"),
                                       self.stop.config(state="disabled")))
        threading.Thread(target=work, daemon=True).start()

    def cancel(self):
        self.cancel_flag = True


if __name__ == "__main__":
    App().mainloop()
