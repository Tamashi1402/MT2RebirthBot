"""
pick_region.py — screenshot-based region picker (like Snipping Tool).

Usage:
    python tools/pick_region.py

Instructions:
    1. Switch to the game window FIRST, then run this
    2. Screen freezes (screenshot shown) — drag to select your region
    3. Release — coordinates printed + saved to tools/region_result.txt
    4. R = re-select on same screenshot, Q/Esc = quit
"""

import tkinter as tk
from PIL import ImageGrab, ImageTk
import os

result_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "region_result.txt")


class RegionPicker:
    def __init__(self):
        # Grab the full screen BEFORE showing the window
        self.screenshot = ImageGrab.grab()
        sw, sh = self.screenshot.size

        self.root = tk.Tk()
        self.root.overrideredirect(True)          # no title bar
        self.root.attributes("-topmost", True)
        self.root.geometry(f"{sw}x{sh}+0+0")
        self.root.config(cursor="crosshair")

        self.canvas = tk.Canvas(self.root, width=sw, height=sh,
                                highlightthickness=0, bd=0)
        self.canvas.pack()

        # Display screenshot as background
        self.bg_img = ImageTk.PhotoImage(self.screenshot)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.bg_img)

        # Dim overlay
        self.canvas.create_rectangle(0, 0, sw, sh,
                                     fill="black", stipple="gray50",
                                     outline="")

        # Instructions
        self.canvas.create_text(
            sw // 2, 28,
            text="Drag to select region  |  R = redo  |  Q / Esc = quit",
            fill="white", font=("Arial", 15, "bold"),
            tags="hint"
        )

        self.start_x = self.start_y = 0
        self.rect_id  = None
        self.coord_id = None
        self.preview_id = None

        self.canvas.bind("<ButtonPress-1>",   self.on_press)
        self.canvas.bind("<B1-Motion>",       self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        self.root.bind("q",        lambda e: self.root.destroy())
        self.root.bind("r",        self.on_reset)

        self.root.mainloop()

    # ── clear selection UI ────────────────────────────────────────
    def clear_selection(self):
        for tag in (self.rect_id, self.coord_id, self.preview_id):
            if tag:
                self.canvas.delete(tag)
        self.rect_id = self.coord_id = self.preview_id = None

    # ── mouse events ─────────────────────────────────────────────
    def on_press(self, event):
        self.start_x, self.start_y = event.x, event.y
        self.clear_selection()

    def on_drag(self, event):
        self.clear_selection()
        x1, y1 = self.start_x, self.start_y
        x2, y2 = event.x, event.y
        self.rect_id = self.canvas.create_rectangle(
            x1, y1, x2, y2,
            outline="red", width=2
        )
        # Show live size
        w, h = abs(x2-x1), abs(y2-y1)
        self.coord_id = self.canvas.create_text(
            (x1+x2)//2, (y1+y2)//2,
            text=f"{w} × {h}",
            fill="yellow", font=("Arial", 12, "bold")
        )

    def on_release(self, event):
        x1 = min(self.start_x, event.x)
        y1 = min(self.start_y, event.y)
        x2 = max(self.start_x, event.x)
        y2 = max(self.start_y, event.y)
        w, h = x2 - x1, y2 - y1

        if w < 3 or h < 3:
            return  # accidental click, ignore

        py_tuple   = f"({x1}, {y1}, {x2}, {y2})"
        cs_rect    = f"new Rectangle({x1}, {y1}, {w}, {h})"

        # Print to console
        print("\n" + "="*52)
        print(f"  Python tuple : {py_tuple}")
        print(f"  C# Rectangle : {cs_rect}")
        print(f"  Size         : {w} x {h} px")
        print("="*52)
        print("  R = re-select  |  Q/Esc = quit\n")

        # Save to file
        with open(result_file, "w") as f:
            f.write(f"python = {py_tuple}\n")
            f.write(f"csharp = {cs_rect}\n")
            f.write(f"size   = {w} x {h}\n")

        # Show result on canvas
        self.clear_selection()
        self.rect_id = self.canvas.create_rectangle(
            x1, y1, x2, y2,
            outline="lime", width=3
        )
        label = f"{py_tuple}   {w}×{h}px"
        self.coord_id = self.canvas.create_text(
            (x1+x2)//2, y1 - 12 if y1 > 30 else y2 + 12,
            text=label,
            fill="lime", font=("Arial", 12, "bold")
        )

    def on_reset(self, event):
        self.clear_selection()
        # Re-draw background + hint
        sw, sh = self.screenshot.size
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.bg_img)
        self.canvas.create_rectangle(0, 0, sw, sh,
                                     fill="black", stipple="gray50", outline="")
        self.canvas.create_text(
            sw // 2, 28,
            text="Drag to select region  |  R = redo  |  Q / Esc = quit",
            fill="white", font=("Arial", 15, "bold")
        )


if __name__ == "__main__":
    print("Taking screenshot... switch to game window NOW (you have 2 seconds)")
    import time; time.sleep(2)
    print("Capturing... drag to select your region.\n")
    RegionPicker()
