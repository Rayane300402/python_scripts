"""
Android Notification Previewer (Desktop)
---------------------------------------
A simple Tkinter app that lets you enter:
- Title
- Body
- Image URL

Then previews an "Android-style" notification in:
- Minimized (collapsed)
- Expanded (big picture style)

Dependencies:
    pip install pillow requests

Run:
    python notif_previewer.py
"""

import io
import textwrap
import tkinter as tk
from tkinter import ttk, messagebox
import os
from urllib.parse import urlparse


try:
    import requests
    from PIL import Image, ImageTk
    try:
        import cairosvg
    except Exception:
        cairosvg = None
except Exception as e:
    raise SystemExit(
        "Missing dependencies. Install with:\n"
        "  pip install pillow requests cairosvg\n\n"
        f"Original error: {e}"
    )



# ----------------------------
# Helpers
# ----------------------------

def _looks_like_svg(url: str, content_type: str | None) -> bool:
    u = (url or "").lower()
    if content_type and "svg" in content_type.lower():
        return True
    if u.endswith(".svg"):
        return True
    # Some CDNs don’t end with .svg; check path
    try:
        path = urlparse(url).path.lower()
        if path.endswith(".svg"):
            return True
    except Exception:
        pass
    return False


def fetch_image(url: str, timeout=10) -> Image.Image | None:
    """Fetch image from URL (PNG/JPG/WebP, plus SVG if cairosvg installed)."""
    url = (url or "").strip()
    if not url:
        return None
    try:
        headers = {"User-Agent": "NotifPreviewer/1.0 (requests)"}
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()

        ctype = resp.headers.get("Content-Type", "")
        data = resp.content

        # Handle SVG via cairosvg -> PNG bytes -> Pillow
        if _looks_like_svg(url, ctype):
            if cairosvg is None:
                # SVG support not installed
                return None
            try:
                png_bytes = cairosvg.svg2png(bytestring=data, output_width=1200)
                img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
                return img
            except Exception:
                return None

        # Normal raster images
        img = Image.open(io.BytesIO(data)).convert("RGB")
        return img

    except Exception:
        return None



