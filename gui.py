import tkinter as tk
from models import Album
from storage import load_db, save_db, generate_id, upsert_album
from utils.time import now_iso

DB_PATH = "data/database.json"

class TrackerGUI:
    def __init__(self, master: tk.Tk) -> None:
        self.master = master
        master.title("Album Review Tracker")

        self.listbox = tk.Listbox(master, width=50)
        self.listbox.pack(fill=tk.BOTH, expand=True)

        btn_frame = tk.Frame(master)
        btn_frame.pack(fill=tk.X)
        tk.Button(btn_frame, text="Refresh", command=self.refresh).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="Add Album", command=self.open_add_dialog).pack(side=tk.LEFT)

        self.refresh()

    def refresh(self) -> None:
        db = load_db(DB_PATH)
        self.listbox.delete(0, tk.END)
        for album in db.get("albums", []):
            self.listbox.insert(tk.END, album["id"])

    def open_add_dialog(self) -> None:
        win = tk.Toplevel(self.master)
        win.title("Add Album")

        labels = ["Artist", "Album", "Release Date"]
        vars = {}
        for i, label in enumerate(labels):
            tk.Label(win, text=label).grid(row=i, column=0, sticky=tk.W)
            var = tk.StringVar()
            tk.Entry(win, textvariable=var).grid(row=i, column=1)
            vars[label.lower().replace(" ", "_")] = var

        def save() -> None:
            artist = vars["artist"].get().strip()
            album = vars["album"].get().strip()
            release_date = vars["release_date"].get().strip()
            if not artist or not album:
                return
            db = load_db(DB_PATH)
            album_id = generate_id(release_date or "0000-00-00", artist, album)
            new_album = Album(
                id=album_id,
                artist=artist,
                album=album,
                release_date=release_date or None,
                audit={"created_at": now_iso(), "updated_at": now_iso(), "updated_by": "gui"},
            )
            upsert_album(db, new_album.to_dict())
            save_db(DB_PATH, db)
            win.destroy()
            self.refresh()

        tk.Button(win, text="Save", command=save).grid(row=len(labels), column=0, columnspan=2)


def run() -> None:
    root = tk.Tk()
    TrackerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    run()
