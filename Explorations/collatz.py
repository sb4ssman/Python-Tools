# -*- coding: utf-8 -*-
"""
collatz.py
Author : Thomas Miller (sb4ssman)
Started: 2026-04-16

Interactive explorer for the Collatz conjecture (3n+1 problem).
Plots one or more sequences simultaneously on a zoomable, log-scale canvas.
Each run is assigned a perceptually distinct color via golden-ratio HSV spread.
The legend is interactive — click any entry to show/hide that run.
A hover databox shows per-step values across all visible runs.

Run standalone:
    python collatz.py
"""

import colorsys
import math
import sys
import time
import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont


def _run_color(idx):
    """Golden-ratio HSV spread — adjacent indices get maximally different hues."""
    h = (idx * 0.618033988749895) % 1.0
    r, g, b = colorsys.hsv_to_rgb(h, 0.72, 0.95)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


def collatz_path(n):
    path = [n]
    while n != 1:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        path.append(n)
    return path


def build_display_path(path):
    """Append one extra 4→2→1 cycle so the terminal loop plays twice."""
    if len(path) >= 3 and path[-3] == 4 and path[-2] == 2 and path[-1] == 1:
        return path + [4, 2, 1], len(path) - 3
    return path, len(path)


def path_stats(path):
    odd_steps = sum(1 for v in path[:-1] if v % 2 == 1)
    max_down = cur_down = 0
    for i in range(1, len(path)):
        if path[i] < path[i - 1]:
            cur_down += 1
        else:
            cur_down = 0
        max_down = max(max_down, cur_down)
    return odd_steps, max_down


