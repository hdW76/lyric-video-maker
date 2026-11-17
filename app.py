"""Lyric Video Maker - interface Windows (tkinter).

Plusieurs musiques dans une file d'attente, chacune avec ses réglages,
rendues en parallèle (un processus par vidéo).
"""
import io
import multiprocessing as mp
import os
import queue
import threading
import tkinter as tk
from concurrent.futures import ProcessPoolExecutor
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

import lyricvideo_core as core

AUDIO_TYPES = [("Audio", "*.mp3 *.m4a *.flac *.wav *.ogg *.opus *.aac"), ("Tous", "*.*")]


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Lyric Video Maker")
        self.geometry("900x820")
        self.minsize(820, 720)
        self.tracks = {}          # id -> dict
        self.order = []           # ids dans l'ordre d'affichage
        self.current = None       # id sélectionné
        self.next_id = 1
        self.fetch_q = queue.Queue()
        self.running = False
        threading.Thread(target=self.fetch_worker, daemon=True).start()
        self.build_ui()

    # ============================================================== interface
    def build_ui(self):
        # ---- file d'attente
        qf = ttk.LabelFrame(self, text="Musiques", padding=8)
        qf.pack(fill="x", padx=10, pady=(10, 0))
        bar = ttk.Frame(qf)
        bar.pack(fill="x")
        ttk.Button(bar, text="Ajouter des musiques…", command=self.add_files).pack(side="left")
        ttk.Button(bar, text="Retirer", command=self.remove_selected).pack(side="left", padx=6)
        ttk.Button(bar, text="Vider", command=self.clear_all).pack(side="left")
        ttk.Button(bar, text="Appliquer ce format et ce mode à toutes",
                   command=self.apply_to_all).pack(side="right")

        cols = ("titre", "format", "paroles", "etat")
        self.tree = ttk.Treeview(qf, columns=cols, show="headings", height=7,
                                 selectmode="extended")
        for c, txt, w in (("titre", "Musique", 380), ("format", "Format", 110),
                          ("paroles", "Paroles", 150), ("etat", "État", 150)):
            self.tree.heading(c, text=txt)
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="x", pady=(6, 0))
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        # ---- réglages de la musique sélectionnée
        ef = ttk.LabelFrame(self, text="Réglages de la musique sélectionnée", padding=8)
        ef.pack(fill="both", expand=True, padx=10, pady=10)
        self.editor = ef

        info = ttk.Frame(ef)
        info.pack(fill="x")
        self.thumb = ttk.Label(info, text="", width=12, anchor="center")
        self.thumb.grid(row=0, column=0, rowspan=3, padx=(0, 10))
        self.title_var, self.artist_var = tk.StringVar(), tk.StringVar()
        ttk.Label(info, text="Titre").grid(row=0, column=1, sticky="e")
        ttk.Entry(info, textvariable=self.title_var, width=46).grid(row=0, column=2, pady=2)
        ttk.Label(info, text="Artiste").grid(row=1, column=1, sticky="e")
        ttk.Entry(info, textvariable=self.artist_var, width=46).grid(row=1, column=2, pady=2)
        ttk.Label(info, text="Format").grid(row=2, column=1, sticky="e")
        self.ratio_var = tk.StringVar(value=list(core.RATIOS)[0])
        ttk.Combobox(info, textvariable=self.ratio_var, values=list(core.RATIOS),
                     state="readonly", width=44).grid(row=2, column=2, pady=2)
        ttk.Button(info, text="Changer la pochette…", command=self.pick_cover).grid(
            row=0, column=3, padx=10, sticky="ew")
        ttk.Button(info, text="Chercher la pochette en ligne",
                   command=self.refetch_cover).grid(row=1, column=3, padx=10, sticky="ew")

        lbar = ttk.Frame(ef)
        lbar.pack(fill="x", pady=(10, 0))
        self.lyrics_on = tk.BooleanVar(value=True)
        ttk.Checkbutton(lbar, text="Afficher les paroles", variable=self.lyrics_on,
                        command=self.toggle_lyrics).pack(side="left", padx=(0, 12))
        self.search_btn = ttk.Button(lbar, text="Chercher les paroles (LRCLIB)",
                                     command=self.refetch_lyrics)
        self.search_btn.pack(side="left")
        self.lyr_status = ttk.Label(lbar, text="", padding=(10, 0))
        self.lyr_status.pack(side="left")
        ttk.Label(ef, text="Paroles : format LRC [mm:ss.xx] ou texte simple",
                  foreground="gray").pack(anchor="w", pady=(6, 0))
        self.text = tk.Text(ef, wrap="word", height=10)
        self.text.pack(fill="both", expand=True)

        # ---- génération
        bot = ttk.Frame(self, padding=(10, 0, 10, 10))
        bot.pack(fill="x")
        ttk.Label(bot, text="Vidéos en même temps").pack(side="left")
        default_par = max(1, min(4, (os.cpu_count() or 2) // 2))
        self.par_var = tk.IntVar(value=default_par)
        ttk.Spinbox(bot, from_=1, to=8, textvariable=self.par_var, width=4).pack(
            side="left", padx=(6, 14))
        self.go = ttk.Button(bot, text="Créer toutes les vidéos", command=self.generate)
        self.go.pack(side="left")
        self.stop = ttk.Button(bot, text="Annuler", command=self.cancel, state="disabled")
        self.stop.pack(side="left", padx=6)
        self.bar = ttk.Progressbar(bot, length=220)
        self.bar.pack(side="left", padx=10)
        self.status = ttk.Label(bot, text="Ajoute une ou plusieurs musiques.")
        self.status.pack(side="left")

        self.set_editor_enabled(False)

    def set_editor_enabled(self, on):
        def walk(w):
            for c in w.winfo_children():
                try:
                    c.configure(state="normal" if on else "disabled")
                except tk.TclError:
                    pass
                walk(c)
        walk(self.editor)
        for c in self.editor.winfo_children():
            if isinstance(c, ttk.Frame):
                for cc in c.winfo_children():
                    if isinstance(cc, ttk.Combobox):
                        cc.configure(state="readonly" if on else "disabled")
        if on:
            self.toggle_lyrics(save=False)

    # ============================================================== file
    def add_files(self):
        paths = filedialog.askopenfilenames(filetypes=AUDIO_TYPES)
        if not paths:
            return
        self.save_current()
        ratio = self.ratio_var.get()
        show = self.lyrics_on.get()
        errors, first_new = [], None
        for p in paths:
            try:
                title, artist, dur, cover = core.read_tags(p)
            except Exception as e:  # noqa: BLE001
                errors.append(f"{os.path.basename(p)} : {e}")
                continue
            tid = str(self.next_id)
            self.next_id += 1
            self.tracks[tid] = dict(path=p, title=title, artist=artist, duration=dur,
                                    cover=cover, lyrics="", lyr_info="Recherche…",
                                    show_lyrics=show, ratio=ratio, state="En attente",
                                    out=None)
            self.order.append(tid)
            self.tree.insert("", "end", iid=tid, values=self.row_values(tid))
            self.fetch_q.put((tid, cover is None, True))
            first_new = first_new or tid
        if first_new:
            self.tree.selection_set(first_new)
            self.tree.see(first_new)
        self.update_status_idle()
        if errors:
            messagebox.showwarning("Fichiers ignorés", "\n".join(errors))

    def remove_selected(self):
        if self.running:
            return
        for tid in self.tree.selection():
            self.tree.delete(tid)
            self.tracks.pop(tid, None)
            self.order.remove(tid)
        self.current = None
        self.load_editor(None)
        self.update_status_idle()

    def clear_all(self):
        if self.running:
            return
        for tid in list(self.order):
            self.tree.delete(tid)
        self.tracks.clear()
        self.order.clear()
        self.current = None
        self.load_editor(None)
        self.update_status_idle()

    def apply_to_all(self):
        self.save_current()
        if not self.current:
            return
        src = self.tracks[self.current]
        for tid in self.order:
            self.tracks[tid]["ratio"] = src["ratio"]
            self.tracks[tid]["show_lyrics"] = src["show_lyrics"]
            self.refresh_row(tid)

    def row_values(self, tid):
        t = self.tracks[tid]
        name = t["title"] + (f" — {t['artist']}" if t["artist"] else "")
        fmt = t["ratio"].split(" - ")[0]
        if not t["show_lyrics"]:
            lyr = "Désactivées"
        elif t["lyrics"].strip():
            lyr = "Synchronisées" if core.parse_lrc(t["lyrics"]) else "Texte simple"
        else:
            lyr = t["lyr_info"] or "Aucune"
        return (name, fmt, lyr, t["state"])

    def refresh_row(self, tid):
        if self.tree.exists(tid):
            self.tree.item(tid, values=self.row_values(tid))

    # ============================================================== éditeur
    def on_select(self, _evt=None):
        sel = self.tree.selection()
        tid = sel[0] if sel else None
        if tid == self.current:
            return
        self.save_current()
        self.current = tid
        self.load_editor(tid)

    def save_current(self):
        tid = self.current
        if not tid or tid not in self.tracks:
            return
        t = self.tracks[tid]
        t["title"] = self.title_var.get()
        t["artist"] = self.artist_var.get()
        t["ratio"] = self.ratio_var.get()
        t["show_lyrics"] = self.lyrics_on.get()
        t["lyrics"] = self.text.get("1.0", "end").strip()
        self.refresh_row(tid)

    def load_editor(self, tid):
        if not tid:
            self.title_var.set("")
            self.artist_var.set("")
            self.set_text("")
            self.thumb.config(image="", text="")
            self.lyr_status.config(text="")
            self.set_editor_enabled(False)
            return
        t = self.tracks[tid]
        self.set_editor_enabled(not self.running)
        self.title_var.set(t["title"])
        self.artist_var.set(t["artist"])
        self.ratio_var.set(t["ratio"])
        self.lyrics_on.set(t["show_lyrics"])
        self.set_text(t["lyrics"])
        self.show_thumb(t["cover"], searching=t.get("cover_searching"))
        self.toggle_lyrics(save=False)

    def set_text(self, txt):
        st = self.text.cget("state")
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        if txt:
            self.text.insert("1.0", txt)
        self.text.config(state=st)

    def show_thumb(self, cover, searching=False):
        if cover:
            try:
                im = Image.open(io.BytesIO(cover)).convert("RGB")
                im.thumbnail((80, 80))
                self._tk = ImageTk.PhotoImage(im)
                self.thumb.config(image=self._tk, text="")
                return
            except Exception:  # noqa: BLE001
                pass
        self.thumb.config(image="", text="Recherche\nde la\npochette…" if searching
                          else "(pas de\npochette)")

    def toggle_lyrics(self, save=True):
        on = self.lyrics_on.get()
        editable = on and not self.running and self.current is not None
        self.text.config(state="normal" if editable else "disabled",
                         foreground="black" if on else "gray")
        self.search_btn.config(state="normal" if editable else "disabled")
        if self.current:
            t = self.tracks[self.current]
            self.lyr_status.config(
                text="Sans paroles : pochette nette au centre, titre et artiste dessous."
                if not on else (t["lyr_info"] or ""))
        if save:
            self.save_current()

    def pick_cover(self):
        if not self.current:
            return
        p = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.jpeg *.png *.webp")])
        if p:
            with open(p, "rb") as f:
                self.tracks[self.current]["cover"] = f.read()
            self.show_thumb(self.tracks[self.current]["cover"])

    def refetch_cover(self):
        if not self.current:
            return
        self.save_current()
        self.tracks[self.current]["cover"] = None
        self.fetch_q.put((self.current, True, False))

    def refetch_lyrics(self):
        if not self.current:
            return
        self.save_current()
        self.tracks[self.current]["lyrics"] = ""
        self.set_text("")
        self.fetch_q.put((self.current, False, True))

    # ============================================================== recherches en ligne
    def fetch_worker(self):
        """Thread de fond : cherche pochettes et paroles une musique à la fois."""
        while True:
            tid, want_cover, want_lyrics = self.fetch_q.get()
            t = self.tracks.get(tid)
            if t is None:
                continue
            title, artist, dur = t["title"], t["artist"], t["duration"]
            if want_cover:
                t["cover_searching"] = True
                self.after(0, lambda i=tid: self.on_fetch_update(i))
                img = core.fetch_cover_online(title, artist)
                self.after(0, lambda i=tid, im=img: self.on_cover(i, im))
            if want_lyrics:
                t["lyr_info"] = "Recherche…"
                self.after(0, lambda i=tid: self.on_fetch_update(i))
                res = core.fetch_lrclib(title, artist, dur)
                self.after(0, lambda i=tid, r=res: self.on_lyrics(i, r))

    def on_fetch_update(self, tid):
        self.refresh_row(tid)
        if tid == self.current:
            t = self.tracks[tid]
            self.show_thumb(t["cover"], searching=t.get("cover_searching"))
            if t["show_lyrics"]:
                self.lyr_status.config(text=t["lyr_info"])

    def on_cover(self, tid, img):
        t = self.tracks.get(tid)
        if t is None:
            return
        t["cover_searching"] = False
        if img and t["cover"] is None:
            t["cover"] = img
        self.on_fetch_update(tid)

    def on_lyrics(self, tid, res):
        t = self.tracks.get(tid)
        if t is None:
            return
        if tid == self.current:
            self.save_current()
        if res and not t["lyrics"].strip():
            t["lyrics"] = res
            t["lyr_info"] = "Paroles synchronisées trouvées."
            if tid == self.current:
                self.set_text(res)
        elif not res:
            t["lyr_info"] = "Rien trouvé : colle les paroles ou laisse vide."
        else:
            t["lyr_info"] = ""
        self.on_fetch_update(tid)

    # ============================================================== génération
    def generate(self):
        self.save_current()
        if not self.order:
            messagebox.showinfo("Musiques", "Ajoute d'abord une ou plusieurs musiques.")
            return
        out_dir = filedialog.askdirectory(title="Dossier où enregistrer les vidéos")
        if not out_dir:
            return
        try:
            n = max(1, min(8, int(self.par_var.get())))
        except (tk.TclError, ValueError):
            n = 1

        used = set()
        jobs = []
        for tid in self.order:
            t = self.tracks[tid]
            base = os.path.splitext(os.path.basename(t["path"]))[0]
            out = os.path.join(out_dir, base + ".mp4")
            k = 2
            while out.lower() in used or os.path.exists(out):
                out = os.path.join(out_dir, f"{base} ({k}).mp4")
                k += 1
            used.add(out.lower())
            t["out"] = out
            t["state"] = "En attente"
            t["pct"] = 0
            self.refresh_row(tid)
            lyrics = core.lyrics_from_text(t["lyrics"], t["duration"]) if t["show_lyrics"] else []
            jobs.append((tid, dict(audio_path=t["path"], out_path=out, title=t["title"],
                                   artist=t["artist"], cover=t["cover"], lyrics=lyrics,
                                   duration=t["duration"], size=core.RATIOS[t["ratio"]],
                                   show_lyrics=t["show_lyrics"])))

        self.running = True
        self.set_editor_enabled(False)
        self.go.config(state="disabled")
        self.stop.config(state="normal")
        self.remaining = {tid for tid, _ in jobs}
        self.results = {"ok": 0, "err": [], "cancel": 0}
        self.manager = mp.Manager()
        self.msgq = self.manager.Queue()
        self.cancel_ev = self.manager.Event()
        self.pool = ProcessPoolExecutor(max_workers=n)
        self.futures = {}
        for tid, kw in jobs:
            self.futures[tid] = self.pool.submit(core.render_job, tid, kw, self.msgq, self.cancel_ev)
        self.status.config(text=f"{len(jobs)} vidéo(s), {n} en même temps…")
        self.after(200, self.poll)

    def poll(self):
        try:
            while True:
                kind, tid, val = self.msgq.get_nowait()
                t = self.tracks.get(tid)
                if t is None:
                    continue
                if kind == "progress":
                    t["pct"] = val
                    t["state"] = f"Rendu {val} %"
                elif kind == "done":
                    self.remaining.discard(tid)
                    if val:
                        t["state"], t["pct"] = "Terminé ✓", 100
                        self.results["ok"] += 1
                    else:
                        t["state"] = "Annulé"
                        self.results["cancel"] += 1
                elif kind == "error":
                    self.remaining.discard(tid)
                    t["state"] = "Erreur ✗"
                    self.results["err"].append(f"{t['title']} : {val[:300]}")
                self.refresh_row(tid)
        except queue.Empty:
            pass
        except (EOFError, OSError, BrokenPipeError):
            pass

        # processus mort sans message (crash) ou tâche annulée avant de démarrer
        for tid in list(self.remaining):
            f = self.futures[tid]
            if f.done():
                if f.cancelled():
                    self.tracks[tid]["state"] = "Annulé"
                    self.results["cancel"] += 1
                    self.remaining.discard(tid)
                    self.refresh_row(tid)
                elif f.exception() is not None:
                    self.tracks[tid]["state"] = "Erreur ✗"
                    self.results["err"].append(f"{self.tracks[tid]['title']} : {f.exception()}")
                    self.remaining.discard(tid)
                    self.refresh_row(tid)

        total = len(self.futures)
        pct = sum(self.tracks[t].get("pct", 0) for t in self.futures if t in self.tracks)
        self.bar.config(value=pct / max(1, total))
        done = total - len(self.remaining)
        if self.remaining:
            self.status.config(text=f"{done}/{total} terminée(s)…")
            self.after(200, self.poll)
        else:
            self.finish()

    def finish(self):
        self.pool.shutdown(wait=False, cancel_futures=True)
        try:
            self.manager.shutdown()
        except Exception:  # noqa: BLE001
            pass
        self.running = False
        self.go.config(state="normal")
        self.stop.config(state="disabled")
        self.set_editor_enabled(self.current is not None)
        if self.current:
            self.load_editor(self.current)
        r = self.results
        msg = f"{r['ok']} vidéo(s) créée(s)."
        if r["cancel"]:
            msg += f"\n{r['cancel']} annulée(s)."
        if r["err"]:
            msg += "\n\nErreurs :\n" + "\n".join(r["err"])
        self.status.config(text=msg.splitlines()[0])
        (messagebox.showwarning if r["err"] else messagebox.showinfo)("Lyric Video Maker", msg)

    def cancel(self):
        if not self.running:
            return
        self.cancel_ev.set()
        for f in self.futures.values():
            f.cancel()
        self.status.config(text="Annulation…")

    def update_status_idle(self):
        if not self.running:
            n = len(self.order)
            self.status.config(text=f"{n} musique(s) dans la liste." if n
                               else "Ajoute une ou plusieurs musiques.")


def selftest(out_dir):
    """Vérifie, sans fenêtre, que le rendu en parallèle marche dans l'exe (utilisé par la CI)."""
    import subprocess
    import imageio_ffmpeg
    os.makedirs(out_dir, exist_ok=True)
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    m = mp.Manager()
    q, ev = m.Queue(), m.Event()
    with ProcessPoolExecutor(max_workers=2) as pool:
        futs = []
        for i, size in enumerate(core.RATIOS.values()):
            src = os.path.join(out_dir, f"son{i}.mp3")
            subprocess.run([ff, "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                            "sine=duration=3", src], check=True)
            t, a, d, cov = core.read_tags(src)
            kw = dict(audio_path=src, out_path=os.path.join(out_dir, f"video{i}.mp4"),
                      title=t, artist=a, cover=cov, duration=d, size=size,
                      lyrics=core.lyrics_from_text("[00:00.50]Été\n[00:02.00]Fin", d),
                      show_lyrics=bool(i % 2))
            futs.append(pool.submit(core.render_job, str(i), kw, q, ev))
        for f in futs:
            f.result()
    res = []
    while not q.empty():
        msg = q.get()
        if msg[0] != "progress":
            res.append(msg)
    ok = len(res) == len(core.RATIOS) and all(r[0] == "done" and r[2] for r in res)
    with open(os.path.join(out_dir, "selftest.txt"), "w", encoding="utf-8") as f:
        f.write(("OK" if ok else "ECHEC") + "\n" + repr(res))


if __name__ == "__main__":
    mp.freeze_support()   # indispensable pour l'exe PyInstaller
    import sys
    if len(sys.argv) == 3 and sys.argv[1] == "--selftest":
        selftest(sys.argv[2])
    else:
        App().mainloop()
