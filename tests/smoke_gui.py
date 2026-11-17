"""Test de l'interface : ajoute 3 musiques et les rend en parallèle via la vraie fenêtre."""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import imageio_ffmpeg  # noqa: E402

import app  # noqa: E402

if __name__ == "__main__":
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    work = os.path.abspath("gui_test")
    os.makedirs(os.path.join(work, "out"), exist_ok=True)
    files = []
    for i, f in enumerate((440, 550, 660)):
        p = os.path.join(work, f"son{i}.mp3")
        subprocess.run([ff, "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                        f"sine=frequency={f}:duration=4", "-metadata", f"title=Son {i}",
                        p], check=True)
        files.append(p)

    msgs = []
    app.filedialog.askopenfilenames = lambda **k: tuple(files)
    app.filedialog.askdirectory = lambda **k: os.path.join(work, "out")
    app.messagebox.showinfo = lambda *a, **k: msgs.append(("info",) + a)
    app.messagebox.showwarning = lambda *a, **k: msgs.append(("warn",) + a)

    w = app.App()
    w.add_files()
    assert len(w.order) == 3, w.order
    # 2e musique : sans paroles, format vertical
    w.tree.selection_set(w.order[1])
    w.on_select()
    w.lyrics_on.set(False)
    w.ratio_var.set(list(app.core.RATIOS)[1])
    w.toggle_lyrics()
    w.par_var.set(2)
    w.generate()

    def check():
        if w.running:
            w.after(300, check)
        else:
            w.destroy()
    w.after(300, check)
    w.mainloop()

    print(msgs)
    outs = sorted(os.listdir(os.path.join(work, "out")))
    print(outs)
    assert outs == ["son0.mp4", "son1.mp4", "son2.mp4"], outs
    assert msgs and msgs[-1][0] == "info", msgs
    print("interface OK")