class CollatzApp(tk.Tk):
    LINE_COLOR     = "#4a9eff"
    TERMINAL_COLOR = "#ffaa00"
    DOT_COLOR      = "#ff6b35"
    TERMINAL_DOT   = "#ffdd55"
    GRID_COLOR     = "#333333"
    GRID_MINOR     = "#2b2b2b"
    AXIS_COLOR     = "#555555"
    BG             = "#1e1e1e"
    CANVAS_BG      = "#252526"

    def __init__(self):
        super().__init__()
        self.title("Collatz Explorer (3n+1)")
        self.configure(bg=self.CANVAS_BG)
        self.resizable(True, True)

        self._path         = []
        self._display_path = []
        self._terminal_idx = 0
        self._anim_index   = 0
        self._anim_job     = None
        self._screen_pts   = []
        self._plot_geom    = {}
        self._zoom         = None
        self._drag_start   = None
        self._drag_rect    = None
        self._multi_paths  = []
        self._hidden_runs  = set()   # indices into _multi_paths that are hidden
        self._legend_items = []      # [(x1,y1,x2,y2,run_idx), ...] for click detection

        self._show_dots  = tk.BooleanVar(value=True)
        self._log_scale  = tk.BooleanVar(value=True)
        self._databox_on = tk.BooleanVar(value=True)

        self._font  = tkfont.Font(family="Segoe UI", size=8)
        self._font9 = tkfont.Font(family="Segoe UI", size=9)

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        self._cancel_anim()
        self.destroy()

    # ----------------------------------------------------------------- UI

    def _build_ui(self):
        sty = ttk.Style(self)
        sty.theme_use("clam")
        sty.configure(".",              background=self.CANVAS_BG, foreground="#cccccc", font=("Segoe UI", 10))
        sty.configure("TEntry",         fieldbackground="#3c3c3c", foreground="#cccccc", insertcolor="#cccccc")
        sty.configure("TButton",        background="#3c3c3c", foreground="#cccccc", padding=(8, 4))
        sty.map("TButton",              background=[("active", "#505050")])
        sty.configure("TLabel",         background=self.CANVAS_BG, foreground="#cccccc")
        sty.configure("TCheckbutton",   background=self.CANVAS_BG, foreground="#cccccc",
                                        indicatorcolor="#3c3c3c", indicatorrelief="flat")
        sty.map("TCheckbutton",         background=[("active", self.CANVAS_BG)],
                                        foreground=[("active", "#ffffff")],
                                        indicatorcolor=[("selected", "#4a9eff"),
                                                        ("active",   "#555555")])
        sty.configure("TScrollbar",     background="#3c3c3c", troughcolor="#1e1e1e",
                                        arrowcolor="#888888", borderwidth=0, relief="flat")
        sty.map("TScrollbar",           background=[("active", "#555555"), ("pressed", "#666666")])
        sty.configure("Accent.TButton", background="#0e639c", foreground="white")
        sty.map("Accent.TButton",       background=[("active", "#1177bb")])

        r1 = ttk.Frame(self, padding=(8, 6, 8, 0))
        r1.pack(fill="x")

        # ── Column 3 packed first so col2 can expand into remaining space ──
        col3 = ttk.Frame(r1)
        col3.pack(side="right", anchor="n", padx=(8, 0))

        cb = ttk.Frame(col3)
        cb.pack(anchor="w")
        ttk.Checkbutton(cb, text="Points",    variable=self._show_dots,  command=self._redraw).grid(row=0, column=0, sticky="w", padx=(0, 10), pady=1)
        ttk.Checkbutton(cb, text="Log scale", variable=self._log_scale,  command=self._redraw).grid(row=0, column=1, sticky="w", pady=1)
        ttk.Checkbutton(cb, text="Databox",   variable=self._databox_on, command=self._redraw).grid(row=1, column=0, sticky="w", padx=(0, 10), pady=1)

        btn_row = ttk.Frame(col3)
        btn_row.pack(side="bottom", anchor="e")
        ttk.Button(btn_row, text="Data View", command=self._open_data_view).pack(side="left", padx=(0, 4))
        self._zoom_btn = ttk.Button(btn_row, text="Zoom out", command=self._zoom_reset, state="disabled")
        self._zoom_btn.pack(side="left")

        # ── Column 1: label row + text box ──
        col1 = ttk.Frame(r1)
        col1.pack(side="left", anchor="n")

        hdr = ttk.Frame(col1)
        hdr.pack(fill="x")
        ttk.Label(hdr, text="Starting numbers:").pack(side="left")
        clear_lbl = tk.Label(hdr, text="Clear", fg="#4a9eff", bg=self.CANVAS_BG,
                             font=("Segoe UI", 8), cursor="hand2")
        clear_lbl.pack(side="right")
        clear_lbl.bind("<Button-1>", lambda _: self._clear_entry())
        clear_lbl.bind("<Enter>",    lambda _: clear_lbl.config(fg="#7bbfff"))
        clear_lbl.bind("<Leave>",    lambda _: clear_lbl.config(fg="#4a9eff"))

        txt_frame = tk.Frame(col1, bg="#555555", highlightthickness=1,
                             highlightbackground="#555555")
        txt_frame.pack(anchor="w")
        xscroll = ttk.Scrollbar(txt_frame, orient="horizontal")
        yscroll = ttk.Scrollbar(txt_frame, orient="vertical")
        self._entry = tk.Text(
            txt_frame, width=24, height=3, wrap="none",
            bg="#3c3c3c", fg="#cccccc", insertbackground="#cccccc",
            selectbackground="#0e639c", relief="flat", bd=1,
            font=("Segoe UI", 10),
            xscrollcommand=xscroll.set, yscrollcommand=yscroll.set,
        )
        xscroll.config(command=self._entry.xview)
        yscroll.config(command=self._entry.yview)
        self._entry.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        self._entry.tag_config("invalid_line", foreground="#ff6b6b")
        self._entry.insert("1.0", "27")
        self._entry.bind("<Control-Return>", lambda _: self._plot())
        self._entry.bind("<KeyRelease>",     self._validate_entry)

        # ── Column 2: buttons / title / stats — expands to fill remaining space ──
        col2 = ttk.Frame(r1)
        col2.pack(side="left", padx=(8, 0), anchor="n", fill="x", expand=True)

        btn_frame = ttk.Frame(col2)
        btn_frame.pack(anchor="w")
        ttk.Button(btn_frame, text="Plot",    style="Accent.TButton", command=self._plot).pack(side="left", padx=(0, 2))
        ttk.Button(btn_frame, text="Animate", command=self._animate).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Step →",  command=self._step).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Reset",   command=self._reset).pack(side="left", padx=2)

        title_border = tk.Frame(col2, highlightthickness=1,
                                highlightbackground="#4a9eff", bg=self.CANVAS_BG)
        title_border.pack(fill="x", pady=(4, 0))
        ttk.Label(title_border, text="Collatz Explorer (n = 3n+1|n-odd ; n/2|n-even)",
                  font=("Segoe UI", 11, "bold"), foreground="#4a9eff").pack(padx=6, pady=2)

        # Stats: row A always visible; row B shows multi-path summary
        stats_frame = ttk.Frame(col2)
        stats_frame.pack(anchor="w", pady=(2, 0))

        row_b = ttk.Frame(stats_frame)
        row_b.pack(anchor="w")
        _HINT = "Ctrl+Enter to plot  ·  drag to zoom  ·  click legend to show/hide"
        self._lbl_multi = ttk.Label(row_b, text=_HINT, foreground="#4a4a4a")
        self._lbl_multi.pack(side="left")

        # ── Status bar ──
        sbar = tk.Frame(self, bg="#2a2a2a", height=20)
        sbar.pack(side="bottom", fill="x")
        self._lbl_current = tk.Label(sbar, text="Ready", fg="#888888", bg="#2a2a2a",
                                     font=("Segoe UI", 9), anchor="w")
        self._lbl_current.pack(side="left", padx=(8, 0))
        self._lbl_memory = tk.Label(sbar, text="Mem: —", fg="#666666", bg="#2a2a2a",
                                    font=("Segoe UI", 9))
        self._lbl_memory.pack(side="right", padx=(0, 10))
        self._lbl_calc_time = tk.Label(sbar, text="Calc: —", fg="#666666", bg="#2a2a2a",
                                       font=("Segoe UI", 9))
        self._lbl_calc_time.pack(side="right", padx=(0, 6))

        # ── Canvas ──
        self._canvas = tk.Canvas(self, bg=self.CANVAS_BG, highlightthickness=0, width=820, height=420)
        self._canvas.pack(fill="both", expand=True, padx=8, pady=0)
        self._canvas.bind("<Configure>",       lambda _: self._redraw())
        self._canvas.bind("<Motion>",          self._on_mouse_move)
        self._canvas.bind("<Leave>",           self._on_mouse_leave)
        self._canvas.bind("<ButtonPress-1>",   self._on_drag_start)
        self._canvas.bind("<B1-Motion>",       self._on_drag_move)
        self._canvas.bind("<ButtonRelease-1>", self._on_drag_end)
        self._canvas.bind("<Double-Button-1>", lambda _: self._zoom_reset())

    # ------------------------------------------------------------------ logic

    def _clear_entry(self):
        self._entry.delete("1.0", "end")

    def _get_entry_text(self):
        return self._entry.get("1.0", "end-1c")

    def _validate_entry(self, *_):
        t = self._entry
        t.tag_remove("invalid_line", "1.0", "end")
        for i, line in enumerate(t.get("1.0", "end-1c").splitlines(), start=1):
            stripped = line.replace(",", " ").strip()
            if not stripped:
                continue
            for token in stripped.split():
                try:
                    n = int(token)
                    if n < 1:
                        raise ValueError
                except ValueError:
                    t.tag_add("invalid_line", f"{i}.0", f"{i}.end")
                    break

    def _parse_input(self):
        for token in self._get_entry_text().replace(",", "\n").splitlines():
            token = token.strip()
            if token:
                try:
                    n = int(token)
                    if n >= 1:
                        return n
                except ValueError:
                    pass
        self._lbl_current.config(text="Enter a positive integer.")
        return None

    def _parse_all_inputs(self):
        ns = []
        for token in self._get_entry_text().replace(",", "\n").splitlines():
            token = token.strip()
            if token:
                try:
                    n = int(token)
                    if n >= 1 and n not in ns:
                        ns.append(n)
                except ValueError:
                    pass
        if not ns:
            self._lbl_current.config(text="Enter positive integers, one per line or comma-separated.")
        return ns

    def _update_stats(self, calc_ms=None, mem_kb=None):
        self._lbl_calc_time.config(text=f"Calc: {calc_ms:.2f} ms" if calc_ms is not None else "Calc: —")
        self._lbl_memory.config(text=f"Mem: {mem_kb:.1f} KB" if mem_kb is not None else "Mem: —")

    _HINT = "Ctrl+Enter to plot  ·  drag to zoom  ·  click legend to show/hide"

    def _update_multi_label(self):
        if len(self._multi_paths) <= 1:
            self._lbl_multi.config(text=self._HINT, foreground="#4a4a4a")
            return
        steps_list = [len(p) - 1 for p, _, _, _ in self._multi_paths]
        peaks_list = [max(p) for p, _, _, _ in self._multi_paths]
        n_max_s = self._multi_paths[steps_list.index(max(steps_list))][1][0]
        n_max_p = self._multi_paths[peaks_list.index(max(peaks_list))][1][0]
        self._lbl_multi.config(
            foreground="#888888",
            text=(f"{len(self._multi_paths)} runs  |  "
                  f"Longest: {max(steps_list)} steps (n={n_max_s:,})  |  "
                  f"Highest peak: {max(peaks_list):,} (n={n_max_p:,})")
        )

    def _load_path(self, n):
        t0 = time.perf_counter()
        self._path = collatz_path(n)
        calc_ms = (time.perf_counter() - t0) * 1000
        mem_kb = (sys.getsizeof(self._path) + len(self._path) * sys.getsizeof(n)) / 1024
        self._display_path, self._terminal_idx = build_display_path(self._path)
        self._update_stats(calc_ms, mem_kb)
        self._zoom = None
        self._zoom_btn.config(state="disabled")

    def _build_multi_paths(self, ns):
        t0 = time.perf_counter()
        result = []
        for i, n in enumerate(ns):
            path = collatz_path(n)
            dp, ti = build_display_path(path)
            result.append((path, dp, ti, _run_color(i)))
        calc_ms = (time.perf_counter() - t0) * 1000
        mem_kb  = sum(sys.getsizeof(p) + len(p) * sys.getsizeof(p[0]) for p, _, _, _ in result) / 1024
        return result, calc_ms, mem_kb

    def _plot(self):
        self._cancel_anim()
        ns = self._parse_all_inputs()
        if not ns:
            return
        self._hidden_runs = set()
        self._multi_paths, calc_ms, mem_kb = self._build_multi_paths(ns)
        p0, dp0, ti0, _ = self._multi_paths[0]
        self._path, self._display_path, self._terminal_idx = p0, dp0, ti0
        self._update_stats(calc_ms, mem_kb)
        self._update_multi_label()
        self._zoom = None
        self._zoom_btn.config(state="disabled")
        self._anim_index = len(self._display_path)
        self._lbl_current.config(text="")
        self._redraw()

    def _animate(self):
        self._cancel_anim()
        ns = self._parse_all_inputs()
        if not ns:
            return
        self._hidden_runs = set()
        self._multi_paths, calc_ms, mem_kb = self._build_multi_paths(ns)
        p0, dp0, ti0, _ = self._multi_paths[0]
        self._path, self._display_path, self._terminal_idx = p0, dp0, ti0
        self._update_stats(calc_ms, mem_kb)
        self._update_multi_label()
        self._zoom = None
        self._zoom_btn.config(state="disabled")
        self._anim_index = 1
        self._lbl_current.config(text="")
        self._tick_anim()

    def _tick_anim(self):
        max_len = max(len(dp) for _, dp, _, _ in self._multi_paths) if self._multi_paths else len(self._display_path)
        if self._anim_index <= max_len:
            self._redraw(self._anim_index)
            step = self._anim_index - 1
            if len(self._multi_paths) > 1:
                parts = []
                for _, dp, _, _ in self._multi_paths:
                    if step < len(dp):
                        parts.append(f"{dp[0]:,}→{dp[step]:,}")
                self._lbl_current.config(text=f"Step {step}:  " + "   ".join(parts))
            else:
                val = self._display_path[min(step, len(self._display_path) - 1)]
                phase = " [4→2→1 loop]" if self._anim_index > len(self._path) else ""
                self._lbl_current.config(text=f"Step {step}: {val:,}{phase}")
            self._anim_index += 1
            delay = max(18, 900 // max_len)
            self._anim_job = self.after(delay, self._tick_anim)
        else:
            self._lbl_current.config(text="Done — reached 4→2→1 cycle.")

    def _step(self):
        self._cancel_anim()
        if not self._path:
            n = self._parse_input()
            if n is None:
                return
            self._load_path(n)
            self._multi_paths = [(self._path, self._display_path, self._terminal_idx, self.LINE_COLOR)]
            self._anim_index = 1
        elif self._anim_index < len(self._display_path):
            self._anim_index += 1
        self._redraw(self._anim_index)
        val = self._display_path[self._anim_index - 1]
        phase = " [4→2→1 loop]" if self._anim_index > len(self._path) else ""
        self._lbl_current.config(text=f"Step {self._anim_index}: {val:,}{phase}")

    def _reset(self):
        self._cancel_anim()
        self._path = self._display_path = []
        self._multi_paths = []
        self._hidden_runs = set()
        self._terminal_idx = self._anim_index = 0
        self._screen_pts = []
        self._zoom = None
        self._zoom_btn.config(state="disabled")
        self._lbl_current.config(text="")
        self._lbl_multi.config(text=self._HINT, foreground="#4a4a4a")
        self._canvas.delete("all")

    def _cancel_anim(self):
        if self._anim_job is not None:
            self.after_cancel(self._anim_job)
            self._anim_job = None

    def _zoom_reset(self):
        self._zoom = None
        self._zoom_btn.config(state="disabled")
        self._redraw()

    def _toggle_run(self, idx):
        if idx in self._hidden_runs:
            self._hidden_runs.discard(idx)
        else:
            visible = [i for i in range(len(self._multi_paths)) if i not in self._hidden_runs]
            if len(visible) <= 1:
                return
            self._hidden_runs.add(idx)
        self._redraw()

    def _open_data_view(self):
        if not self._multi_paths:
            self._lbl_current.config(text="No data — plot first.")
            return
        win = tk.Toplevel(self)
        win.title("Data View — Collatz Statistics")
        win.configure(bg=self.BG)
        win.geometry("700x340")
        win.resizable(True, True)

        sty = ttk.Style(win)
        sty.configure("Dark.Treeview",
                       background="#2d2d2d", foreground="#cccccc",
                       fieldbackground="#2d2d2d", rowheight=22)
        sty.configure("Dark.Treeview.Heading",
                       background="#3c3c3c", foreground="#cccccc")
        sty.map("Dark.Treeview", background=[("selected", "#0e639c")])

        cols   = ("n", "steps", "peak", "odd", "down_run", "color_hex")
        hdrs   = ("Start n", "Steps", "Peak", "Odd Steps", "Max ↓ Run", "Color")
        widths = (110, 80, 140, 100, 100, 90)

        frame = ttk.Frame(win, padding=10)
        frame.pack(fill="both", expand=True)

        tree = ttk.Treeview(frame, columns=cols, show="headings", style="Dark.Treeview")
        for col, hdr, w in zip(cols, hdrs, widths):
            tree.heading(col, text=hdr)
            tree.column(col, width=w, anchor="center", stretch=False)

        for i, (path, dp, _, pcolor) in enumerate(self._multi_paths):
            odd, down = path_stats(path)
            marker = " (hidden)" if i in self._hidden_runs else ""
            tree.insert("", "end", values=(
                f"{dp[0]:,}{marker}", f"{len(path) - 1:,}",
                f"{max(path):,}", f"{odd:,}", str(down), pcolor,
            ))

        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        if len(self._multi_paths) > 1:
            all_steps = [len(p) - 1 for p, _, _, _ in self._multi_paths]
            all_peaks = [max(p) for p, _, _, _ in self._multi_paths]
            summary = (f"Runs: {len(self._multi_paths)}   "
                       f"Steps range: {min(all_steps):,}–{max(all_steps):,}   "
                       f"Peak range: {min(all_peaks):,}–{max(all_peaks):,}")
            ttk.Label(win, text=summary, foreground="#888888",
                      background=self.BG).pack(pady=(0, 8))

    # ---------------------------------------------------------- zoom drag

    def _on_drag_start(self, event):
        for x1, y1, x2, y2, idx in self._legend_items:
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                self._toggle_run(idx)
                self._drag_start = None
                return
        self._drag_start = (event.x, event.y)

    def _on_drag_move(self, event):
        if self._drag_start is None:
            return
        if self._drag_rect:
            self._canvas.delete(self._drag_rect)
        x0, y0 = self._drag_start
        self._drag_rect = self._canvas.create_rectangle(
            x0, y0, event.x, event.y,
            outline="#aaaaaa", dash=(4, 4), fill="", tags="rubberband"
        )

    def _on_drag_end(self, event):
        if self._drag_rect:
            self._canvas.delete(self._drag_rect)
            self._drag_rect = None
        if self._drag_start is None:
            return
        x0, y0 = self._drag_start
        x1, y1 = event.x, event.y
        self._drag_start = None

        if abs(x1 - x0) < 5 or abs(y1 - y0) < 5:
            return

        g = self._plot_geom
        if not g or not self._display_path:
            return

        def sx_to_step(sx):
            raw = (sx - g["lp"]) / max(g["pw"], 1) * (g["ie"] - g["is"]) + g["is"]
            return max(0, min(len(self._display_path) - 1, round(raw)))

        def sy_to_val(sy):
            frac = 1.0 - (sy - g["tp"]) / max(g["ph"], 1)
            frac = max(0.0, min(1.0, frac))
            if g["log"]:
                return 10 ** (g["ly0"] + frac * (g["ly1"] - g["ly0"]))
            return g["y0"] + frac * (g["y1"] - g["y0"])

        s0 = sx_to_step(min(x0, x1))
        s1 = sx_to_step(max(x0, x1))
        if s0 >= s1:
            s1 = min(s0 + 1, len(self._display_path) - 1)

        data = [self._display_path[i] for i in range(s0, s1 + 1)]
        if self._log_scale.get():
            ny0, ny1 = 1, max(data)
        else:
            rb_lo = sy_to_val(max(y0, y1))
            rb_hi = sy_to_val(min(y0, y1))
            in_box = [v for v in data if rb_lo <= v <= rb_hi]
            ny0, ny1 = (max(1, rb_lo), rb_hi) if in_box else (1, max(data))

        if ny1 <= ny0:
            ny1 = ny0 + 1

        self._zoom = {"x0": s0, "x1": s1, "y0": ny0, "y1": ny1}
        self._zoom_btn.config(state="normal")
        self._redraw()

    # ---------------------------------------------------------- mouse overlay

    def _on_mouse_move(self, event):
        c = self._canvas
        c.delete("crosshair")
        c.delete("tooltip")
        if not self._display_path or not self._plot_geom:
            return
        g      = self._plot_geom
        mx, my = event.x, event.y
        cw     = c.winfo_width()
        raw    = (mx - g["lp"]) / max(g["pw"], 1) * (g["ie"] - g["is"]) + g["is"]
        step   = max(g["is"], min(g["ie"], round(raw)))
        if self._databox_on.get():
            self._draw_databox(c, g, step, cw)
        else:
            self._draw_crosshair(c, g, mx, my, step, cw)

    def _draw_crosshair(self, c, g, mx, my, step, cw):
        c.create_line(mx, g["tp"], mx, g["ay"], fill="#4a4a4a", dash=(3, 4), tags="crosshair")
        c.create_line(g["lp"], my, cw, my,      fill="#4a4a4a", dash=(3, 4), tags="crosshair")

        slbl = str(step)
        sw   = self._font.measure(slbl) + 8
        sx   = max(g["lp"], min(cw - sw, mx - sw // 2))
        c.create_rectangle(sx, g["ay"] + 2, sx + sw, g["ay"] + 15,
                           fill=self.BG, outline=self.AXIS_COLOR, tags="crosshair")
        c.create_text(sx + sw // 2, g["ay"] + 8, text=slbl, anchor="center",
                      fill="#cccccc", font=("Segoe UI", 8), tags="crosshair")

        frac = 1.0 - (my - g["tp"]) / max(g["ph"], 1)
        frac = max(0.0, min(1.0, frac))
        yval = (10 ** (g["ly0"] + frac * (g["ly1"] - g["ly0"])) if g["log"]
                else g["y0"] + frac * (g["y1"] - g["y0"]))
        yval = max(1, round(yval))
        ylbl = f"{yval:,}"
        yw   = self._font.measure(ylbl) + 6
        yy   = max(g["tp"] + 6, min(g["ay"] - 6, my))
        c.create_rectangle(g["lp"] - yw - 2, yy - 7, g["lp"] - 2, yy + 7,
                           fill=self.BG, outline=self.AXIS_COLOR, tags="crosshair")
        c.create_text(g["lp"] - 5, yy, text=ylbl, anchor="e",
                      fill="#cccccc", font=("Segoe UI", 8), tags="crosshair")

        if self._screen_pts:
            nearest = min(self._screen_pts, key=lambda p: (p[0] - mx) ** 2 + (p[1] - my) ** 2)
            px, py, idx, val = nearest
            if ((px - mx) ** 2 + (py - my) ** 2) ** 0.5 <= 18:
                lbl = f"Step {idx}:  {val:,}"
                bw  = self._font9.measure(lbl) + 10
                tx  = px + 12
                ty  = py - 22
                if tx + bw > cw:
                    tx = px - bw - 8
                c.create_rectangle(tx - 4, ty - 4, tx + bw, ty + 13,
                                   fill="#2d2d2d", outline="#666666", tags="tooltip")
                c.create_text(tx, ty + 4, text=lbl, anchor="w",
                              fill="#ffffff", font=("Segoe UI", 9), tags="tooltip")

    def _draw_databox(self, c, g, step, cw):
        snap_x = g["lp"] + (step - g["is"]) / max(g["ie"] - g["is"], 1) * g["pw"]
        c.create_line(snap_x, g["tp"], snap_x, g["ay"],
                      fill="#888888", dash=(3, 4), tags="crosshair")
        slbl = str(step)
        sw   = self._font.measure(slbl) + 8
        sx   = max(g["lp"], min(cw - sw, snap_x - sw // 2))
        c.create_rectangle(sx, g["ay"] + 2, sx + sw, g["ay"] + 15,
                           fill=self.BG, outline=self.AXIS_COLOR, tags="crosshair")
        c.create_text(sx + sw // 2, g["ay"] + 8, text=slbl, anchor="center",
                      fill="#cccccc", font=("Segoe UI", 8), tags="crosshair")

        visible_paths = [(dp, pcolor) for i, (_, dp, _, pcolor) in enumerate(self._multi_paths)
                         if i not in self._hidden_runs]
        multi = len(visible_paths) > 1
        pad, lh = 8, 15
        bx_anchor = g.get("leg_x", g["lp"] + g["pw"])

        if multi:
            header = f"Step  {step}"
            rows = []
            for dp, pcolor in visible_paths:
                if step < len(dp):
                    v     = dp[step]
                    prev  = dp[step - 1] if step > 0 else None
                    delta = f"  Δ{v - prev:+,}" if prev is not None else ""
                    rows.append((pcolor, f"{dp[0]:,}", f"{v:,}  {'odd' if v % 2 else 'even'}{delta}"))
                else:
                    rows.append((pcolor, f"{dp[0]:,}", "— terminated"))

            num_w = max(self._font9.measure(r[1]) for r in rows)
            val_w = max(self._font9.measure(r[2]) for r in rows)
            bw    = max(self._font9.measure(header), num_w + val_w + 20) + pad * 2 + 14
            bh    = lh + 4 + len(rows) * lh + pad * 2
            bx    = bx_anchor - bw - 10
            by    = g.get("leg_y", g["tp"] + 6)
            c.create_rectangle(bx, by, bx + bw, by + bh,
                               fill="#1a1a2e", outline="#556", width=1, tags="crosshair")
            c.create_text(bx + pad, by + pad, text=header, anchor="nw",
                          fill="#aaaacc", font=("Segoe UI", 9, "bold"), tags="crosshair")
            c.create_line(bx + pad, by + pad + lh, bx + bw - pad, by + pad + lh,
                          fill="#334", tags="crosshair")
            ry = by + pad + lh + 4
            for pcolor, num_txt, val_txt in rows:
                c.create_rectangle(bx + pad, ry + 2, bx + pad + 10, ry + 11,
                                   fill=pcolor, outline="", tags="crosshair")
                c.create_text(bx + pad + 14, ry, text=num_txt, anchor="nw",
                              fill="#cccccc", font=("Segoe UI", 9), tags="crosshair")
                c.create_text(bx + pad + 14 + num_w + 6, ry, text=val_txt, anchor="nw",
                              fill="#aaaaaa", font=("Segoe UI", 9), tags="crosshair")
                ry += lh
        else:
            dp_vis = visible_paths[0][0] if visible_paths else self._display_path
            if step < 0 or step >= len(dp_vis):
                return
            val  = dp_vis[step]
            prev = dp_vis[step - 1] if step > 0 else None
            nxt  = dp_vis[step + 1] if step < len(dp_vis) - 1 else None
            delta = f"  Δ {val - prev:+,}" if prev is not None else ""
            lines = [
                f"Step  {step}",
                f"Value  {val:,}",
                f"       {'odd' if val % 2 else 'even'}{delta}",
            ]
            if nxt is not None:
                lines.append(f"Next   {nxt:,}")
            bw = max(self._font9.measure(ln) for ln in lines) + pad * 2
            bh = len(lines) * lh + pad * 2
            bx = bx_anchor - bw - 10
            by = g.get("leg_y", g["tp"] + 6)
            c.create_rectangle(bx, by, bx + bw, by + bh,
                               fill="#1a1a2e", outline="#556", width=1, tags="crosshair")
            for k, ln in enumerate(lines):
                c.create_text(bx + pad, by + pad + k * lh, text=ln, anchor="nw",
                              fill="#ccccdd", font=("Segoe UI", 9), tags="crosshair")

    def _on_mouse_leave(self, *_):
        self._canvas.delete("crosshair")
        self._canvas.delete("tooltip")

    # ----------------------------------------------------------------- drawing

    def _redraw(self, visible_count=None):
        if not self._display_path:
            return
        c = self._canvas
        c.delete("all")
        self._screen_pts  = []
        self._legend_items = []

        cw, ch = c.winfo_width(), c.winfo_height()
        if cw < 20 or ch < 20:
            return

        multi  = len(self._multi_paths) > 1
        render = self._multi_paths if self._multi_paths else \
                 [(self._path, self._display_path, self._terminal_idx, self.LINE_COLOR)]

        visible = [(i, path, dp, ti, col) for i, (path, dp, ti, col) in enumerate(render)
                   if i not in self._hidden_runs]
        if not visible:
            return

        max_dp_len = max(len(dp) for _, _, dp, _, _ in visible)
        count = visible_count if visible_count is not None else max_dp_len
        zoom  = self._zoom
        log   = self._log_scale.get()
        max_v = max(max(dp) for _, _, dp, _, _ in visible)

        i_s = max(0, zoom["x0"]) if zoom else 0
        i_e = min(count - 1, zoom["x1"]) if zoom else count - 1
        if i_e < i_s:
            return

        log_dec = math.ceil(math.log10(max(max_v, 2))) if log else 1
        if log:
            y0, y1 = 1, 10 ** log_dec
        elif zoom:
            y0, y1 = zoom["y0"], zoom["y1"]
        else:
            y0, y1 = 1, 10 ** math.ceil(math.log10(max(max_v, 2)))

        ly0, ly1 = 0.0, float(log_dec)

        lp = self._font.measure(f"{int(y1):,}") + 16
        rp, tp, bp = 16, 16, 28
        pw = max(cw - lp - rp, 1)
        ph = max(ch - tp - bp, 1)
        ay = tp + ph

        def to_xy(i, v):
            px = lp + (i - i_s) / max(i_e - i_s, 1) * pw
            if log:
                frac = (math.log10(max(v, 1)) - ly0) / max(ly1 - ly0, 1e-10)
            else:
                frac = (v - y0) / max(y1 - y0, 1)
            return px, tp + (1 - frac) * ph

        # Cache screen coords for primary (first visible) path
        primary_dp = visible[0][2]
        for i in range(i_s, min(count, len(primary_dp))):
            v = primary_dp[i]
            self._screen_pts.append((*to_xy(i, v), i, v))

        self._plot_geom = dict(
            lp=lp, tp=tp, pw=pw, ph=ph, ay=ay,
            ie=i_e, log=log, log_dec=log_dec,
            ly0=ly0, ly1=ly1, y0=y0, y1=y1,
        )
        self._plot_geom["is"] = i_s

        # ── Y-axis grid ──
        if log:
            for e in range(0, log_dec):
                for m in range(2, 10):
                    _, gy = to_xy(0, m * 10 ** e)
                    if tp - 2 <= gy <= ay + 2:
                        c.create_line(lp, gy, lp + pw, gy, fill=self.GRID_MINOR, dash=(2, 8))
            for e in range(0, log_dec + 1):
                v = 10 ** e
                _, gy = to_xy(0, v)
                if tp - 2 <= gy <= ay + 2:
                    c.create_line(lp, gy, lp + pw, gy, fill=self.GRID_COLOR, dash=(4, 6))
                    c.create_text(lp - 6, gy, text=f"{v:,}", anchor="e",
                                  fill="#666666", font=("Segoe UI", 8))
        else:
            for k in range(5):
                v = y0 + k / 4 * (y1 - y0)
                _, gy = to_xy(0, v)
                c.create_line(lp, gy, lp + pw, gy, fill=self.GRID_COLOR, dash=(4, 6))
                c.create_text(lp - 6, gy, text=f"{int(v):,}", anchor="e",
                              fill="#666666", font=("Segoe UI", 8))

        # ── Axis lines ──
        c.create_line(lp, ay, lp + pw, ay, fill=self.AXIS_COLOR)
        c.create_line(lp, tp, lp,      ay, fill=self.AXIS_COLOR)

        # ── X-axis ticks ──
        x_span    = max(i_e - i_s, 1)
        tick_step = max(1, x_span // max(2, pw // 60))
        ticks     = list(range(i_s, i_e + 1, tick_step))
        if ticks[-1] != i_e:
            ticks.append(i_e)
        for ti in ticks:
            tx, _ = to_xy(ti, y0)
            c.create_line(tx, ay, tx, ay + 4, fill=self.AXIS_COLOR)
            c.create_text(tx, ay + 5, text=str(ti), anchor="n",
                          fill="#666666", font=("Segoe UI", 8))

        # ── Path rendering ──
        for run_idx, _, dp, ti_split, pcolor in visible:
            p_i_e = min(i_e, len(dp) - 1)
            if p_i_e < i_s:
                continue

            if multi:
                pts = [c_ for i in range(i_s, p_i_e + 1) for c_ in to_xy(i, dp[i])]
                if len(pts) >= 4:
                    c.create_line(*pts, fill=pcolor, width=2)
            else:
                main_end   = min(ti_split, p_i_e)
                term_start = max(ti_split, i_s)
                if i_s < main_end + 1:
                    pts = [c_ for i in range(i_s, main_end + 1) for c_ in to_xy(i, dp[i])]
                    if len(pts) >= 4:
                        c.create_line(*pts, fill=pcolor, width=2)
                if term_start <= p_i_e:
                    seg_s = max(i_s, term_start - 1)
                    pts = [c_ for i in range(seg_s, p_i_e + 1) for c_ in to_xy(i, dp[i])]
                    if len(pts) >= 4:
                        c.create_line(*pts, fill=self.TERMINAL_COLOR, width=2)

            if self._show_dots.get():
                r = 3 if x_span <= 80 else 2
                for i in range(i_s, p_i_e + 1):
                    px_, py_ = to_xy(i, dp[i])
                    dot_col = pcolor if multi else (self.TERMINAL_DOT if i >= ti_split else self.DOT_COLOR)
                    c.create_oval(px_ - r, py_ - r, px_ + r, py_ + r, fill=dot_col, outline="")

            if i_s == 0:
                sx_, sy_ = to_xy(0, dp[0])
                c.create_text(sx_, sy_ - 10, text=str(dp[0]),
                              fill="#ffffff", font=("Segoe UI", 8))

            if not multi and i_s <= ti_split <= p_i_e:
                tx_, ty_ = to_xy(ti_split, dp[ti_split])
                c.create_line(tx_, ty_, tx_, ay, fill=self.TERMINAL_COLOR, dash=(4, 4), width=1)
                c.create_oval(tx_ - 5, ty_ - 5, tx_ + 5, ty_ + 5,
                              fill=self.TERMINAL_COLOR, outline="#ffffff", width=1)
                anchor = "sw" if tx_ > lp + pw * 0.7 else "s"
                c.create_text(tx_, ty_ - 14, text=f"enters 4→2→1  (step {ti_split})",
                              fill=self.TERMINAL_COLOR, font=("Segoe UI", 8), anchor=anchor)

        # ── Legend (always shown when there is at least one path) ──
        if render:
            all_texts  = [str(dp[0]) for _, dp, _, _ in render]
            item_tw    = max(self._font.measure(t) for t in all_texts)
            # legend wide enough for entries AND the "Viewing:" header
            leg_w      = max(12 + 6 + item_tw + 18,
                             self._font.measure("Viewing:") + 14)
            pad_l      = 6
            title_h    = 14
            item_h     = 16
            leg_h      = pad_l + title_h + 3 + len(render) * item_h + pad_l
            box_y      = tp + 6                          # aligned with databox
            # anchor from canvas right edge so it never drifts off-screen
            leg_left   = cw - leg_w - rp - 4
            self._plot_geom["leg_x"] = leg_left
            self._plot_geom["leg_y"] = box_y

            c.create_rectangle(leg_left - 4, box_y, leg_left + leg_w, box_y + leg_h,
                               fill="#1a1a2e", outline="#444", width=1)
            c.create_text(leg_left, box_y + pad_l, text="Viewing:", anchor="nw",
                          fill="#888888", font=("Segoe UI", 8, "italic"))
            sep_y = box_y + pad_l + title_h
            c.create_line(leg_left - 4, sep_y, leg_left + leg_w, sep_y, fill="#334")
            ly = sep_y + 3

            for run_idx, (_, dp, _, pcolor) in enumerate(render):
                hidden     = run_idx in self._hidden_runs
                sw_color   = "#444444" if hidden else pcolor
                text_color = "#555555" if hidden else "#cccccc"
                label      = str(dp[0]) + (" ○" if hidden else "")
                c.create_rectangle(leg_left, ly + 3, leg_left + 12, ly + 13,
                                   fill=sw_color, outline="")
                c.create_text(leg_left + 18, ly + 8, text=label, anchor="w",
                              fill=text_color, font=("Segoe UI", 8))
                self._legend_items.append((leg_left - 4, ly, leg_left + leg_w, ly + item_h, run_idx))
                ly += item_h
        else:
            self._plot_geom["leg_x"] = cw - rp
            self._plot_geom["leg_y"] = tp + 6


if __name__ == "__main__":
    app = CollatzApp()
    try:
        app.mainloop()
    except KeyboardInterrupt:
        pass