def fit_cover(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Resize/crop image to cover the target box (like centerCrop)."""
    if img is None:
        return None
    iw, ih = img.size
    if iw <= 0 or ih <= 0:
        return None

    scale = max(target_w / iw, target_h / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    resized = img.resize((nw, nh), Image.LANCZOS)

    left = max(0, (nw - target_w) // 2)
    top = max(0, (nh - target_h) // 2)
    return resized.crop((left, top, left + target_w, top + target_h))


def ellipsize(text: str, max_chars: int) -> str:
    t = (text or "").replace("\n", " ").strip()
    if len(t) <= max_chars:
        return t
    if max_chars <= 1:
        return "…"
    return t[: max_chars - 1].rstrip() + "…"


# ----------------------------
# "Notification" rendering
# ----------------------------

class NotificationPreview(ttk.Frame):
    """
    A stylized preview that approximates Android notifications:
    - Collapsed: app icon + title + 1–2 lines
    - Expanded: includes a big picture area
    """

    def __init__(self, master, mode: str, **kwargs):
        super().__init__(master, **kwargs)
        self.mode = mode  # "collapsed" or "expanded"
        self._photo_big = None  # keep references
        self._photo_icon = None

        # Styling-ish
        self.configure(padding=12)

        # Outer "card"
        self.card = tk.Frame(self, bg="#1f1f1f", bd=0, highlightthickness=1, highlightbackground="#303030")
        self.card.pack(fill="both", expand=True)

        # Header row
        self.header = tk.Frame(self.card, bg="#1f1f1f")
        self.header.pack(fill="x", padx=12, pady=(12, 6))

        self.icon_canvas = tk.Canvas(self.header, width=36, height=36, bg="#1f1f1f", highlightthickness=0)
        self.icon_canvas.pack(side="left")

        self.head_text = tk.Frame(self.header, bg="#1f1f1f")
        self.head_text.pack(side="left", fill="x", expand=True, padx=(10, 0))

        self.app_line = tk.Label(self.head_text, text="App Title", bg="#1f1f1f", fg="#cfcfcf",
                                 font=("Segoe UI", 9))
        self.app_line.pack(anchor="w")

        self.title_label = tk.Label(self.head_text, text="Title", bg="#1f1f1f", fg="#ffffff",
                                    font=("Segoe UI", 11, "bold"))
        self.title_label.pack(anchor="w", pady=(2, 0))

        # Body
        self.body_label = tk.Label(self.card, text="Body", bg="#1f1f1f", fg="#e6e6e6",
                                   font=("Segoe UI", 10), justify="left", anchor="w")
        self.body_label.pack(fill="x", padx=12, pady=(0, 10))

        # Big picture area for expanded
        self.big_frame = tk.Frame(self.card, bg="#1f1f1f")
        if self.mode == "expanded":
            self.big_frame.pack(fill="x", padx=12, pady=(0, 12))

        self.big_canvas = tk.Canvas(self.big_frame, width=360, height=180,
                                    bg="#2a2a2a", highlightthickness=1, highlightbackground="#303030")
        if self.mode == "expanded":
            self.big_canvas.pack(fill="x")

        # Footer (buttons-ish)
        self.footer = tk.Frame(self.card, bg="#1f1f1f")
        self.footer.pack(fill="x", padx=12, pady=(0, 12))
        self.footer_label = tk.Label(self.footer, text="Reply   •   Mark as read   •   Settings",
                                     bg="#1f1f1f", fg="#a9a9a9", font=("Segoe UI", 9))
        self.footer_label.pack(anchor="w")

        self._draw_default_icon()

    def _draw_default_icon(self):
        self.icon_canvas.delete("all")

        logo_path = "logo.png"  # must be next to your .py, or change path
        if os.path.exists(logo_path):
            try:
                img = Image.open(logo_path).convert("RGBA")
                img = img.resize((30, 30), Image.LANCZOS)
                self._photo_icon = ImageTk.PhotoImage(img)
                # draw a subtle rounded backing
                self.icon_canvas.create_oval(3, 3, 33, 33, fill="#2b2b2b", outline="")
                self.icon_canvas.create_image(18, 18, image=self._photo_icon, anchor="center")
                return
            except Exception:
                pass

        # fallback if logo.png missing/broken
        self.icon_canvas.create_oval(3, 3, 33, 33, fill="#4a90e2", outline="")
        self.icon_canvas.create_text(18, 18, text="A", fill="white", font=("Segoe UI", 14, "bold"))


    def set_content(self, title: str, body: str, img: Image.Image | None):
        # Collapsed behavior: shorter body (1–2 lines)
        # Expanded behavior: more body, plus big image
        title = (title or "").strip()
        body = (body or "").strip()

        if self.mode == "collapsed":
            display_title = ellipsize(title if title else "Title", 38)
            # approximate 2 lines ~ 90 chars
            display_body = ellipsize(body if body else "Body", 92)
        else:
            display_title = ellipsize(title if title else "Title", 52)
            # approx 4 lines
            display_body = ellipsize(body if body else "Body", 220)

        self.title_label.config(text=display_title)
        # wrap to fit width a bit; Tk wraps by pixels if wraplength set
        self.body_label.config(text=display_body, wraplength=420)

        # Expanded big image
        if self.mode == "expanded":
            self.big_canvas.delete("all")
            w = int(self.big_canvas.winfo_width() or 360)
            h = int(self.big_canvas.winfo_height() or 180)

            if img is None:
                # placeholder
                self.big_canvas.create_rectangle(0, 0, w, h, fill="#2a2a2a", outline="#303030")
                self.big_canvas.create_text(w // 2, h // 2, text="(No image / couldn't load)",
                                            fill="#bdbdbd", font=("Segoe UI", 10))
                self._photo_big = None
            else:
                fitted = fit_cover(img, w, h)
                self._photo_big = ImageTk.PhotoImage(fitted)
                self.big_canvas.create_image(0, 0, image=self._photo_big, anchor="nw")


        # Also optionally tint icon based on image average (fun but optional)
        # Keeping it simple: leave icon constant.


# ----------------------------
# App
# ----------------------------

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Android Notification Previewer")
        self.geometry("980x620")
        self.minsize(920, 560)

        self._last_img = None

        # Layout
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(0, weight=1)

        left = ttk.Frame(self, padding=16)
        left.grid(row=0, column=0, sticky="nsew")
        left.columnconfigure(0, weight=1)

        right = ttk.Frame(self, padding=16)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        # Inputs
        ttk.Label(left, text="Title").grid(row=0, column=0, sticky="w")
        self.title_var = tk.StringVar()
        self.title_entry = ttk.Entry(left, textvariable=self.title_var)
        self.title_entry.grid(row=1, column=0, sticky="ew", pady=(4, 12))

        ttk.Label(left, text="Body").grid(row=2, column=0, sticky="w")
        self.body_text = tk.Text(left, height=10, wrap="word")
        self.body_text.grid(row=3, column=0, sticky="nsew", pady=(4, 12))
        left.rowconfigure(3, weight=1)

        ttk.Label(left, text="Image URL").grid(row=4, column=0, sticky="w")
        self.img_var = tk.StringVar()
        self.img_entry = ttk.Entry(left, textvariable=self.img_var)
        self.img_entry.grid(row=5, column=0, sticky="ew", pady=(4, 12))

        btn_row = ttk.Frame(left)
        btn_row.grid(row=6, column=0, sticky="ew")
        btn_row.columnconfigure(0, weight=1)
        btn_row.columnconfigure(1, weight=1)

        self.gen_btn = ttk.Button(btn_row, text="Generate Preview", command=self.generate)
        self.gen_btn.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.clear_btn = ttk.Button(btn_row, text="Clear", command=self.clear)
        self.clear_btn.grid(row=0, column=1, sticky="ew", padx=(6, 0))

        # Right side: previews
        ttk.Label(right, text="Preview").grid(row=0, column=0, sticky="w", pady=(0, 10))

        previews = ttk.Frame(right)
        previews.grid(row=1, column=0, sticky="nsew")
        previews.columnconfigure(0, weight=1)
        previews.columnconfigure(1, weight=1)
        previews.rowconfigure(1, weight=1)

        ttk.Label(previews, text="Minimized (Collapsed)").grid(row=0, column=0, sticky="w", pady=(0, 6))
        ttk.Label(previews, text="Maximized (Expanded / Big picture)").grid(row=0, column=1, sticky="w", pady=(0, 6))

        self.collapsed = NotificationPreview(previews, mode="collapsed")
        self.collapsed.grid(row=1, column=0, sticky="nsew", padx=(0, 10))

        self.expanded = NotificationPreview(previews, mode="expanded")
        self.expanded.grid(row=1, column=1, sticky="nsew", padx=(10, 0))

        # Seed initial
        self.title_var.set("Title")
        self.body_text.insert("1.0", "Insert text")
        self.img_var.set("")

        self.after(50, self.generate)  # initial render after layout

    def clear(self):
        self.title_var.set("")
        self.body_text.delete("1.0", "end")
        self.img_var.set("")
        self._last_img = None
        self.collapsed.set_content("", "", None)
        self.expanded.set_content("", "", None)

    def generate(self):
        title = self.title_var.get()
        body = self.body_text.get("1.0", "end").strip()
        url = self.img_var.get().strip()

        img = None
        if url:
            # Fetch on UI thread for simplicity; for huge images/slow net, you could thread it.
            img = fetch_image(url)
            if img is None:
                messagebox.showwarning(
                    "Image load failed",
                    "Couldn't load the image from that URL.\n"
                    "Preview will show a placeholder."
                )

        self._last_img = img
        self.collapsed.set_content(title, body, img)
        self.expanded.set_content(title, body, img)


if __name__ == "__main__":
    # Use ttk theme if available
    app = App()
    try:
        style = ttk.Style()
        # Choose something common; falls back harmlessly
        if "clam" in style.theme_names():
            style.theme_use("clam")
    except Exception:
        pass
    app.mainloop()
