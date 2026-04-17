import math
import sys
import time
import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont

MULTI_COLORS = ["#4a9eff", "#ff6b6b", "#4ade80", "#ffd700", "#c084fc", "#fb923c"]


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
    """Return (odd_steps, max_descending_run).
    Ascending runs are always 1 — 3n+1 is always even so every rise is
    immediately followed by a halving."""
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
        self.configure(bg=self.BG)
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
        self._multi_paths  = []   # [(path, dp, ti, color), ...] when multi-view active

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
        sty.configure(".",              background=self.BG, foreground="#cccccc", font=("Segoe UI", 10))
        sty.configure("TEntry",         fieldbackground="#3c3c3c", foreground="#cccccc", insertcolor="#cccccc")
        sty.configure("TButton",        background="#3c3c3c", foreground="#cccccc", padding=(8, 4))
        sty.map("TButton",              background=[("active", "#505050")])
        sty.configure("TLabel",         background=self.BG, foreground="#cccccc")
        sty.configure("TCheckbutton",   background=self.BG, foreground="#cccccc")
        sty.configure("Accent.TButton", background="#0e639c", foreground="white")
        sty.map("Accent.TButton",       background=[("active", "#1177bb")])

        # ── Single row, 3 columns ──
        r1 = ttk.Frame(self, padding=(10, 10, 10, 4))
        r1.pack(fill="x")

        # ── Column 1: label + text box ──
        col1 = ttk.Frame(r1)
        col1.pack(side="left", anchor="n")
        ttk.Label(col1, text="Starting numbers:").pack(anchor="w")

        txt_frame = tk.Frame(col1, bg="#555555", highlightthickness=1,
                            highlightbackground="#555555")
        txt_frame.pack(anchor="w")
        xscroll = ttk.Scrollbar(txt_frame, orient="horizontal")
        yscroll = ttk.Scrollbar(txt_frame, orient="vertical")
        self._entry = tk.Text(
            txt_frame, width=24, height=5, wrap="none",
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

        # ── Column 2: buttons / bordered title / stats ──
        col2 = ttk.Frame(r1)
        col2.pack(side="left", padx=(10, 0), anchor="n")

        btn_frame = ttk.Frame(col2)
        btn_frame.pack(anchor="w")
        ttk.Button(btn_frame, text="Plot",    style="Accent.TButton", command=self._plot).pack(side="left", padx=(0, 2))
        ttk.Button(btn_frame, text="Animate", command=self._animate).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Step →",  command=self._step).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Reset",   command=self._reset).pack(side="left", padx=2)

        title_border = tk.Frame(col2, highlightthickness=1,
                                highlightbackground="#4a9eff", bg=self.BG)
        title_border.pack(fill="x", pady=(6, 0))
        ttk.Label(title_border, text="Collatz Explorer (n = 3n+1|n-odd ; n/2|n-even)",
                  font=("Segoe UI", 11, "bold"), foreground="#4a9eff").pack(padx=6, pady=2)

        bot = ttk.Frame(col2)
        bot.pack(anchor="w", pady=(4, 0))
        self._lbl_steps     = ttk.Label(bot, text="Steps: —");      self._lbl_steps.pack(side="left", padx=(0, 12))
        self._lbl_peak      = ttk.Label(bot, text="Peak: —");       self._lbl_peak.pack(side="left", padx=(0, 12))
        self._lbl_odd       = ttk.Label(bot, text="Odd steps: —");  self._lbl_odd.pack(side="left", padx=(0, 12))
        self._lbl_run_down  = ttk.Label(bot, text="↓ run: —");      self._lbl_run_down.pack(side="left", padx=(0, 12))

        # ── Column 3: checkboxes top, zoom bottom-right ──
        col3 = ttk.Frame(r1)
        col3.pack(side="left", padx=(14, 0), fill="y", anchor="n")

        cb = ttk.Frame(col3)
        cb.pack(anchor="w")
        ttk.Checkbutton(cb, text="Points",    variable=self._show_dots,  command=self._redraw).grid(row=0, column=0, sticky="w", padx=(0, 10), pady=1)
        ttk.Checkbutton(cb, text="Log scale", variable=self._log_scale,  command=self._redraw).grid(row=0, column=1, sticky="w", pady=1)
        ttk.Checkbutton(cb, text="Databox",   variable=self._databox_on, command=self._redraw).grid(row=1, column=0, sticky="w", padx=(0, 10), pady=1)

        self._zoom_btn = ttk.Button(col3, text="Zoom out", command=self._zoom_reset, state="disabled")
        self._zoom_btn.pack(side="bottom", anchor="e")

        # ── Status bar (pack before canvas so it stays at bottom) ──
        sbar = tk.Frame(self, bg="#2a2a2a", height=20)
        sbar.pack(side="bottom", fill="x")
        self._lbl_current = tk.Label(sbar, text="Ready", fg="#888888", bg="#2a2a2a",
                                     font=("Segoe UI", 9), anchor="w")
        self._lbl_current.pack(side="left", padx=(8, 0))
        self._lbl_memory    = tk.Label(sbar, text="Mem: —", fg="#666666", bg="#2a2a2a",
                                       font=("Segoe UI", 9))
        self._lbl_memory.pack(side="right", padx=(0, 10))
        self._lbl_calc_time = tk.Label(sbar, text="Calc: —", fg="#666666", bg="#2a2a2a",
                                       font=("Segoe UI", 9))
        self._lbl_calc_time.pack(side="right", padx=(0, 6))

        # ── Canvas ──
        self._canvas = tk.Canvas(self, bg=self.CANVAS_BG, highlightthickness=0, width=820, height=420)
        self._canvas.pack(fill="both", expand=True, padx=10, pady=(0, 4))
        self._canvas.bind("<Configure>",       lambda _: self._redraw())
        self._canvas.bind("<Motion>",          self._on_mouse_move)
        self._canvas.bind("<Leave>",           self._on_mouse_leave)
        self._canvas.bind("<ButtonPress-1>",   self._on_drag_start)
        self._canvas.bind("<B1-Motion>",       self._on_drag_move)
        self._canvas.bind("<ButtonRelease-1>", self._on_drag_end)
        self._canvas.bind("<Double-Button-1>", lambda _: self._zoom_reset())

    # ------------------------------------------------------------------ logic

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
        """Return first valid positive integer from the text box, or None."""
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
        """Return list of all valid positive integers from the text box."""
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

    def _update_stats(self, path, calc_ms=None, mem_kb=None):
        odd, down = path_stats(path)
        self._lbl_steps.config(text=f"Steps: {len(path) - 1}")
        self._lbl_peak.config(text=f"Peak: {max(path):,}")
        self._lbl_odd.config(text=f"Odd steps: {odd}")
        self._lbl_run_down.config(text=f"↓ run: {down}")
        self._lbl_calc_time.config(text=f"Calc: {calc_ms:.2f} ms" if calc_ms is not None else "Calc: —")
        self._lbl_memory.config(text=f"Mem: {mem_kb:.1f} KB" if mem_kb is not None else "Mem: —")

    def _load_path(self, n):
        t0 = time.perf_counter()
        self._path = collatz_path(n)
        calc_ms = (time.perf_counter() - t0) * 1000
        mem_kb = (sys.getsizeof(self._path) + len(self._path) * sys.getsizeof(n)) / 1024
        self._display_path, self._terminal_idx = build_display_path(self._path)
        self._update_stats(self._path, calc_ms, mem_kb)
        self._zoom = None
        self._zoom_btn.config(state="disabled")

    def _build_multi_paths(self, ns):
        """Compute all paths, return (multi_paths, calc_ms, mem_kb)."""
        t0 = time.perf_counter()
        result = []
        for i, n in enumerate(ns):
            path = collatz_path(n)
            dp, ti = build_display_path(path)
            result.append((path, dp, ti, MULTI_COLORS[i % len(MULTI_COLORS)]))
        calc_ms = (time.perf_counter() - t0) * 1000
        mem_kb  = sum(sys.getsizeof(p) + len(p) * sys.getsizeof(p[0]) for p, _, _, _ in result) / 1024
        return result, calc_ms, mem_kb

    def _plot(self):
        self._cancel_anim()
        ns = self._parse_all_inputs()
        if not ns:
            return
        self._multi_paths, calc_ms, mem_kb = self._build_multi_paths(ns)
        p0, dp0, ti0, _ = self._multi_paths[0]
        self._path, self._display_path, self._terminal_idx = p0, dp0, ti0
        self._update_stats(p0, calc_ms, mem_kb)
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
        self._multi_paths, calc_ms, mem_kb = self._build_multi_paths(ns)
        p0, dp0, ti0, _ = self._multi_paths[0]
        self._path, self._display_path, self._terminal_idx = p0, dp0, ti0
        self._update_stats(p0, calc_ms, mem_kb)
        self._zoom = None
        self._zoom_btn.config(state="disabled")
        self._anim_index = 1
        self._lbl_current.config(text="")
        self._tick_anim()

    def _tick_anim(self):
        max_len = max(len(dp) for _, dp, _, _ in self._multi_paths) if self._multi_paths else len(self._display_path)
        if self._anim_index <= max_len:
            self._redraw(self._anim_index)
            safe_i = min(self._anim_index - 1, len(self._display_path) - 1)
            val = self._display_path[safe_i]
            phase = " [4→2→1 loop]" if self._anim_index > len(self._path) else ""
            self._lbl_current.config(text=f"Step {self._anim_index}: {val:,}{phase}")
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
        self._terminal_idx = self._anim_index = 0
        self._screen_pts = []
        self._zoom = None
        self._zoom_btn.config(state="disabled")
        for lbl, txt in [(self._lbl_steps, "Steps: —"), (self._lbl_peak, "Peak: —"),
                         (self._lbl_odd, "Odd steps: —"), (self._lbl_run_down, "↓ run: —"),
                         (self._lbl_current, "")]:
            lbl.config(text=txt)
        self._canvas.delete("all")

    def _cancel_anim(self):
        if self._anim_job is not None:
            self.after_cancel(self._anim_job)
            self._anim_job = None

    def _zoom_reset(self):
        self._zoom = None
        self._zoom_btn.config(state="disabled")
        self._redraw()

    # ---------------------------------------------------------- zoom drag

    def _on_drag_start(self, event):
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

        g   = self._plot_geom
        mx, my = event.x, event.y
        cw  = c.winfo_width()
        raw = (mx - g["lp"]) / max(g["pw"], 1) * (g["ie"] - g["is"]) + g["is"]
        step = max(g["is"], min(g["ie"], round(raw)))

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
        # Draw the step-snapped vertical line and x-axis label
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

        multi = len(self._multi_paths) > 1
        pad, lh = 8, 15
        bx_anchor = g.get("leg_x", g["lp"] + g["pw"])

        if multi:
            # Comparison table: one row per path
            header = f"Step  {step}"
            rows = []
            for _, dp, _, pcolor in self._multi_paths:
                n0 = dp[0]
                if step < len(dp):
                    v    = dp[step]
                    prev = dp[step - 1] if step > 0 else None
                    delta = f"  Δ{v - prev:+,}" if prev is not None else ""
                    parity = "odd" if v % 2 else "even"
                    rows.append((pcolor, f"{n0:,}", f"{v:,}  {parity}{delta}"))
                else:
                    rows.append((pcolor, f"{n0:,}", "— terminated"))

            num_w  = max(self._font9.measure(r[1]) for r in rows)
            val_w  = max(self._font9.measure(r[2]) for r in rows)
            hdr_w  = self._font9.measure(header)
            bw     = max(hdr_w, num_w + val_w + 20) + pad * 2 + 14
            bh     = lh + 4 + len(rows) * lh + pad * 2
            bx     = bx_anchor - bw - 10
            by     = g["tp"] + 10

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
            if step < 0 or step >= len(self._display_path):
                return
            val  = self._display_path[step]
            prev = self._display_path[step - 1] if step > 0 else None
            nxt  = self._display_path[step + 1] if step < len(self._display_path) - 1 else None
            delta = f"  Δ {val - prev:+,}" if prev is not None else ""
            lines = [
                f"Step  {step}",
                f"Value  {val:,}",
                f"       {'odd' if val % 2 else 'even'}{delta}",
            ]
            if nxt is not None:
                lines.append(f"Next   {nxt:,}")
            bw  = max(self._font9.measure(ln) for ln in lines) + pad * 2
            bh  = len(lines) * lh + pad * 2
            bx  = bx_anchor - bw - 10
            by  = g["tp"] + 10
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
        self._screen_pts = []

        cw, ch = c.winfo_width(), c.winfo_height()
        if cw < 20 or ch < 20:
            return

        # Build render list
        multi  = len(self._multi_paths) > 1
        render = self._multi_paths if self._multi_paths else \
                 [(self._path, self._display_path, self._terminal_idx, self.LINE_COLOR)]

        max_dp_len = max(len(dp) for _, dp, _, _ in render)
        count = visible_count if visible_count is not None else max_dp_len
        zoom  = self._zoom
        log   = self._log_scale.get()
        max_v = max(max(dp) for _, dp, _, _ in render)

        # Index range
        i_s = max(0, zoom["x0"]) if zoom else 0
        i_e = min(count - 1, zoom["x1"]) if zoom else count - 1
        if i_e < i_s:
            return

        # Y range — log always uses full decades
        log_dec = math.ceil(math.log10(max(max_v, 2))) if log else 1
        if log:
            y0, y1 = 1, 10 ** log_dec
        elif zoom:
            y0, y1 = zoom["y0"], zoom["y1"]
        else:
            y0, y1 = 1, 10 ** math.ceil(math.log10(max(max_v, 2)))

        ly0, ly1 = 0.0, float(log_dec)

        # Padding — left pad from actual font width of widest y label
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

        # Cache screen coords for primary path (mouse hover)
        for i in range(i_s, min(count, len(self._display_path))):
            v = self._display_path[i]
            self._screen_pts.append((*to_xy(i, v), i, v))

        self._plot_geom = dict(
            lp=lp, tp=tp, pw=pw, ph=ph, ay=ay,
            ie=i_e, log=log, log_dec=log_dec,
            ly0=ly0, ly1=ly1, y0=y0, y1=y1,
        )
        self._plot_geom["is"] = i_s

        # ── Y-axis grid ──
        if log:
            # Minor lines (2–9) within each decade
            for e in range(0, log_dec):
                for m in range(2, 10):
                    _, gy = to_xy(0, m * 10 ** e)
                    if tp - 2 <= gy <= ay + 2:
                        c.create_line(lp, gy, lp + pw, gy, fill=self.GRID_MINOR, dash=(2, 8))
            # Major decade lines at 10^0, 10^1, …, 10^log_dec
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
        for _, dp, ti_split, pcolor in render:
            p_i_e = min(i_e, len(dp) - 1)
            if p_i_e < i_s:
                continue

            if multi:
                # Multi-view: single colour throughout, no terminal split
                pts = [c_ for i in range(i_s, p_i_e + 1) for c_ in to_xy(i, dp[i])]
                if len(pts) >= 4:
                    c.create_line(*pts, fill=pcolor, width=2)
            else:
                # Single path: blue main + gold terminal
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

            # Dots
            if self._show_dots.get():
                r = 3 if x_span <= 80 else 2
                for i in range(i_s, p_i_e + 1):
                    px_, py_ = to_xy(i, dp[i])
                    if multi:
                        dot_col = pcolor
                    else:
                        dot_col = self.TERMINAL_DOT if i >= ti_split else self.DOT_COLOR
                    c.create_oval(px_ - r, py_ - r, px_ + r, py_ + r, fill=dot_col, outline="")

            # Start label
            if i_s == 0:
                sx_, sy_ = to_xy(0, dp[0])
                c.create_text(sx_, sy_ - 10, text=str(dp[0]),
                              fill="#aaaaaa", font=("Segoe UI", 8))

            # Terminal entry marker (single-path mode only)
            if not multi and i_s <= ti_split <= p_i_e:
                tx_, ty_ = to_xy(ti_split, dp[ti_split])
                c.create_line(tx_, ty_, tx_, ay, fill=self.TERMINAL_COLOR, dash=(4, 4), width=1)
                c.create_oval(tx_ - 5, ty_ - 5, tx_ + 5, ty_ + 5,
                              fill=self.TERMINAL_COLOR, outline="#ffffff", width=1)
                anchor = "sw" if tx_ > lp + pw * 0.7 else "s"
                c.create_text(tx_, ty_ - 14,
                              text=f"enters 4→2→1  (step {ti_split})",
                              fill=self.TERMINAL_COLOR, font=("Segoe UI", 8), anchor=anchor)

        # Multi-view legend — top-right; store left edge for databox positioning
        if multi:
            leg_texts  = [str(dp[0]) for _, dp, _, _ in render]
            leg_tw     = max(self._font.measure(t) for t in leg_texts)
            leg_w      = 12 + 6 + leg_tw + 10
            leg_h      = len(render) * 14 + 6
            leg_left   = lp + pw - leg_w - 6
            self._plot_geom["leg_x"] = leg_left
            ly = tp + 6
            c.create_rectangle(leg_left - 4, ly - 2, leg_left + leg_w, ly + leg_h,
                               fill="#1a1a2e", outline="#444", width=1)
            for _, dp, _, pcolor in render:
                c.create_rectangle(leg_left, ly + 2, leg_left + 12, ly + 12, fill=pcolor, outline="")
                c.create_text(leg_left + 18, ly + 7, text=str(dp[0]), anchor="w",
                              fill="#cccccc", font=("Segoe UI", 8))
                ly += 14
        else:
            self._plot_geom["leg_x"] = lp + pw  # no legend: right edge


if __name__ == "__main__":
    app = CollatzApp()
    try:
        app.mainloop()
    except KeyboardInterrupt:
        pass
