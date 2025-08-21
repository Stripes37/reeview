import tkinter as tk
from models import Album, Stage
from storage import (
    load_db,
    save_db,
    generate_id,
    upsert_album,
    remove_album,
    find_album,
)
from utils.time import now_iso

DB_PATH = "data/database.json"


class TrackerGUI:
    def __init__(self, master: tk.Tk) -> None:
        self.master = master
        master.title("Album Review Tracker")

        self.drag_data = None
        self.listboxes: dict[str, tk.Listbox] = {}

        board = tk.Frame(master)
        board.pack(fill=tk.BOTH, expand=True)

        for stage in Stage:
            col = tk.Frame(board)
            col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            tk.Label(col, text=stage.value).pack()
            lb = tk.Listbox(col, width=25)
            lb.pack(fill=tk.BOTH, expand=True)
            lb.stage = stage  # type: ignore[attr-defined]
            self.listboxes[stage.value] = lb
            self._make_draggable(lb)

        btn_frame = tk.Frame(master)
        btn_frame.pack(fill=tk.X)
        tk.Button(btn_frame, text="Refresh", command=self.refresh).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="Add Album", command=self.open_add_dialog).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="Remove", command=self.remove_selected).pack(side=tk.LEFT)

        self.refresh()

    def _make_draggable(self, lb: tk.Listbox) -> None:
        lb.bind("<ButtonPress-1>", self.on_start_drag)
        lb.bind("<B1-Motion>", self.on_drag)
        lb.bind("<ButtonRelease-1>", self.on_drop)

    def on_start_drag(self, event: tk.Event) -> None:
        widget: tk.Listbox = event.widget  # type: ignore[assignment]
        index = widget.nearest(event.y)
        if index < 0:
            return
        self.drag_data = {
            "widget": widget,
            "index": index,
            "item": widget.get(index),
        }

    def on_drag(self, event: tk.Event) -> None:
        # No visual feedback needed for simple drag operation
        pass

    def on_drop(self, event: tk.Event) -> None:
        if not self.drag_data:
            return
        target = event.widget.winfo_containing(event.x_root, event.y_root)
        source_widget: tk.Listbox = self.drag_data["widget"]
        item = self.drag_data["item"]
        source_widget.delete(self.drag_data["index"])
        if isinstance(target, tk.Listbox) and hasattr(target, "stage"):
            target.insert(tk.END, item)
            self.set_stage(item, target.stage)
        else:
            # revert if dropped outside
            source_widget.insert(self.drag_data["index"], item)
        self.drag_data = None

    def set_stage(self, album_id: str, stage: Stage) -> None:
        db = load_db(DB_PATH)
        album = find_album(db, album_id)
        if not album:
            return
        status = album.setdefault("status", {"stage": Stage.IDEATION.value, "history": []})
        from_stage = status.get("stage", Stage.IDEATION.value)
        status.setdefault("history", []).append(
            {
                "from_stage": from_stage,
                "to_stage": stage.value,
                "at": now_iso(),
                "note": "",
            }
        )
        status["stage"] = stage.value
        save_db(DB_PATH, db)

    def refresh(self) -> None:
        db = load_db(DB_PATH)
        for lb in self.listboxes.values():
            lb.delete(0, tk.END)
        for album in db.get("albums", []):
            stage = album.get("status", {}).get("stage", Stage.IDEATION.value)
            lb = self.listboxes.get(stage)
            if lb:
                lb.insert(tk.END, album["id"])

    def remove_selected(self) -> None:
        for lb in self.listboxes.values():
            sel = lb.curselection()
            if sel:
                album_id = lb.get(sel[0])
                db = load_db(DB_PATH)
                if remove_album(db, album_id):
                    save_db(DB_PATH, db)
                self.refresh()
                return

    def open_add_dialog(self) -> None:
        win = tk.Toplevel(self.master)
        win.title("Add Album")

        labels = ["Artist", "Album", "Release Date"]
        vars: dict[str, tk.StringVar] = {}
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
