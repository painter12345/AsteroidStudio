import os, sys, json, copy, math, queue, random, threading, subprocess, time, colorsys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import numpy as np
from PIL import Image, ImageTk, ImageDraw, ImageFont
try:
    import PIL._tkinter_finder
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import asteroid as tr

GEN = os.path.join(tr.TOOL, 'asteroid.py')
RES = ['512', '1024', '2048', '4096', '8192']
LIVE_RES = ['512', '1024']
RES_INFO = {'512': 'a few seconds', '1024': 'about 10 s', '2048': 'about 30 s',
            '4096': 'about 1\u20132 min', '8192': 'about 5\u201310 min'}
BG = '#1b1f27'
PANEL = '#232934'
FIELD = '#2c3340'
FG = '#d9dee8'
DIM = '#8a93a6'
ACC = '#6fa8ff'
WARM = '#ffb36b'
LINE = '#3a4252'
NOWIN = 0x08000000 if os.name == 'nt' else 0
FONT = 'Segoe UI' if os.name == 'nt' else 'DejaVu Sans'
MONO = 'Consolas' if os.name == 'nt' else 'DejaVu Sans Mono'


SETTINGS = tr.SETTINGS_FILE

def load_settings():
    try:
        with open(SETTINGS) as f:
            return json.load(f)
    except Exception:
        return {}


def save_settings(d):
    try:
        with open(SETTINGS, 'w') as f:
            json.dump(d, f, indent=1)
    except Exception:
        pass


def open_folder(d):
    if os.name == 'nt':
        os.startfile(d)
    else:
        subprocess.Popen(['xdg-open', d])


def hexcol(c):
    return '#%02x%02x%02x' % tuple(int(max(0, min(255, round(v)))) for v in c)


def getp(d, path):
    for k in path:
        d = d[k]
    return d


def setp(d, path, v):
    for k in path[:-1]:
        d = d[k]
    d[path[-1]] = v



def sheet_font(size):
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()



def make_style(root):
    st = ttk.Style(root)
    st.theme_use('clam')
    st.configure('.', background=BG, foreground=FG, fieldbackground=FIELD, bordercolor=LINE, lightcolor=PANEL,
                 darkcolor=BG, troughcolor=FIELD, focuscolor=ACC, selectbackground=ACC, selectforeground='#0b1020',
                 insertcolor=FG, font=(FONT, 10))
    st.configure('TFrame', background=BG)
    st.configure('Card.TFrame', background=PANEL)
    st.configure('Bar.TFrame', background=PANEL)
    st.configure('TLabel', background=BG, foreground=FG)
    st.configure('Dim.TLabel', background=BG, foreground=DIM)
    st.configure('Bar.TLabel', background=PANEL, foreground=FG)
    st.configure('BarDim.TLabel', background=PANEL, foreground=DIM)
    st.configure('CardDim.TLabel', background=PANEL, foreground=DIM)
    st.configure('CardHead.TLabel', background=PANEL, foreground=FG, font=(FONT, 11, 'bold'))
    st.configure('Head.TLabel', background=BG, foreground=FG, font=(FONT, 11, 'bold'))
    st.configure('Title.TLabel', background=PANEL, foreground=FG, font=(FONT, 12, 'bold'))
    st.configure('TButton', background=PANEL, foreground=FG, padding=(10, 4), bordercolor=LINE)
    st.map('TButton', background=[('disabled', BG), ('active', '#2f3746')], foreground=[('disabled', '#5a6272')])
    st.configure('Accent.TButton', background='#2d5fa8', foreground='white')
    st.map('Accent.TButton', background=[('disabled', '#253246'), ('active', '#3a72c4')])
    st.configure('Small.TButton', padding=(5, 1))
    st.configure('TNotebook', background=BG, bordercolor=LINE, tabmargins=(4, 6, 4, 0))
    st.configure('TNotebook.Tab', background=PANEL, foreground=DIM, padding=(9, 5), bordercolor=LINE)
    st.map('TNotebook.Tab', background=[('selected', BG)], foreground=[('selected', FG)])
    st.configure('TLabelframe', background=BG, bordercolor=LINE)
    st.configure('TLabelframe.Label', background=BG, foreground=DIM)
    st.configure('TEntry', fieldbackground=FIELD, foreground=FG)
    st.configure('TSpinbox', fieldbackground=FIELD, foreground=FG, arrowcolor=FG, background=PANEL)
    st.configure('TCombobox', fieldbackground=FIELD, foreground=FG, arrowcolor=FG, background=PANEL)
    st.map('TCombobox', fieldbackground=[('readonly', FIELD)], foreground=[('readonly', FG)],
           selectbackground=[('readonly', FIELD)], selectforeground=[('readonly', FG)])
    st.configure('Horizontal.TScale', background=PANEL, troughcolor=FIELD, bordercolor=LINE)
    st.configure('TCheckbutton', background=BG, foreground=FG)
    st.map('TCheckbutton', background=[('active', BG)])
    st.configure('Toolbutton', background=PANEL, foreground=DIM, padding=(10, 4))
    st.map('Toolbutton', background=[('selected', '#2d5fa8'), ('active', '#2f3746')], foreground=[('selected', 'white')])
    st.configure('Horizontal.TProgressbar', background=ACC, troughcolor=FIELD, bordercolor=LINE, lightcolor=ACC, darkcolor=ACC)
    st.configure('Vertical.TScrollbar', background=PANEL, troughcolor=BG, arrowcolor=DIM, bordercolor=BG,
                 lightcolor=PANEL, darkcolor=PANEL, gripcount=0)
    st.map('Vertical.TScrollbar', background=[('active', '#3a4456')])
    root.option_add('*TCombobox*Listbox.background', FIELD)
    root.option_add('*TCombobox*Listbox.foreground', FG)
    root.option_add('*TCombobox*Listbox.selectBackground', ACC)


class ScrollFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0, bg=BG)
        self.vsb = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.inner = ttk.Frame(self.canvas, padding=(4, 6, 8, 12))
        self.inner.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.win = self.canvas.create_window((0, 0), window=self.inner, anchor='nw')
        self.canvas.bind('<Configure>', lambda e: self.canvas.itemconfigure(self.win, width=e.width))
        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.canvas.pack(side='left', fill='both', expand=True)
        self.vsb.pack(side='right', fill='y')
        self.bind('<Enter>', self._on)
        self.bind('<Leave>', self._off)

    def _on(self, _e=None):
        self.canvas.bind_all('<MouseWheel>', self._wheel)
        self.canvas.bind_all('<Button-4>', lambda e: self.canvas.yview_scroll(-2, 'units'))
        self.canvas.bind_all('<Button-5>', lambda e: self.canvas.yview_scroll(2, 'units'))

    def _off(self, _e=None):
        self.canvas.unbind_all('<MouseWheel>')
        self.canvas.unbind_all('<Button-4>')
        self.canvas.unbind_all('<Button-5>')

    def _wheel(self, e):
        self.canvas.yview_scroll(-1 * int(e.delta / 120) if abs(e.delta) >= 120 else (-1 if e.delta > 0 else 1), 'units')


class Slider:
    def __init__(self, app, parent, row, label, path, lo, hi, step, isint=False, tip=None, src=None, notify=None, registry=None):
        self.app, self.path, self.lo, self.hi, self.step, self.isint = app, path, lo, hi, step, isint
        self.src = src or (lambda: app.P)
        self.notify = notify or app.changed
        self.busy = False
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky='w', padx=(8, 8), pady=(4, 0))
        self.var = tk.DoubleVar()
        self.scale = ttk.Scale(parent, from_=lo, to=hi, orient='horizontal', variable=self.var, command=self.moved)
        self.scale.grid(row=row, column=1, sticky='ew', pady=(4, 0))
        self.scale.bind('<ButtonPress-1>', self.press, add='+')
        self.scale.bind('<ButtonRelease-1>', self.release, add='+')
        self.start = None
        self.txt = tk.StringVar()
        en = ttk.Entry(parent, textvariable=self.txt, width=9, justify='right')
        en.grid(row=row, column=2, padx=(8, 4), pady=(4, 0))
        en.bind('<Return>', self.typed)
        en.bind('<FocusOut>', self.typed)
        if tip:
            ttk.Label(parent, text=tip, style='Dim.TLabel', font=(FONT, 8)).grid(row=row + 1, column=0, columnspan=3, sticky='w', padx=(8, 0))
        (registry if registry is not None else app.sliders).append(self)

    def press(self, _e=None):
        self.start = copy.deepcopy(getp(self.src(), self.path))
        if self.registry_undo():
            self.app.snapshot()

    def release(self, _e=None):
        if self.start is not None and self.registry_undo() and getp(self.src(), self.path) == self.start and self.app.history:
            self.app.history.pop()
            if not self.app.history:
                self.app.undo_btn.configure(state='disabled')
        self.start = None

    def registry_undo(self):
        return self.src is not None and getattr(self.app, 'P', None) is self.src()

    def fmt(self, v):
        if self.isint:
            return str(int(round(v)))
        dec = max(0, -int(np.floor(np.log10(self.step)))) if self.step < 1 else 0
        return ('%.' + str(dec) + 'f') % v

    def snap(self, v):
        v = round(v / self.step) * self.step
        return int(round(v)) if self.isint else float(self.fmt(v))

    def refresh(self):
        v = getp(self.src(), self.path)
        self.busy = True
        self.var.set(min(max(v, self.lo), self.hi))
        self.txt.set(self.fmt(v))
        self.busy = False

    def moved(self, _=None):
        if self.busy:
            return
        v = self.snap(self.var.get())
        self.txt.set(self.fmt(v))
        if v != getp(self.src(), self.path):
            setp(self.src(), self.path, v)
            self.notify()

    def typed(self, _=None):
        try:
            v = self.snap(float(self.txt.get().replace(',', '.')))
        except ValueError:
            self.refresh()
            return
        self.busy = True
        self.var.set(min(max(v, self.lo), self.hi))
        self.busy = False
        self.txt.set(self.fmt(v))
        if v != getp(self.src(), self.path):
            if self.registry_undo():
                self.app.snapshot()
            setp(self.src(), self.path, v)
            self.notify()


def sv_image(h, n=256):
    c = np.array(colorsys.hsv_to_rgb(h, 1.0, 1.0), np.float32)
    sat = np.linspace(0, 1, n, dtype=np.float32)[None, :, None]
    val = np.linspace(1, 0, n, dtype=np.float32)[:, None, None]
    img = val * ((1 - sat) + sat * c[None, None, :])
    return Image.fromarray((img * 255 + 0.5).astype(np.uint8))


def hue_image(w=26, n=256):
    rows = np.array([colorsys.hsv_to_rgb(y / float(n), 1.0, 1.0) for y in range(n)], np.float32)
    return Image.fromarray((np.repeat(rows[:, None, :], w, 1) * 255 + 0.5).astype(np.uint8))


def recent_colours():
    out = []
    for c in load_settings().get('recent_colours', []):
        try:
            v = [int(max(0, min(255, x))) for x in c][:3]
            if len(v) == 3:
                out.append(v)
        except (TypeError, ValueError):
            pass
    return out[:14]


def remember_colour(rgb):
    S = load_settings()
    rc = [list(rgb)] + [c for c in recent_colours() if list(c) != list(rgb)]
    S['recent_colours'] = rc[:14]
    save_settings(S)


class PixelPicker(tk.Toplevel):
    Z = 11

    def __init__(self, master, img, done, fullscreen=False):
        super().__init__(master)
        self.img = img
        self.arr = np.asarray(img).astype(np.float32)
        self.done = done
        self.finished = False
        self.configure(bg='black')
        iw, ih = img.size
        if fullscreen:
            self.overrideredirect(True)
            sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
            self.geometry('%dx%d+0+0' % (sw, sh))
            dw, dh = sw, sh
        else:
            self.title('Click a colour in the picture')
            sc = min(1100.0 / iw, 760.0 / ih, 1.0 if max(iw, ih) > 300 else 4.0)
            dw, dh = max(1, int(iw * sc)), max(1, int(ih * sc))
        self.sx, self.sy = iw / float(dw), ih / float(dh)
        disp = img.resize((dw, dh), Image.LANCZOS) if (dw, dh) != (iw, ih) else img
        self.tkimg = ImageTk.PhotoImage(disp)
        self.cv = tk.Canvas(self, width=dw, height=dh, bg='black', highlightthickness=0, cursor='crosshair')
        self.cv.pack()
        self.cv.create_image(0, 0, image=self.tkimg, anchor='nw')
        self.loupe_img = None
        self.lp = self.cv.create_image(0, 0, anchor='nw')
        self.lbox = self.cv.create_rectangle(0, 0, 0, 0, outline='white', width=2)
        self.lfr = self.cv.create_rectangle(0, 0, 0, 0, outline='white', width=1)
        self.ltxt_bg = self.cv.create_rectangle(0, 0, 0, 0, fill='#101318', outline='')
        self.ltxt = self.cv.create_text(0, 0, anchor='nw', fill='white', font=(MONO, 10))
        self.cv.create_rectangle(dw // 2 - 210, 2, dw // 2 + 210, 28, fill='#101318', outline=LINE)
        self.cv.create_text(dw // 2, 15, text='Click a colour  \u00b7  Esc or right-click = cancel', fill='white',
                            font=(FONT, 11, 'bold'))
        self.cv.bind('<Motion>', self.move)
        self.cv.bind('<Button-1>', self.click)
        self.cv.bind('<Button-3>', lambda e: self.close(None))
        self.bind('<Escape>', lambda e: self.close(None))
        self.protocol('WM_DELETE_WINDOW', lambda: self.close(None))
        self.after(50, self.take_focus)

    def take_focus(self):
        try:
            self.lift()
            self.focus_force()
            self.grab_set()
        except tk.TclError:
            pass

    def at(self, x, y):
        H, W = self.arr.shape[:2]
        return min(max(int(x * self.sx), 0), W - 1), min(max(int(y * self.sy), 0), H - 1)

    def colour(self, ix, iy):
        H, W = self.arr.shape[:2]
        a = self.arr[max(iy - 1, 0):min(iy + 2, H), max(ix - 1, 0):min(ix + 2, W)]
        return [int(round(v)) for v in a.reshape(-1, 3).mean(0)]

    def move(self, e):
        ix, iy = self.at(e.x, e.y)
        r = self.Z // 2
        H, W = self.arr.shape[:2]
        ys = np.clip(np.arange(iy - r, iy + r + 1), 0, H - 1)
        xs = np.clip(np.arange(ix - r, ix + r + 1), 0, W - 1)
        crop = self.arr[ys][:, xs].astype(np.uint8)
        big = Image.fromarray(crop).resize((self.Z * 10, self.Z * 10), Image.NEAREST)
        self.loupe_img = ImageTk.PhotoImage(big)
        cw, ch = int(self.cv.cget('width')), int(self.cv.cget('height'))
        lx = e.x + 24 if e.x + 24 + 110 < cw else e.x - 24 - 110
        ly = e.y + 24 if e.y + 24 + 140 < ch else e.y - 24 - 140
        self.cv.itemconfigure(self.lp, image=self.loupe_img)
        self.cv.coords(self.lp, lx, ly)
        self.cv.coords(self.lfr, lx, ly, lx + 110, ly + 110)
        self.cv.coords(self.lbox, lx + 50, ly + 50, lx + 60, ly + 60)
        c = self.colour(ix, iy)
        self.cv.coords(self.ltxt_bg, lx, ly + 112, lx + 110, ly + 134)
        self.cv.coords(self.ltxt, lx + 6, ly + 115)
        self.cv.itemconfigure(self.ltxt, text=hexcol(c))
        for it in (self.lp, self.lfr, self.lbox, self.ltxt_bg, self.ltxt):
            self.cv.tag_raise(it)

    def click(self, e):
        self.close(self.colour(*self.at(e.x, e.y)))

    def close(self, rgb):
        if self.finished:
            return
        self.finished = True
        try:
            self.grab_release()
        except tk.TclError:
            pass
        self.destroy()
        self.done(rgb)


class ColourPicker(tk.Toplevel):
    def __init__(self, app, initial, title, live=None):
        super().__init__(app)
        self.app = app
        self.live = live
        self.result = None
        self.title(title)
        self.configure(bg=BG)
        self.resizable(False, False)
        self.transient(app)
        self.initial = [int(round(float(v))) for v in initial][:3]
        self.rgb = list(self.initial)
        self.h, self.s, self.v = colorsys.rgb_to_hsv(*[c / 255.0 for c in self.rgb])
        body = ttk.Frame(self, padding=12)
        body.pack(fill='both')
        self.sv = tk.Canvas(body, width=256, height=256, highlightthickness=1, highlightbackground=LINE, cursor='crosshair', bg=BG)
        self.sv.grid(row=0, column=0, sticky='n')
        self.hue = tk.Canvas(body, width=26, height=256, highlightthickness=1, highlightbackground=LINE, cursor='sb_v_double_arrow', bg=BG)
        self.hue.grid(row=0, column=1, sticky='n', padx=(8, 14))
        self.hue_tk = ImageTk.PhotoImage(hue_image())
        self.hue.create_image(0, 0, image=self.hue_tk, anchor='nw')
        self.hue_mark = self.hue.create_rectangle(0, 0, 27, 4, outline='white', width=2)
        self.sv_img = self.sv.create_image(0, 0, anchor='nw')
        self.sv_mark = self.sv.create_oval(0, 0, 0, 0, outline='white', width=2)
        self.sv_mark2 = self.sv.create_oval(0, 0, 0, 0, outline='black', width=1)
        for ev in ('<Button-1>', '<B1-Motion>'):
            self.sv.bind(ev, self.sv_click)
            self.hue.bind(ev, self.hue_click)
        right = ttk.Frame(body)
        right.grid(row=0, column=2, sticky='n')
        self.cmp = tk.Canvas(right, width=150, height=56, highlightthickness=1, highlightbackground=LINE, bg=BG)
        self.cmp.grid(row=0, column=0, columnspan=4, sticky='w')
        self.cmp_old = self.cmp.create_rectangle(0, 0, 75, 57, outline='')
        self.cmp_new = self.cmp.create_rectangle(75, 0, 151, 57, outline='')
        self.cmp.tag_bind(self.cmp_old, '<Button-1>', lambda e: self.set_rgb(self.initial))
        ttk.Label(right, text='before          now', style='Dim.TLabel').grid(row=1, column=0, columnspan=4, sticky='w', pady=(2, 8))
        ttk.Label(right, text='Hex').grid(row=2, column=0, sticky='w')
        self.hexv = tk.StringVar()
        he = ttk.Entry(right, textvariable=self.hexv, width=9)
        he.grid(row=2, column=1, columnspan=3, sticky='w', pady=2)
        he.bind('<Return>', self.hex_typed)
        he.bind('<FocusOut>', self.hex_typed)
        self.chv = []
        for i, nm in enumerate('RGB'):
            ttk.Label(right, text=nm).grid(row=3 + i, column=0, sticky='w')
            v = tk.StringVar()
            sp = ttk.Spinbox(right, textvariable=v, from_=0, to=255, increment=1, width=6, command=self.ch_typed)
            sp.grid(row=3 + i, column=1, columnspan=3, sticky='w', pady=2)
            sp.bind('<Return>', self.ch_typed)
            sp.bind('<FocusOut>', self.ch_typed)
            self.chv.append(v)
        ttk.Button(right, text='Pick from screen', command=self.pick_screen).grid(row=6, column=0, columnspan=4, sticky='ew', pady=(12, 3))
        ttk.Button(right, text='Pick from picture\u2026', command=self.pick_picture).grid(row=7, column=0, columnspan=4, sticky='ew')
        low = ttk.Frame(self, padding=(12, 0, 12, 12))
        low.pack(fill='x')
        self.swatch_row(low, 'This planet', app.planet_colours(), 0)
        self.swatch_row(low, 'Recent', recent_colours(), 1)
        bar = ttk.Frame(low)
        bar.grid(row=2, column=0, columnspan=2, sticky='e', pady=(10, 0))
        ttk.Button(bar, text='Cancel', command=self.cancel).pack(side='right')
        ttk.Button(bar, text='OK', style='Accent.TButton', command=self.ok).pack(side='right', padx=6)
        self.bind('<Escape>', lambda e: self.cancel())
        self.bind('<Return>', lambda e: self.ok() if not isinstance(self.focus_get(), (ttk.Entry, ttk.Spinbox)) else None)
        self.protocol('WM_DELETE_WINDOW', self.cancel)
        self.draw_sv()
        self.refresh(notify=False)
        self.update_idletasks()
        try:
            x = app.winfo_rootx() + max(0, (app.winfo_width() - self.winfo_reqwidth()) // 2)
            y = app.winfo_rooty() + max(0, (app.winfo_height() - self.winfo_reqheight()) // 3)
            self.geometry('+%d+%d' % (x, y))
        except tk.TclError:
            pass
        self.grab_set()
        self.focus_set()

    def swatch_row(self, parent, label, cols, row):
        ttk.Label(parent, text=label, style='Dim.TLabel', width=11).grid(row=row, column=0, sticky='w', pady=(6, 0))
        fr = ttk.Frame(parent)
        fr.grid(row=row, column=1, sticky='w', pady=(6, 0))
        if not cols:
            ttk.Label(fr, text='\u2013', style='Dim.TLabel').pack(side='left')
        for c in cols[:14]:
            c = [int(round(float(v))) for v in c][:3]
            lab = tk.Label(fr, bg=hexcol(c), width=2, relief='solid', bd=1, cursor='hand2')
            lab.pack(side='left', padx=(0, 3))
            lab.bind('<Button-1>', lambda e, c=c: self.set_rgb(c))

    def draw_sv(self):
        self.sv_tk = ImageTk.PhotoImage(sv_image(self.h))
        self.sv.itemconfigure(self.sv_img, image=self.sv_tk)

    def refresh(self, notify=True):
        x, y = self.s * 255, (1 - self.v) * 255
        self.sv.coords(self.sv_mark, x - 6, y - 6, x + 6, y + 6)
        self.sv.coords(self.sv_mark2, x - 7, y - 7, x + 7, y + 7)
        hy = self.h * 255
        self.hue.coords(self.hue_mark, 1, hy - 3, 27, hy + 3)
        self.cmp.itemconfigure(self.cmp_old, fill=hexcol(self.initial))
        self.cmp.itemconfigure(self.cmp_new, fill=hexcol(self.rgb))
        self.hexv.set(hexcol(self.rgb))
        for v, c in zip(self.chv, self.rgb):
            v.set(str(c))
        if notify and self.live:
            self.live(list(self.rgb))

    def from_hsv(self):
        self.rgb = [int(round(c * 255)) for c in colorsys.hsv_to_rgb(self.h, self.s, self.v)]
        self.refresh()

    def set_rgb(self, rgb):
        self.rgb = [int(max(0, min(255, round(float(c))))) for c in rgb][:3]
        h, s, v = colorsys.rgb_to_hsv(*[c / 255.0 for c in self.rgb])
        if s > 0 and v > 0:
            if abs(h - self.h) > 1e-4:
                self.h = h
                self.draw_sv()
        self.s, self.v = s, v
        self.refresh()

    def sv_click(self, e):
        self.s = min(max(e.x / 255.0, 0.0), 1.0)
        self.v = 1 - min(max(e.y / 255.0, 0.0), 1.0)
        self.from_hsv()

    def hue_click(self, e):
        self.h = min(max(e.y / 256.0, 0.0), 0.999)
        self.draw_sv()
        self.from_hsv()

    def hex_typed(self, _e=None):
        t = self.hexv.get().strip().lstrip('#')
        if len(t) == 3:
            t = ''.join(ch * 2 for ch in t)
        try:
            if len(t) != 6:
                raise ValueError
            c = [int(t[i:i + 2], 16) for i in (0, 2, 4)]
        except ValueError:
            self.hexv.set(hexcol(self.rgb))
            return
        if c != self.rgb:
            self.set_rgb(c)

    def ch_typed(self, _e=None):
        try:
            c = [int(round(float(v.get().replace(',', '.')))) for v in self.chv]
        except ValueError:
            self.refresh(notify=False)
            return
        c = [max(0, min(255, x)) for x in c]
        if c != self.rgb:
            self.set_rgb(c)

    def picked(self, rgb):
        try:
            self.deiconify()
            self.lift()
            self.grab_set()
            self.focus_set()
        except tk.TclError:
            return
        if rgb:
            self.set_rgb(rgb)

    def pick_screen(self):
        try:
            from PIL import ImageGrab
        except Exception as ex:
            messagebox.showerror('Pick from screen', 'Screen capture is not available here.\n%s' % ex, parent=self)
            return
        self.grab_release()
        self.withdraw()

        def grab():
            try:
                img = ImageGrab.grab().convert('RGB')
            except Exception as ex:
                self.picked(None)
                messagebox.showerror('Pick from screen', 'Could not capture the screen.\n%s' % ex, parent=self)
                return
            PixelPicker(self, img, self.picked, fullscreen=True)
        self.after(250, grab)

    def pick_picture(self):
        path = filedialog.askopenfilename(parent=self, title='Picture to pick a colour from',
                                          filetypes=[('Pictures', '*.png *.jpg *.jpeg *.bmp *.tga *.webp *.dds'), ('All files', '*.*')])
        if not path:
            return
        try:
            img = Image.open(path).convert('RGB')
        except Exception as ex:
            messagebox.showerror('Could not open picture', str(ex), parent=self)
            return
        self.grab_release()
        PixelPicker(self, img, self.picked, fullscreen=False)

    def ok(self):
        self.ch_typed()
        self.result = list(self.rgb)
        self.grab_release()
        self.destroy()

    def cancel(self):
        self.result = None
        self.grab_release()
        self.destroy()


def pick_colour(app, initial, title='Pick a colour', live=None, restore=None):
    snap = getattr(app, 'snapshot', None)
    if snap:
        snap()
    dlg = ColourPicker(app, initial, title, live)
    app.wait_window(dlg)
    res = dlg.result
    same = res is not None and list(res) == [int(round(float(v))) for v in initial][:3]
    if res is None or same:
        if snap and app.history:
            app.history.pop()
            if not app.history:
                app.undo_btn.configure(state='disabled')
        if restore:
            restore()
        return None
    remember_colour(res)
    return res


class Swatch:
    def __init__(self, app, parent, path):
        self.app, self.path = app, path
        self.lab = tk.Label(parent, width=6, relief='solid', bd=1, cursor='hand2')
        self.lab.bind('<Button-1>', self.pick)
        app.swatches.append(self)

    def refresh(self):
        self.lab.configure(bg=hexcol(getp(self.app.P, self.path)))

    def pick(self, _e=None):
        old = copy.deepcopy(getp(self.app.P, self.path))

        def live(v):
            setp(self.app.P, self.path, v)
            self.refresh()
            self.app.changed()

        def restore():
            live(old)
        c = pick_colour(self.app, old, live=live, restore=restore)
        if c:
            live(c)


def num(label, key, lo, hi, inc, fmt, default=0.0, isint=False, width=7):
    def g(it):
        return it[key] if isinstance(it, list) else it.get(key, default)

    def s(it, v):
        it[key] = v
    return {'label': label, 'get': g, 'set': s, 'lo': lo, 'hi': hi, 'inc': inc, 'fmt': fmt, 'int': isint, 'width': width}


def colf(label, key, default=(128, 128, 128)):
    def g(it):
        return it[key] if isinstance(it, list) else it.get(key, list(default))

    def s(it, v):
        it[key] = v
    return {'label': label, 'get': g, 'set': s, 'kind': 'color'}


def spinf(label, key, default=1):
    def g(it):
        return it.get(key, default)

    def s(it, v):
        it[key] = v
    return {'label': label, 'get': g, 'set': s, 'kind': 'choice', 'values': ['1', '-1'], 'conv': int}



class ListEditor:
    def __init__(self, app, parent, items_fn, fields, new_item, card=False, cols=5, add_text='Add', notify=None, registry=None, on_remove=None):
        self.app, self.items_fn, self.fields, self.new_item, self.card, self.cols = app, items_fn, fields, new_item, card, cols
        self.notify = notify or app.changed
        self.on_remove = on_remove
        self.frame = ttk.Frame(parent)
        self.body = ttk.Frame(self.frame)
        self.body.pack(fill='x')
        self.bar = ttk.Frame(self.frame)
        self.bar.pack(fill='x', pady=(6, 0))
        ttk.Button(self.bar, text=add_text, command=self.add).pack(side='left')
        (registry if registry is not None else app.editors).append(self)

    def rebuild(self):
        for w in self.body.winfo_children():
            w.destroy()
        items = self.items_fn()
        if not self.card:
            if items:
                for j, f in enumerate(self.fields):
                    ttk.Label(self.body, text=f['label'], style='Dim.TLabel').grid(row=0, column=j, padx=4, sticky='w')
            for i, it in enumerate(items):
                for j, f in enumerate(self.fields):
                    self.widget(self.body, it, f).grid(row=i + 1, column=j, padx=4, pady=2, sticky='w')
                ttk.Button(self.body, text='✕', width=3, style='Small.TButton',
                           command=lambda i=i: self.remove(i)).grid(row=i + 1, column=len(self.fields), padx=4)
        else:
            for i, it in enumerate(items):
                card = ttk.Frame(self.body, style='Card.TFrame', padding=8)
                card.pack(fill='x', pady=4)
                for j, f in enumerate(self.fields):
                    r, c = divmod(j, self.cols)
                    ttk.Label(card, text=f['label'], style='CardDim.TLabel').grid(row=r * 2, column=c, sticky='w', padx=4)
                    self.widget(card, it, f).grid(row=r * 2 + 1, column=c, sticky='w', padx=4, pady=(0, 6))
                ttk.Button(card, text='✕', width=3, style='Small.TButton',
                           command=lambda i=i: self.remove(i)).grid(row=1, column=self.cols, padx=(2, 0), sticky='w')

    def widget(self, parent, item, f):
        kind = f.get('kind', 'num')
        if kind == 'custom':
            return f['make'](parent, item)
        if kind == 'color':
            lab = tk.Label(parent, bg=hexcol(f['get'](item)), width=6, relief='solid', bd=1, cursor='hand2')

            def pick(_e=None, lab=lab):
                old = copy.deepcopy(f['get'](item))

                def live(v):
                    f['set'](item, v)
                    try:
                        lab.configure(bg=hexcol(v))
                    except tk.TclError:
                        pass
                    self.notify()

                def restore():
                    live(old)
                c = pick_colour(self.app, old, live=live, restore=restore)
                if c:
                    live(c)
            lab.bind('<Button-1>', pick)
            return lab
        if kind == 'choice':
            var = tk.StringVar(value=str(f['get'](item)))
            cb = ttk.Combobox(parent, textvariable=var, values=f['values'], width=f.get('width', 4), state='readonly')

            def sel(_e=None, var=var):
                self.app.snapshot()
                f['set'](item, f.get('conv', str)(var.get()))
                self.notify()
            cb.bind('<<ComboboxSelected>>', sel)
            return cb
        fmt = f['fmt']
        var = tk.StringVar(value=fmt % f['get'](item))
        sp = ttk.Spinbox(parent, textvariable=var, from_=f['lo'], to=f['hi'], increment=f['inc'], width=f['width'], format=fmt)

        def commit(_e=None, var=var):
            try:
                v = float(var.get().replace(',', '.'))
            except ValueError:
                var.set(fmt % f['get'](item))
                return
            if f.get('int'):
                v = int(round(v))
            if v != f['get'](item):
                self.app.snapshot()
                f['set'](item, v)
                self.notify()
        sp.configure(command=commit)
        sp.bind('<Return>', commit)
        sp.bind('<FocusOut>', commit)
        return sp

    def add(self):
        self.app.snapshot()
        self.items_fn().append(self.new_item())
        self.rebuild()
        self.notify()

    def remove(self, i):
        items = self.items_fn()
        if self.items_fn is self.app.stops_fn and len(items) <= 1:
            return
        self.app.snapshot()
        items.pop(i)
        if self.on_remove:
            self.on_remove(i)
        self.rebuild()
        self.notify()



FEAT_NAMES = ['Crater', 'Basin', 'Dome', 'Mountain', 'Plateau']
PALETTES = {
    'carbon': [[34, 32, 31], [44, 42, 40], [52, 50, 47], [58, 55, 52], [64, 61, 57], [70, 67, 63], [78, 75, 70]],
    'stony': [[86, 78, 70], [104, 94, 84], [118, 108, 96], [128, 117, 104], [136, 124, 110], [144, 132, 118], [154, 142, 128]],
    'metal': [[88, 88, 90], [104, 104, 106], [118, 117, 116], [128, 127, 125], [138, 137, 134], [148, 147, 144], [162, 160, 156]],
    'rusty': [[78, 54, 42], [102, 70, 52], [124, 86, 62], [136, 96, 70], [146, 106, 78], [154, 118, 92], [166, 134, 110]],
    'ice': [[150, 158, 166], [176, 182, 190], [196, 202, 208], [206, 211, 216], [214, 219, 224], [222, 226, 230], [232, 236, 240]],
    'grey': [[66, 66, 68], [84, 84, 84], [100, 98, 96], [110, 108, 104], [120, 118, 114], [130, 128, 124], [142, 140, 136]],
    'olive': [[64, 62, 52], [82, 80, 66], [98, 96, 78], [108, 104, 86], [118, 112, 94], [126, 120, 102], [138, 132, 116]],
}
PAL_LEVELS = (-1.0, -0.08, 0.0, 0.1, 0.35, 0.65, 0.9)


class OptSwatch:
    def __init__(self, app, parent, path, auto_rgb, auto_text='auto'):
        self.app, self.path, self.auto_rgb = app, path, auto_rgb
        self.frame = ttk.Frame(parent)
        self.lab = tk.Label(self.frame, width=6, relief='solid', bd=1, cursor='hand2')
        self.lab.pack(side='left')
        self.lab.bind('<Button-1>', self.pick)
        self.note = ttk.Label(self.frame, text=auto_text, style='Dim.TLabel')
        self.btn = ttk.Button(self.frame, text='Auto', style='Small.TButton', command=self.reset)
        app.swatches.append(self)

    def refresh(self):
        v = getp(self.app.P, self.path)
        self.lab.configure(bg=hexcol(v if v is not None else self.auto_rgb))
        self.note.pack_forget()
        self.btn.pack_forget()
        if v is None:
            self.note.pack(side='left', padx=(6, 0))
        else:
            self.btn.pack(side='left', padx=(6, 0))

    def pick(self, _e=None):
        old = copy.deepcopy(getp(self.app.P, self.path))

        def live(v):
            setp(self.app.P, self.path, v)
            self.refresh()
            self.app.changed()

        def restore():
            live(old)
        c = pick_colour(self.app, old if old is not None else self.auto_rgb, live=live, restore=restore)
        if c:
            live(c)

    def reset(self):
        self.app.snapshot()
        setp(self.app.P, self.path, None)
        self.refresh()
        self.app.changed()


def sample_line(arr, x1, y1, x2, y2, n, gain, box):
    H, W, _ = arr.shape
    out = []
    for i in range(n):
        t = i / max(n - 1, 1)
        x = int(round(x1 + (x2 - x1) * t)); y = int(round(y1 + (y2 - y1) * t))
        blk = arr[max(0, y - box):min(H, y + box + 1), max(0, x - box):min(W, x + box + 1)].reshape(-1, 3)
        out.append([int(round(v)) for v in np.clip(blk.mean(0) * gain, 0, 255)])
    return out


class SampleWin(tk.Toplevel):
    def __init__(self, app, path):
        super().__init__(app)
        self.app = app
        self.title('Colours from a picture')
        self.configure(bg=BG)
        self.src = Image.open(path).convert('RGB')
        self.arr = np.asarray(self.src).astype(np.float32)
        iw, ih = self.src.size
        self.s = min(900 / iw, 640 / ih)
        disp = self.src.resize((max(1, int(iw * self.s)), max(1, int(ih * self.s))), Image.LANCZOS)
        self.tkimg = ImageTk.PhotoImage(disp)
        left = ttk.Frame(self, padding=10)
        left.pack(side='left', fill='both', expand=True)
        ttk.Label(left, text='Click the LOW end, then the HIGH end of a line across the picture.',
                  style='Head.TLabel').pack(anchor='w')
        ttk.Label(left, text='For example from a dark crater floor up to a bright ridge. The colours along the line '
                             'become the colours by height.', style='Dim.TLabel').pack(anchor='w', pady=(0, 8))
        self.cv = tk.Canvas(left, width=disp.width, height=disp.height, bg='black', highlightthickness=0, cursor='crosshair')
        self.cv.pack()
        self.cv.create_image(0, 0, image=self.tkimg, anchor='nw')
        self.cv.bind('<Button-1>', self.click)
        right = ttk.Frame(self, padding=10)
        right.pack(side='left', fill='y')
        P = app.P
        hs = [st[0] for st in P['colors']['stops']]
        self.land = tk.BooleanVar(value=bool(P['shape']['ocean']))
        top = max([h for h in hs if h > 0] + [float(P['relief']['high']) * 0.75])
        self.n = tk.IntVar(value=6)
        self.gain = tk.DoubleVar(value=1.0)
        self.box = tk.IntVar(value=4)
        self.h0 = tk.DoubleVar(value=0.0 if self.land.get() else min(hs))
        self.h1 = tk.DoubleVar(value=round(top))
        rows = [('Colours', self.n, 2, 16, 1), ('Brightness', self.gain, 0.5, 2.0, 0.02), ('Averaging (px)', self.box, 1, 16, 1),
                ('Low end height (m)', self.h0, -10000, 10000, 10), ('High end height (m)', self.h1, -10000, 10000, 10)]
        for i, (lab, var, lo, hi, inc) in enumerate(rows):
            ttk.Label(right, text=lab).grid(row=i, column=0, sticky='w', pady=3)
            sp = ttk.Spinbox(right, textvariable=var, from_=lo, to=hi, increment=inc, width=8, command=self.draw)
            sp.grid(row=i, column=1, padx=6, pady=3)
            sp.bind('<Return>', self.draw)
            sp.bind('<FocusOut>', self.draw)
        ttk.Checkbutton(right, text='Keep the colours below 0 m', variable=self.land,
                        command=self.draw).grid(row=5, column=0, columnspan=2, sticky='w', pady=8)
        self.strip = tk.Canvas(right, width=90, height=300, bg=BG, highlightthickness=1, highlightbackground=LINE)
        self.strip.grid(row=6, column=0, columnspan=2, pady=8)
        bar = ttk.Frame(right)
        bar.grid(row=7, column=0, columnspan=2, sticky='ew', pady=(8, 0))
        ttk.Button(bar, text='Clear', command=self.clear).pack(side='left')
        self.use_btn = ttk.Button(bar, text='Use these colours', style='Accent.TButton', command=self.use, state='disabled')
        self.use_btn.pack(side='left', padx=6)
        self.pts = []
        self.stripimg = None
        self.transient(app)

    def click(self, e):
        if len(self.pts) >= 2:
            self.pts = []
        self.pts.append((e.x / self.s, e.y / self.s))
        self.draw()

    def clear(self):
        self.pts = []
        self.draw()

    def compute(self):
        (x1, y1), (x2, y2) = self.pts
        n = max(2, min(16, int(self.n.get())))
        cols = sample_line(self.arr, x1, y1, x2, y2, n, float(self.gain.get()), max(1, int(self.box.get())))
        h0, h1 = float(self.h0.get()), float(self.h1.get())
        if self.land.get():
            h0 = max(h0, 0.0)
        if h1 <= h0:
            h1 = h0 + 100
        new = [[round(h0 + (h1 - h0) * i / (n - 1)), c] for i, c in enumerate(cols)]
        if self.land.get():
            keep = [copy.deepcopy(st) for st in self.app.P['colors']['stops'] if st[0] < min(0.0, h0)]
            new = keep + new
        return new

    def draw(self, _e=None):
        self.cv.delete('mark')
        for x, y in self.pts:
            self.cv.create_oval(x * self.s - 5, y * self.s - 5, x * self.s + 5, y * self.s + 5, outline=ACC, width=2, tags='mark')
        self.strip.delete('all')
        if len(self.pts) == 2:
            (x1, y1), (x2, y2) = self.pts
            self.cv.create_line(x1 * self.s, y1 * self.s, x2 * self.s, y2 * self.s, fill=ACC, width=2, dash=(6, 4), tags='mark')
            try:
                st = self.compute()
            except Exception:
                return
            hs = np.array([a[0] for a in st], float)
            cs = np.array([a[1] for a in st], float)
            yy = np.linspace(hs.max(), hs.min(), 300)
            img = np.stack([np.interp(yy, hs, cs[:, i]) for i in range(3)], -1)
            img = np.repeat(img[:, None, :], 90, 1)
            self.stripimg = ImageTk.PhotoImage(Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)))
            self.strip.create_image(0, 0, image=self.stripimg, anchor='nw')
            self.use_btn.configure(state='normal')
        else:
            self.use_btn.configure(state='disabled')

    def use(self):
        st = self.compute()
        self.app.snapshot()
        self.app.P['colors']['stops'] = st
        self.app.refresh_all()
        self.app.changed()
        self.destroy()


class ExportDialog(tk.Toplevel):
    KINDS = (('height', 'Height map'), ('heightfine', 'Fine height map'), ('color', 'Colour map'),
             ('normal', 'Normal map'), ('preview', 'Preview sheet'), ('config', 'Kopernicus config'))
    SIZES = ['Same as build', '8192 × 4096', '4096 × 2048', '2048 × 1024', '1024 × 512']

    def __init__(self, app, builds):
        super().__init__(app)
        self.app = app
        self.P = copy.deepcopy(app.P)
        self.name = self.P['name']
        self.builds = builds
        self.S = load_settings()
        self.title('Export – %s' % self.name)
        self.configure(bg=BG)
        self.transient(app)
        self.resizable(False, False)
        self.q = queue.Queue()
        f = ttk.Frame(self, padding=18)
        f.pack(fill='both', expand=True)
        ttk.Label(f, text='Export %s' % self.name, style='Head.TLabel').grid(row=0, column=0, columnspan=4, sticky='w', pady=(0, 10))
        ttk.Label(f, text='From build').grid(row=1, column=0, sticky='w', pady=4)
        self.v_build = tk.StringVar()
        labels = ['%s × %d' % (r, int(r) // 2) for r in builds]
        cb = ttk.Combobox(f, textvariable=self.v_build, values=labels, width=14, state='readonly')
        cb.grid(row=1, column=1, sticky='w', pady=4)
        cb.bind('<<ComboboxSelected>>', lambda e: self.update_rows())
        pref = app.res.get()
        self.v_build.set(labels[builds.index(pref)] if pref in builds else labels[0])
        ttk.Label(f, text='Folder').grid(row=2, column=0, sticky='w', pady=4)
        self.v_dir = tk.StringVar(value=self.S.get('export_dir') or os.path.join(tr.TOOL, 'export'))
        ttk.Entry(f, textvariable=self.v_dir, width=52).grid(row=2, column=1, columnspan=2, sticky='we', pady=4)
        ttk.Button(f, text='Browse…', command=self.browse).grid(row=2, column=3, padx=(6, 0))
        ttk.Label(f, text='File name', style='Dim.TLabel').grid(row=3, column=1, sticky='w', pady=(12, 2))
        ttk.Label(f, text='Format', style='Dim.TLabel').grid(row=3, column=2, sticky='w', pady=(12, 2))
        self.rows = {}
        defaults = {'height': True, 'heightfine': True, 'color': True, 'normal': True, 'preview': False, 'config': True}
        hstem = self.stem('height')
        names = {'height': hstem, 'heightfine': hstem + 'fine', 'color': self.stem('color'), 'normal': self.stem('normal'),
                 'preview': self.name + '_preview', 'config': self.name + '_kopernicus'}
        for i, (k, lab) in enumerate(self.KINDS):
            on = tk.BooleanVar(value=self.S.get('on_' + k, defaults[k]))
            chk = ttk.Checkbutton(f, text=lab, variable=on)
            chk.grid(row=4 + i, column=0, sticky='w', pady=3)
            v_name = tk.StringVar(value=names[k])
            ttk.Entry(f, textvariable=v_name, width=30).grid(row=4 + i, column=1, sticky='w', pady=3)
            fl = tr.EXPORT_FORMATS[k]
            v_fmt = tk.StringVar(value=self.S.get('fmt_' + k) if self.S.get('fmt_' + k) in fl else fl[0])
            fc = ttk.Combobox(f, textvariable=v_fmt, values=fl, width=27, state='readonly')
            fc.grid(row=4 + i, column=2, sticky='w', pady=3)
            note = ttk.Label(f, text='', style='Dim.TLabel')
            note.grid(row=4 + i, column=3, sticky='w', padx=(6, 0))
            self.rows[k] = (on, chk, v_name, v_fmt, note)
        r = 4 + len(self.KINDS)
        ttk.Label(f, text='Size').grid(row=r, column=0, sticky='w', pady=(12, 4))
        self.v_size = tk.StringVar(value=self.S.get('size') if self.S.get('size') in self.SIZES else self.SIZES[0])
        ttk.Combobox(f, textvariable=self.v_size, values=self.SIZES, width=14, state='readonly').grid(row=r, column=1, sticky='w', pady=(12, 4))
        self.v_flip = tk.BooleanVar(value=self.S.get('flip', True))
        ttk.Checkbutton(f, text='Flip DDS files upside down (KSP needs this)', variable=self.v_flip).grid(row=r + 1, column=0, columnspan=3, sticky='w', pady=4)
        r += 1
        ttk.Label(f, text='Path in config').grid(row=r + 1, column=0, sticky='w', pady=4)
        self.auto_cfg = tr.default_cfg_path(self.v_dir.get())
        self.v_cfg = tk.StringVar(value=self.S.get('cfg_path') or self.auto_cfg)
        ttk.Entry(f, textvariable=self.v_cfg, width=40).grid(row=r + 1, column=1, sticky='w', pady=4)
        ttk.Label(f, text='folder under GameData where the textures go', style='Dim.TLabel').grid(row=r + 1, column=2, columnspan=2, sticky='w', padx=(6, 0))
        ttk.Label(f, text='Height map: an 8-bit greyscale DDS like the ones Kopernicus’ VertexHeightMap reads. 8 bits only '
                          'give 256 height steps, so the fine height map holds what falls between the steps. Add it as a '
                          'second VertexHeightMap and the ground is smooth instead of terraced. The Kopernicus config '
                          'has both, with the right offset and deformity, the VertexHeightOblateAdvanced node for the '
                          'shape, the colour and normal parts, and the radius, gravity and time warp heights. Paste its '
                          'nodes into your body’s Body. After changing the shape, delete the body’s Kopernicus cache file '
                          'so the map view picks up the new shape.',
                  style='Dim.TLabel', wraplength=640, justify='left').grid(row=r + 2, column=0, columnspan=4, sticky='w', pady=(8, 0))
        self.stat = ttk.Label(f, text='', style='Dim.TLabel', wraplength=640, justify='left')
        self.stat.grid(row=r + 3, column=0, columnspan=4, sticky='w', pady=(10, 0))
        bar = ttk.Frame(f)
        bar.grid(row=r + 4, column=0, columnspan=4, sticky='e', pady=(14, 0))
        self.open_btn = ttk.Button(bar, text='Open folder', command=lambda: open_folder(self.v_dir.get()), state='disabled')
        self.open_btn.pack(side='left', padx=(0, 6))
        self.go_btn = ttk.Button(bar, text='Export', style='Accent.TButton', command=self.go)
        self.go_btn.pack(side='left', padx=(0, 6))
        self.close_btn = ttk.Button(bar, text='Close', command=self.destroy)
        self.close_btn.pack(side='left')
        self.update_rows()
        self.update_idletasks()
        w, h = self.winfo_reqwidth(), self.winfo_reqheight()
        x = app.winfo_rootx() + max(0, (app.winfo_width() - w) // 2)
        y = app.winfo_rooty() + max(0, (app.winfo_height() - h) // 3)
        self.geometry('+%d+%d' % (x, y))
        self.grab_set()

    def stem(self, k):
        fn = self.P['files'].get(k) or ''
        return os.path.splitext(os.path.basename(fn))[0] if fn else '%s_%s' % (self.name, k)

    def res(self):
        return self.v_build.get().split(' ')[0]

    def src(self):
        return self.app.out_path(self.res())

    def update_rows(self):
        src = self.src()
        has = {'preview': os.path.isfile(os.path.join(src, self.name + '_preview.png'))}
        for k, (on, chk, v_name, v_fmt, note) in self.rows.items():
            if has.get(k, True):
                chk.state(['!disabled'])
                note.configure(text='')
            else:
                on.set(False)
                chk.state(['disabled'])
                note.configure(text='not in this build')
        st = self.app.is_stale(self.res())
        self.stat.configure(text='Note: the settings changed after this build – the export shows the build, not the new settings.' if st else '')

    def browse(self):
        d = filedialog.askdirectory(parent=self, title='Export to folder', initialdir=self.v_dir.get() if os.path.isdir(self.v_dir.get()) else tr.TOOL)
        if d:
            self.v_dir.set(d)
            new = tr.default_cfg_path(d)
            if self.v_cfg.get().strip() in ('', self.auto_cfg) or tr.gamedata_rel(d):
                self.v_cfg.set(new)
            self.auto_cfg = new

    def go(self):
        folder = self.v_dir.get().strip()
        if not folder:
            messagebox.showerror('Folder', 'Please choose a folder.', parent=self)
            return
        jobs = []
        for k, (on, chk, v_name, v_fmt, note) in self.rows.items():
            if on.get():
                base = v_name.get().strip()
                if not base or any(ch in base for ch in '\\/:*?"<>|'):
                    messagebox.showerror('File name', 'Please give the %s a valid file name.' % dict(self.KINDS)[k].lower(), parent=self)
                    return
                jobs.append((k, base, v_fmt.get()))
        if not jobs:
            messagebox.showinfo('Nothing to export', 'Tick at least one file.', parent=self)
            return
        jobs.sort(key=lambda j: j[0] == 'config')
        targets = [tr.export_target(folder, b, fm) for _, b, fm in jobs]
        exist = [t for t in targets if os.path.exists(t)]
        if exist and not messagebox.askyesno('Replace files?', 'These files already exist and will be replaced:\n\n' + '\n'.join(os.path.basename(x) for x in exist), parent=self):
            return
        sz = self.v_size.get()
        size = None if sz == self.SIZES[0] else int(sz.split(' ')[0])
        if size and size > int(self.res()):
            if not messagebox.askyesno('Bigger than the build', 'This stretches the %s build to %d. It will not gain any detail, '
                                       'it only gets bigger and softer.\n\nFor real detail, build at %d first.\n\nExport anyway?'
                                       % (self.res(), size, size), parent=self):
                return
        cfg = self.v_cfg.get().strip().replace('\\', '/').strip('/')
        self.S.update({'export_dir': folder, 'size': sz, 'flip': bool(self.v_flip.get()),
                       'cfg_path': '' if cfg == self.auto_cfg else cfg})
        for k, (on, chk, v_name, v_fmt, note) in self.rows.items():
            self.S['fmt_' + k] = v_fmt.get()
            if str(chk.state()).find('disabled') < 0:
                self.S['on_' + k] = bool(on.get())
        save_settings(self.S)
        self.go_btn.configure(state='disabled')
        self.close_btn.configure(state='disabled')
        self.stat.configure(text='Exporting…')
        src, name, P, flip = self.src(), self.name, self.P, bool(self.v_flip.get())

        def job():
            try:
                w = tr.export_maps(src, name, P, jobs, folder, size, flip, log=lambda m: self.q.put(('log', m)), cfg_path=cfg)
                self.q.put(('done', w))
            except Exception as ex:
                self.q.put(('err', str(ex)))
        threading.Thread(target=job, daemon=True).start()
        self.after(100, self.poll)

    def poll(self):
        try:
            while True:
                kind, data = self.q.get_nowait()
                if kind == 'log':
                    self.app.log(data)
                elif kind == 'done':
                    self.go_btn.configure(state='normal')
                    self.close_btn.configure(state='normal')
                    self.open_btn.configure(state='normal')
                    self.stat.configure(text='Exported %d file%s to %s' % (len(data), '' if len(data) == 1 else 's', self.v_dir.get()))
                    self.app.status('Exported %s' % self.name)
                    return
                else:
                    self.go_btn.configure(state='normal')
                    self.close_btn.configure(state='normal')
                    self.stat.configure(text='Export failed: ' + data)
                    return
        except queue.Empty:
            pass
        self.after(100, self.poll)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(tr.APP_NAME)
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry('%dx%d+20+20' % (min(1520, sw - 60), min(940, sh - 90)))
        self.minsize(1100, 680)
        self.configure(bg=BG)
        make_style(self)
        self.P = tr.normalize({'name': 'NewWorld'})
        self.preset_file = None
        self.dirty = False
        self.sliders, self.editors, self.swatches, self.checks, self.combos = [], [], [], [], []
        self.proc = None
        self.q = queue.Queue()
        self.view_src = None
        self.pending = None
        self.redraw_id = None
        self.res = tk.StringVar(value='2048')
        self.view = tk.StringVar(value='live')
        self.show = tk.StringVar(value='Colour')
        self.stops_fn = lambda: self.P['colors']['stops']
        self.history = []
        st = load_settings()
        self.live_size = tk.StringVar(value=str(st.get('live_size', 512)) if str(st.get('live_size', 512)) in LIVE_RES else '512')
        self.live_lock = threading.Lock()
        self.live_q = queue.Queue()
        self.live_cache = {}
        self.live_gen = 0
        self.live_req = None
        self.live_thread = None
        self.live_last = None
        self.live_after = None
        self.live_err = None
        self.live_view = None
        self.rot = [0.0, 0.0]
        self.drag = None
        self.view_geom = None
        self.feat_type = tk.StringVar(value='Crater')
        self.place_mode = tk.BooleanVar(value=False)
        self.fdrag = None
        self.body = None
        self.hit = None
        self.shadows = tk.BooleanVar(value=bool(st.get('shadows', True)))
        self.build_ui()
        self.after(150, self.live_poll)
        self.bind('<Control-z>', self.undo)
        names = self.preset_names()
        if names:
            self.load('Potato' if 'Potato' in names else names[0])
        else:
            self.refresh_all()
        self.protocol('WM_DELETE_WINDOW', self.close)
        self.set_icon(self)

    @staticmethod
    def set_icon(win):
        if os.name != 'nt':
            return
        for base in (getattr(sys, '_MEIPASS', ''), tr.TOOL):
            ico = os.path.join(base, 'icon.ico') if base else ''
            if ico and os.path.isfile(ico):
                try:
                    win.iconbitmap(ico)
                except Exception:
                    pass
                return

    def planet_colours(self):
        return [s[1] for s in self.P['colors']['stops']]

    def preset_names(self):
        os.makedirs(tr.PRESETS, exist_ok=True)
        return sorted(f[:-5] for f in os.listdir(tr.PRESETS) if f.endswith('.json'))

    def build_ui(self):
        top = ttk.Frame(self, style='Bar.TFrame', padding=(12, 8))
        top.pack(fill='x')
        ttk.Label(top, text=tr.APP_NAME, style='Title.TLabel').pack(side='left', padx=(0, 20))
        ttk.Label(top, text='Body', style='BarDim.TLabel').pack(side='left')
        self.pick = ttk.Combobox(top, state='readonly', width=22)
        self.pick.pack(side='left', padx=6)
        self.pick.bind('<<ComboboxSelected>>', self.on_pick)
        ttk.Button(top, text='New…', command=self.new).pack(side='left', padx=2)
        ttk.Button(top, text='Save', command=lambda: self.save()).pack(side='left', padx=2)
        ttk.Button(top, text='Save as…', command=self.save_as).pack(side='left', padx=2)
        ttk.Button(top, text='Open output folder', command=self.open_out).pack(side='right')
        self.undo_btn = ttk.Button(top, text='Undo', command=self.undo, state='disabled')
        self.undo_btn.pack(side='left', padx=(18, 2))
        ttk.Button(top, text='Surprise me', command=lambda: self.randomize('all')).pack(side='left', padx=2)
        pw = ttk.PanedWindow(self, orient='horizontal')
        pw.pack(fill='both', expand=True)
        left = ttk.Frame(pw, padding=(8, 4, 0, 8))
        right = ttk.Frame(pw, padding=(8, 8, 12, 8))
        pw.add(left, weight=0)
        pw.add(right, weight=1)
        self.nb = ttk.Notebook(left, width=600)
        self.nb.pack(fill='both', expand=True)
        self.tab_shape()
        self.tab_relief()
        self.tab_landforms()
        self.tab_craters()
        self.tab_features()
        self.tab_colours()
        self.tab_body()
        vb = ttk.Frame(right)
        vb.pack(fill='x')
        self.export_btn = ttk.Button(vb, text='Export…', command=self.export)
        self.export_btn.pack(side='right')
        for val, txt in (('live', 'Live preview'), ('preview', 'Preview sheet'), ('flat', 'Flat map')):
            ttk.Radiobutton(vb, text=txt, value=val, variable=self.view, style='Toolbutton',
                            command=self.update_view).pack(side='left', padx=(0, 4))
        self.live_lab = ttk.Label(vb, text='', style='Dim.TLabel')
        self.live_lab.pack(side='left', padx=(8, 0))
        tb = ttk.Frame(right)
        tb.pack(fill='x', pady=(6, 0))
        ttk.Label(tb, text='Show', style='Dim.TLabel').pack(side='left', padx=(0, 4))
        scb = ttk.Combobox(tb, textvariable=self.show, values=['Colour', 'Height', 'Colour, no shading'], width=17, state='readonly')
        scb.pack(side='left')
        scb.bind('<<ComboboxSelected>>', lambda e: self.update_view(from_live=True))
        lcb = ttk.Combobox(tb, textvariable=self.live_size, values=LIVE_RES, width=5, state='readonly')
        lcb.pack(side='left', padx=(8, 8))
        lcb.bind('<<ComboboxSelected>>', self.live_size_changed)
        ttk.Checkbutton(tb, text='Shadows', variable=self.shadows, command=self.shadows_changed).pack(side='left', padx=(0, 8))
        fcb = ttk.Combobox(tb, textvariable=self.feat_type, values=FEAT_NAMES, width=9, state='readonly')
        fcb.pack(side='right')
        ttk.Checkbutton(tb, text='Place features', variable=self.place_mode, style='Toolbutton',
                        command=self.place_toggled).pack(side='right', padx=(0, 4))
        self.canvas = tk.Canvas(right, bg='#0d0f14', highlightthickness=1, highlightbackground=LINE)
        self.canvas.pack(fill='both', expand=True, pady=(8, 4))
        self.canvas.bind('<Configure>', lambda e: self.schedule_redraw())
        self.canvas.bind('<ButtonPress-1>', self.drag_start)
        self.canvas.bind('<B1-Motion>', self.drag_move)
        self.canvas.bind('<ButtonRelease-1>', self.drag_end)
        self.canvas.bind('<Double-Button-1>', self.drag_reset)
        self.canvas.bind('<Motion>', self.hover)
        self.canvas.bind('<Leave>', lambda e: self.hover_lab.configure(text=''))
        self.canvas.bind('<Button-3>', self.feature_remove_click)
        self.hover_lab = ttk.Label(right, text='', style='Dim.TLabel', font=(MONO, 9))
        self.hover_lab.pack(fill='x')
        sb = ttk.Frame(right)
        sb.pack(fill='x', pady=(4, 0))
        ttk.Label(sb, text='Resolution', style='Dim.TLabel').pack(side='left')
        ttk.Combobox(sb, textvariable=self.res, values=RES, width=7, state='readonly').pack(side='left', padx=6)
        self.res.trace_add('write', lambda *a: (self.update_view(), self.update_res_info()))
        self.build_btn = ttk.Button(sb, text='Build', style='Accent.TButton', command=self.build)
        self.build_btn.pack(side='left')
        self.cancel_btn = ttk.Button(sb, text='Cancel', command=self.cancel, state='disabled')
        self.cancel_btn.pack(side='left', padx=6)
        self.prog = ttk.Progressbar(sb, mode='determinate', maximum=100)
        self.prog.pack(side='left', fill='x', expand=True, padx=(6, 0))
        self.res_info = ttk.Label(right, text='', style='Dim.TLabel', wraplength=820, justify='left')
        self.res_info.pack(fill='x', pady=(6, 0))
        self.stat = ttk.Label(right, text='Ready', style='Dim.TLabel')
        self.stat.pack(fill='x', pady=(2, 0))
        self.logbox = tk.Text(right, height=6, bg=FIELD, fg=DIM, insertbackground=FG, relief='flat',
                              font=(MONO, 9), state='disabled', wrap='none')
        self.logbox.pack(fill='x', pady=(6, 0))

    def rand_bar(self, parent, text, what, hint):
        r = ttk.Frame(parent)
        r.pack(fill='x', pady=(2, 0))
        ttk.Button(r, text=text, command=lambda: self.randomize(what)).pack(side='left', padx=(0, 8))
        ttk.Label(r, text=hint, style='Dim.TLabel').pack(side='left')

    def section(self, parent, text):
        ttk.Label(parent, text=text, style='Head.TLabel').pack(anchor='w', pady=(12, 4))

    def note(self, parent, text):
        ttk.Label(parent, text=text, style='Dim.TLabel', wraplength=540, justify='left').pack(anchor='w')

    def grid_box(self, parent):
        g = ttk.Frame(parent)
        g.pack(fill='x')
        g.columnconfigure(1, weight=1)
        return g

    def check(self, parent, text, path):
        v = tk.BooleanVar()

        def flip():
            self.snapshot()
            setp(self.P, path, bool(v.get()))
            self.changed()
        cb = ttk.Checkbutton(parent, text=text, variable=v, command=flip)
        self.checks.append((v, path))
        return cb

    def swatch_row(self, parent, items):
        r = ttk.Frame(parent)
        r.pack(fill='x', pady=(6, 0))
        for i, (lab, path) in enumerate(items):
            ttk.Label(r, text=lab).pack(side='left', padx=(8 if i == 0 else 22, 10))
            Swatch(self, r, path).lab.pack(side='left')
        return r

    def tab_shape(self):
        sf = ScrollFrame(self.nb)
        self.nb.add(sf, text='Shape')
        p = sf.inner
        self.rand_bar(p, 'Randomize shape', 'shape', 'a new body shape and new highlands (new seed)')
        self.section(p, 'Body shape – VertexHeightOblateAdvanced')
        self.note(p, 'The big shape comes from the VertexHeightOblateAdvanced PQS mod (by Lt_Duckweed), not from the height '
                     'map, so the height map only holds the detail. The preview uses the mod’s own maths, so it matches the game. '
                     'Sizes are times the radius on the Body tab, which is the smallest radius (the neck of a contact binary).')
        self.check(p, 'Use VertexHeightOblateAdvanced (off = a round body)', ('oblate', 'enabled')).pack(anchor='w', padx=8, pady=(4, 4))
        g = self.grid_box(p)
        self.combo(g, 0, 'Mode', ('oblate', 'mode'), [('CustomEllipsoid', 'Ellipsoid'), ('ContactBinary', 'Contact binary'),
                                                   ('PointEquipotential', 'Spinning (point mass)'),
                                                   ('UniformEquipotential', 'Spinning (uniform)'), ('Blend', 'Spinning × ellipsoid')])
        self.shape_lab = ttk.Label(p, text='', style='Dim.TLabel', wraplength=540, justify='left')
        self.shape_lab.pack(anchor='w', padx=8, pady=(6, 0))
        self.shape_frames = {}
        f = self.shape_frames['spin'] = ttk.Frame(p)
        self.section(f, 'Spin')
        self.spin_note = ttk.Label(f, text='', style='Dim.TLabel', wraplength=540, justify='left')
        self.spin_note.pack(anchor='w')
        g = self.grid_box(f)
        Slider(self, g, 0, 'Gravity (g)', ('oblate', 'geeASL'), 0, 0.1, 0.0001, tip='surface gravity in g, also written as geeASL in the config')
        Slider(self, g, 2, 'Rotation period (s)', ('oblate', 'period'), 0, 100000, 10, tip='0 = no spin shape, the body stays round')
        f = self.shape_frames['energy'] = ttk.Frame(p)
        g = self.grid_box(f)
        self.combo(g, 0, 'Energy branch', ('oblate', 'energyMode'), [('Low', 'Low (spheroid)'), ('High', 'High (Jacobi)')])
        f = self.shape_frames['ellipsoid'] = ttk.Frame(p)
        self.section(f, 'Ellipsoid')
        g = self.grid_box(f)
        Slider(self, g, 0, 'a – long axis', ('oblate', 'a'), 1, 3, 0.01, tip='along the map’s left edge and its middle (longitude 0 and 180)')
        Slider(self, g, 2, 'b – middle axis', ('oblate', 'b'), 1, 3, 0.01, tip='at longitude 90 and 270')
        Slider(self, g, 4, 'c – pole to pole', ('oblate', 'c'), 1, 3, 0.01, tip='the mod makes every axis at least 1')
        f = self.shape_frames['contact'] = ttk.Frame(p)
        self.section(f, 'Contact binary')
        g = self.grid_box(f)
        Slider(self, g, 0, 'Big lobe', ('oblate', 'primaryRadius'), 1, 2, 0.01, tip='lobe radius × neck radius, 1 to 2; it sits at the map’s left edge')
        Slider(self, g, 2, 'Small lobe', ('oblate', 'secondaryRadius'), 1, 2, 0.01, tip='at most the big lobe; it sits in the middle of the map')
        self.high_frame = f = ttk.Frame(p)
        f.pack(fill='x')
        self.section(f, 'Highlands and lowlands')
        self.note(f, 'Big raised and sunken areas on top of the shape.')
        g = self.grid_box(f)
        Slider(self, g, 0, 'Highland amount', ('shape', 'land'), 0.02, 0.98, 0.01, tip='share of the surface above 0 m')
        Slider(self, g, 2, 'Highland blobs', ('shape', 'continents'), 0, 12, 1, isint=True, tip='0 = random shapes')
        Slider(self, g, 4, 'Twist', ('shape', 'warp'), 0, 2, 0.05, tip='how bent and stretched the areas are')
        Slider(self, g, 6, 'Edge roughness', ('shape', 'coast'), 0, 1, 0.02)
        self.shape_shown = None

    SHAPE_PARTS = {'CustomEllipsoid': ('ellipsoid',), 'ContactBinary': ('contact',), 'PointEquipotential': ('spin',),
                   'UniformEquipotential': ('spin', 'energy'), 'Blend': ('spin', 'ellipsoid')}
    SPIN_NOTES = {'PointEquipotential': 'A spinning rubble pile: the faster it turns, the more it bulges at the equator, up to a top '
                                        'shape like Bennu or Ryugu. KSP turns the body with this period too.',
                  'UniformEquipotential': 'A spinning body of even density: a smooth spheroid on the low branch, or a long Jacobi '
                                          'ellipsoid on the high branch when it spins fast. KSP turns the body with this period too.',
                  'Blend': 'The spinning point-mass shape times the ellipsoid below. Without a gravity and a period the mod '
                           'keeps the body round. KSP turns the body with this period too.'}

    def shape_sections(self):
        if not hasattr(self, 'shape_frames'):
            return
        o = self.P.get('oblate') or {}
        mode = o.get('mode', 'CustomEllipsoid')
        parts = self.SHAPE_PARTS.get(mode, ()) if o.get('enabled', True) else ()
        self.spin_note.configure(text=self.SPIN_NOTES.get(mode, ''))
        if parts == self.shape_shown:
            return
        self.shape_shown = parts
        for f in self.shape_frames.values():
            f.pack_forget()
        for k in ('spin', 'energy', 'ellipsoid', 'contact'):
            if k in parts:
                self.shape_frames[k].pack(fill='x', before=self.high_frame)

    def shape_info(self):
        self.shape_sections()
        try:
            S = tr.get_shape(tr.normalize(copy.deepcopy(self.P)))
            txt = S.summary()
            if S.active():
                txt += ' · up to %.2f × the radius' % S.dmax
        except Exception as ex:
            txt = str(ex)
        if hasattr(self, 'shape_lab'):
            self.shape_lab.configure(text=txt)

    def tab_relief(self):
        sf = ScrollFrame(self.nb)
        self.nb.add(sf, text='Relief')
        p = sf.inner
        self.rand_bar(p, 'Randomize relief', 'relief', 'new mountain, hill and plains settings')
        self.section(p, 'Height range')
        g = self.grid_box(p)
        Slider(self, g, 0, 'Highest point (m)', ('relief', 'high'), 10, 8000, 10, tip='roughly the tallest hills above the shape, before craters')
        Slider(self, g, 2, 'Lowest point (m)', ('relief', 'low'), -8000, -10, 10, tip='the lowest basins below the shape')
        self.section(p, 'Mountains')
        g = self.grid_box(p)
        Slider(self, g, 0, 'Mountains', ('relief', 'mountains'), 0, 1.5, 0.02)
        Slider(self, g, 1, 'Mountain size', ('relief', 'mountain_size'), 0.3, 3, 0.05, tip='bigger = wider ranges with fewer, larger peaks')
        Slider(self, g, 3, 'Mountain area', ('relief', 'mountain_area'), 0, 1, 0.02)
        Slider(self, g, 4, 'Sharpness', ('relief', 'sharpness'), 0.4, 3, 0.05, tip='low = rounded old mountains, high = sharp jagged peaks')
        self.section(p, 'Hills and plains')
        g = self.grid_box(p)
        Slider(self, g, 0, 'Hills', ('relief', 'hills'), 0, 1.5, 0.02)
        Slider(self, g, 1, 'Hill size', ('relief', 'hill_size'), 0.3, 3, 0.05)
        Slider(self, g, 2, 'Flat plains', ('relief', 'plains'), 0, 1, 0.02, tip='smooths hills and mountains away in large areas')
        Slider(self, g, 4, 'Fine roughness', ('relief', 'roughness'), 0, 1.5, 0.02)
        self.section(p, 'Normal map')
        g = self.grid_box(p)
        Slider(self, g, 0, 'Relief strength', ('normal_strength',), 0, 12, 0.1, tip='how strong the bumps look from orbit (normal map and preview)')

    def tab_landforms(self):
        sf = ScrollFrame(self.nb)
        self.nb.add(sf, text='Landforms')
        p = sf.inner
        self.rand_bar(p, 'Randomize landforms', 'landforms', 'new plateaus, canyons, grooves and domes')
        self.section(p, 'Plateaus')
        self.note(p, 'Raised tablelands with flat tops and steep, ragged edges.')
        g = self.grid_box(p)
        Slider(self, g, 0, 'Plateaus', ('plateaus', 'amount'), 0, 1, 0.02, tip='0 = none, higher = more of the surface')
        Slider(self, g, 2, 'Height (m)', ('plateaus', 'height'), 0, 5000, 10)
        Slider(self, g, 3, 'Size', ('plateaus', 'size'), 0.3, 3, 0.05)
        Slider(self, g, 4, 'Edge steepness', ('plateaus', 'edge'), 0, 1, 0.02, tip='low = gentle slopes up, high = cliffs')
        Slider(self, g, 6, 'Flat tops', ('plateaus', 'flat'), 0, 1, 0.02, tip='how much of the hills and mountains on top are smoothed away')
        self.section(p, 'Canyons')
        self.note(p, 'Long troughs with flat floors and ragged walls. They taper off at both ends.')
        g = self.grid_box(p)
        Slider(self, g, 0, 'Canyons', ('relief', 'canyons'), 0, 1, 0.02, tip='0 = none, higher = more and longer canyons')
        Slider(self, g, 2, 'Depth (m)', ('relief', 'canyon_depth'), 0, 5000, 10)
        Slider(self, g, 3, 'Width (km)', ('relief', 'canyon_width'), 0.1, 50, 0.1)
        self.section(p, 'Grooves and cracks')
        self.note(p, 'Long crossing grooves like the ones on Phobos, cracks in an icy crust, or a network of polygon cells. '
                     'Each one is a groove, with raised edges if you like, and its own colour.')
        g = self.grid_box(p)
        Slider(self, g, 0, 'Cracks', ('cracks', 'amount'), 0, 1, 0.02, tip='0 = none, higher = longer lines / more of the cells')
        self.combo(g, 2, 'Kind', ('cracks', 'style'), [('lines', 'Long lines'), ('cells', 'Polygon cells')])
        Slider(self, g, 3, 'Lines', ('cracks', 'count'), 1, 16, 1, isint=True, tip='long lines only')
        Slider(self, g, 5, 'Bend', ('cracks', 'curvy'), 0, 1, 0.02, tip='long lines only: 0 = straight arcs')
        Slider(self, g, 7, 'Cell size (km)', ('cracks', 'cell_size'), 0.5, 200, 0.5, tip='polygon cells only')
        Slider(self, g, 9, 'Width (km)', ('cracks', 'width'), 0.02, 10, 0.01)
        Slider(self, g, 10, 'Depth (m)', ('cracks', 'depth'), 0, 2000, 5)
        Slider(self, g, 11, 'Raised edges', ('cracks', 'ridges'), 0, 1.5, 0.02, tip='ridges along both sides of each crack')
        Slider(self, g, 13, 'Crack colour amount', ('colors', 'crack_amount'), 0, 1, 0.02)
        self.swatch_row(p, [('Crack colour', ('colors', 'crack_color'))])
        r = ttk.Frame(p)
        r.pack(fill='x', pady=(6, 0))
        ttk.Button(r, text='New groove pattern', command=self.crack_seed).pack(side='left', padx=8)
        self.section(p, 'Domes')
        self.note(p, 'Round domes with a pit at the top, scattered at random (the “volcano” of Terra Studio). Place your own on the Features tab.')
        g = self.grid_box(p)
        Slider(self, g, 0, 'Count', ('volcanoes', 'count'), 0, 40, 1, isint=True)
        Slider(self, g, 1, 'Size (km wide)', ('volcanoes', 'size_km'), 0.2, 100, 0.1)
        Slider(self, g, 2, 'Height (m)', ('volcanoes', 'height'), 10, 8000, 10)
        Slider(self, g, 3, 'Summit crater', ('volcanoes', 'caldera'), 0, 1, 0.02)
        Slider(self, g, 4, 'Size variety', ('volcanoes', 'size_var'), 0, 0.9, 0.02)
        r = ttk.Frame(p)
        r.pack(fill='x', pady=(6, 0))
        ttk.Button(r, text='New dome places', command=self.volcano_seed).pack(side='left', padx=8)

    def combo(self, parent, row, label, path, options):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky='w', padx=(8, 8), pady=(4, 0))
        var = tk.StringVar()
        names = [n for _, n in options]
        cb = ttk.Combobox(parent, textvariable=var, values=names, width=16, state='readonly')
        cb.grid(row=row, column=1, sticky='w', pady=(4, 0))

        def sel(_e=None):
            v = dict((n, k) for k, n in options).get(var.get())
            if v is not None and v != getp(self.P, path):
                self.snapshot()
                setp(self.P, path, v)
                self.changed()
        cb.bind('<<ComboboxSelected>>', sel)
        self.combos.append((var, path, dict(options)))

    def crack_seed(self):
        self.snapshot()
        self.P['cracks']['seed'] = random.randint(1, 99999)
        self.changed()

    def tab_craters(self):
        sf = ScrollFrame(self.nb)
        self.nb.add(sf, text='Craters')
        p = sf.inner
        self.rand_bar(p, 'Randomize craters', 'craters', 'new crater pattern and settings')
        self.section(p, 'Craters')
        self.note(p, 'Many small ones, few big ones, spread evenly over the real surface: the tips of a long body get as '
                     'many per km² as its waist, and a crater is as wide in km wherever it lands. Rims are soft, never '
                     'outlined. Craters smaller than about a pixel are left out of the smaller previews.')
        g = self.grid_box(p)
        Slider(self, g, 0, 'Count', ('craters', 'count'), 0, 20000, 50, isint=True, tip='0 = no craters')
        Slider(self, g, 2, 'Smallest (km wide)', ('craters', 'min_km'), 0.05, 10, 0.01)
        Slider(self, g, 3, 'Largest (km wide)', ('craters', 'max_km'), 0.1, 60, 0.05)
        Slider(self, g, 4, 'Small vs big', ('craters', 'size_mix'), 1.0, 3.0, 0.05, tip='higher = more small craters, fewer big ones')
        Slider(self, g, 6, 'Depth', ('craters', 'depth'), 0, 2.5, 0.05, tip='1 = about as deep as real craters of that size')
        self.section(p, 'Age')
        g = self.grid_box(p)
        Slider(self, g, 0, 'Fresh craters', ('craters', 'fresh'), 0, 1, 0.02, tip='0 = all old and worn down, 1 = all sharp and young')
        Slider(self, g, 2, 'Bright ejecta', ('craters', 'ejecta'), 0, 1, 0.02, tip='light blankets around young craters')
        Slider(self, g, 4, 'Ray streaks', ('craters', 'rays'), 0, 1, 0.02, tip='how much of the ejecta runs out in soft rays')
        r = ttk.Frame(p)
        r.pack(fill='x', pady=(10, 0))
        ttk.Button(r, text='New crater pattern', command=self.crater_seed).pack(side='left', padx=8)
        self.section(p, 'Crater colours')
        self.note(p, 'Also used by the craters and basins you place yourself. Click a colour box to change it.')
        g = self.grid_box(p)
        Slider(self, g, 0, 'Floor colour amount', ('colors', 'crater_floor_amount'), 0, 1, 0.02, tip='dark (or light) floors, strongest in big craters and basins')
        self.swatch_row(p, [('Floor colour', ('colors', 'crater_floor'))])
        r = ttk.Frame(p)
        r.pack(fill='x', pady=(6, 0))
        ttk.Label(r, text='Ejecta colour').pack(side='left', padx=(8, 10))
        OptSwatch(self, r, ('colors', 'ejecta_color'), [214, 210, 202], 'auto = a lighter version of the ground').frame.pack(side='left')

    def tab_colours(self):
        sf = ScrollFrame(self.nb)
        self.nb.add(sf, text='Colours')
        p = sf.inner
        self.rand_bar(p, 'Randomize colours', 'colours', 'a new palette (carbon, stony, metal, rusty, icy, grey, olive)')
        self.section(p, 'Colour by height')
        self.note(p, 'Each colour sits at its height in metres above or below the shape. Heights in between blend '
                     'smoothly. Click any colour box for the colour picker: colour square, '
                     'hex, eyedropper for anything on your screen, colours from a picture, recent colours.')
        ed = ListEditor(self, p, self.stops_fn,
                        [num('Height (m)', 0, -10000, 10000, 10, '%.0f', width=9), colf('Colour', 1)],
                        lambda: [0.0, [128, 128, 120]], add_text='Add colour', notify=self.changed)
        ed.frame.pack(fill='x', pady=6)
        ttk.Button(ed.bar, text='Sort', command=self.sort_stops).pack(side='left', padx=6)
        ttk.Button(ed.bar, text='Colours from picture…', command=self.sample).pack(side='left')
        g = self.grid_box(p)
        Slider(self, g, 0, 'Height blur (m)', ('colors', 'jitter'), 0, 1500, 10, tip='mixes the colours up and down a bit so they don’t follow contour lines')
        self.section(p, 'Patches')
        g = self.grid_box(p)
        Slider(self, g, 0, 'Patches', ('colors', 'patches'), 0, 1.5, 0.02)
        Slider(self, g, 1, 'Patch size', ('colors', 'patch_size'), 0.3, 3, 0.05)
        self.swatch_row(p, [('Patch colour', ('colors', 'patch_color'))])
        self.section(p, 'Rock on steep slopes')
        self.note(p, 'Slopes are measured against the shape, so the sides of the lobes don’t all turn to rock.')
        g = self.grid_box(p)
        Slider(self, g, 0, 'Rock starts at (°)', ('colors', 'rock_slope', 0), 0, 60, 0.5)
        Slider(self, g, 1, 'All rock at (°)', ('colors', 'rock_slope', 1), 1, 80, 0.5)
        Slider(self, g, 2, 'Rock amount', ('colors', 'rock_amount'), 0, 1, 0.02)
        self.swatch_row(p, [('Rock colour', ('colors', 'rock'))])
        self.section(p, 'Frost')
        g = self.grid_box(p)
        Slider(self, g, 0, 'North frost from (° latitude)', ('colors', 'cap_north'), 30, 90, 0.5, tip='90 = none')
        Slider(self, g, 2, 'South frost from (° latitude)', ('colors', 'cap_south'), 30, 90, 0.5, tip='90 = none')
        Slider(self, g, 4, 'Frost edge raggedness', ('colors', 'cap_ragged'), 0, 1, 0.02)
        Slider(self, g, 5, 'Frost above (m)', ('colors', 'snow_line'), 0, 99000, 10, tip='frost on everything above this height, set it high for none')
        Slider(self, g, 7, 'No frost on slopes over (°)', ('colors', 'snow_slope'), 5, 90, 0.5)
        self.swatch_row(p, [('Frost colour', ('colors', 'ice'))])
        self.section(p, 'Dome rock')
        self.note(p, 'Colour of the domes, the random ones and the ones you place.')
        g = self.grid_box(p)
        Slider(self, g, 0, 'Amount', ('colors', 'volcano_amount'), 0, 1, 0.02)
        self.swatch_row(p, [('Volcanic rock', ('colors', 'volcano_color'))])
        self.section(p, 'Final look')
        self.note(p, 'For the whole colour map.')
        g = self.grid_box(p)
        Slider(self, g, 0, 'Brightness', ('colors', 'brightness'), -0.5, 0.5, 0.01)
        Slider(self, g, 1, 'Contrast', ('colors', 'contrast'), 0.4, 2, 0.01)
        Slider(self, g, 2, 'Saturation', ('colors', 'saturation'), 0, 2, 0.01, tip='0 = grey, 1 = as set, 2 = very colourful')

    def tab_features(self):
        sf = ScrollFrame(self.nb)
        self.nb.add(sf, text='Features')
        p = sf.inner
        self.section(p, 'Your own features')
        self.note(p, 'Craters, basins, domes, mountains and plateaus exactly where you want them. Turn on Place features '
                     '(above the preview), pick the kind, then click the flat map or the body to add one. Drag to '
                     'move it, right-click to remove it. Height 0 = a size that fits how wide it is. Sizes are km on '
                     'the real surface. Longitude is counted from the left edge of the map.')
        r = ttk.Frame(p)
        r.pack(fill='x', pady=(8, 4))
        ttk.Label(r, text='Kind to add').pack(side='left', padx=(8, 8))
        cb = ttk.Combobox(r, textvariable=self.feat_type, values=FEAT_NAMES, width=10, state='readonly')
        cb.pack(side='left')
        ttk.Checkbutton(r, text='Place on the map', variable=self.place_mode, style='Toolbutton',
                        command=self.place_toggled).pack(side='left', padx=10)
        ed = ListEditor(self, p, lambda: self.P['features'],
                        [{'label': 'Kind', 'kind': 'choice', 'values': FEAT_NAMES, 'width': 9,
                          'get': lambda it: it['type'].capitalize(), 'set': lambda it, v: it.__setitem__('type', v.lower())},
                         num('Latitude', 'lat', -90, 90, 0.5, '%.1f'),
                         num('Longitude', 'lon', 0, 360, 0.5, '%.1f'),
                         num('Size (km)', 'size', 0.02, 500, 0.1, '%.2f'),
                         num('Height or depth (m)', 'height', 0, 10000, 10, '%.0f', width=8),
                         num('Fresh', 'fresh', 0, 1, 0.05, '%.2f', width=5)],
                        self.new_feature, card=True, cols=3, add_text='Add feature', notify=self.changed)
        ed.frame.pack(fill='x', pady=6)
        self.feat_ed = ed
        self.note(p, 'Fresh: for craters and basins, 1 = sharp and young with bright ejecta, 0 = old and worn down. '
                     'A plateau rises by its height above the ground around it, with a flat top and steep, ragged edges.')

    def new_feature(self):
        t = self.feat_type.get().lower()
        f = tr.default_feature(t if t in tr.FEATURE_TYPES else 'crater', float(self.P['radius']))
        f['lon'] = round((float(self.P['preview']['view_lon']) + self.rot[0]) % 360, 1)
        f['lat'] = round(max(-60.0, min(60.0, float(self.P['preview']['view_lat']) + self.rot[1])), 1)
        return f

    def tab_body(self):
        sf = ScrollFrame(self.nb)
        self.nb.add(sf, text='Body')
        p = sf.inner
        self.section(p, 'Name and randomness')
        g = ttk.Frame(p)
        g.pack(fill='x')
        self.v_name = tk.StringVar()
        self.v_seed = tk.StringVar()
        self.v_radius = tk.StringVar()
        ttk.Label(g, text='Name').grid(row=0, column=0, sticky='w', padx=8, pady=4)
        en = ttk.Entry(g, textvariable=self.v_name, width=24)
        en.grid(row=0, column=1, sticky='w', pady=4)
        en.bind('<Return>', self.commit_name)
        en.bind('<FocusOut>', self.commit_name)
        ttk.Label(g, text='Seed').grid(row=1, column=0, sticky='w', padx=8, pady=4)
        es = ttk.Entry(g, textvariable=self.v_seed, width=10)
        es.grid(row=1, column=1, sticky='w', pady=4)
        es.bind('<Return>', self.commit_seed)
        es.bind('<FocusOut>', self.commit_seed)
        ttk.Button(g, text='New random seed', command=self.random_seed).grid(row=1, column=2, padx=6)
        ttk.Label(g, text='Radius (m)').grid(row=2, column=0, sticky='w', padx=8, pady=4)
        er = ttk.Entry(g, textvariable=self.v_radius, width=12)
        er.grid(row=2, column=1, sticky='w', pady=4)
        er.bind('<Return>', self.commit_radius)
        er.bind('<FocusOut>', self.commit_radius)
        ttk.Label(g, text='the smallest radius', style='Dim.TLabel').grid(row=2, column=2, sticky='w', padx=6)
        g = self.grid_box(p)
        Slider(self, g, 0, 'Gravity (g)', ('oblate', 'geeASL'), 0, 0.1, 0.0001, tip='surface gravity in g, written as geeASL in the config')
        self.section(p, 'File names')
        self.note(p, 'Starting names for Export. You choose the folder and the format each time you export.')
        g = ttk.Frame(p)
        g.pack(fill='x', pady=4)
        self.v_files = {}
        for i, (k, lab) in enumerate((('height', 'Height map'), ('color', 'Colour map'), ('normal', 'Normal map'))):
            ttk.Label(g, text=lab).grid(row=i, column=0, sticky='w', padx=8, pady=4)
            v = tk.StringVar()
            e = ttk.Entry(g, textvariable=v, width=40)
            e.grid(row=i, column=1, sticky='w', pady=4)
            e.bind('<Return>', self.commit_files)
            e.bind('<FocusOut>', self.commit_files)
            self.v_files[k] = v
        self.section(p, 'Preview camera')
        g = self.grid_box(p)
        Slider(self, g, 0, 'Tilt', ('preview', 'tilt'), -90, 90, 1)
        Slider(self, g, 1, 'View latitude', ('preview', 'view_lat'), -90, 90, 1)
        Slider(self, g, 2, 'View longitude', ('preview', 'view_lon'), 0, 360, 5)

    def snapshot(self):
        self.history.append(copy.deepcopy(self.P))
        del self.history[:-40]
        self.undo_btn.configure(state='normal')

    def undo(self, e=None):
        if e is not None and isinstance(self.focus_get(), (ttk.Entry, ttk.Spinbox, tk.Entry)):
            return
        if not self.history:
            return
        self.P = self.history.pop()
        if not self.history:
            self.undo_btn.configure(state='disabled')
        self.refresh_all()
        self.changed(snap=False)
        self.status('Undone')

    def palette(self, name=None):
        name = name or random.choice(list(PALETTES))
        R = random.uniform
        hi = float(self.P['relief']['high']); lo = float(self.P['relief']['low'])
        shift = [R(-8, 8) for _ in range(3)]
        st = []
        for lev, c in zip(PAL_LEVELS, PALETTES[name]):
            h = lev * (-lo if lev < 0 else hi)
            st.append([round(h / 10) * 10, [int(max(0, min(255, round(v + shift[k] + R(-5, 5))))) for k, v in enumerate(c)]])
        C = self.P['colors']
        C['stops'] = st
        C['rock'] = [int(max(0, min(255, v * 1.08 + 6))) for v in PALETTES[name][4]]
        C['patch_color'] = [int(max(0, min(255, v + R(-20, 20)))) for v in PALETTES[name][3]]
        C['ice'] = [int(R(226, 242)), int(R(230, 244)), int(R(236, 250))]
        C['cap_north'] = 90
        C['cap_south'] = 90
        C['snow_line'] = 99000
        return name

    def randomize(self, what):
        self.commit_entries()
        self.snapshot()
        P = self.P
        R = random.uniform
        Rk = float(P['radius']) / 1000
        if what == 'all':
            P['relief']['high'] = round(Rk * R(40, 110) / 10) * 10
            P['relief']['low'] = -round(Rk * R(30, 90) / 10) * 10
        if what in ('shape', 'all'):
            P['seed'] = random.randint(1, 99999)
            o = P['oblate']
            o['enabled'] = True
            o['mode'] = random.choice(['CustomEllipsoid', 'CustomEllipsoid', 'CustomEllipsoid', 'ContactBinary', 'PointEquipotential'])
            o['a'] = round(R(1.15, 2.0), 2)
            o['b'] = round(R(1.0, min(o['a'], 1.5)), 2)
            o['c'] = 1.0
            o['primaryRadius'] = round(R(1.2, 1.8), 2)
            o['secondaryRadius'] = round(R(1.0, o['primaryRadius']), 2)
            if o['mode'] == 'PointEquipotential':
                if o['geeASL'] <= 0:
                    o['geeASL'] = 0.001
                wc = math.sqrt(o['geeASL'] * tr.G0 * float(P['radius']) / 1.5) / (1.5 * float(P['radius']))
                o['period'] = round(2 * math.pi / wc / R(0.85, 0.99))
            sh = P['shape']
            sh['land'] = round(R(0.3, 0.7), 2)
            sh['continents'] = random.choice([0, 0, 1, 2, 3])
            sh['warp'] = round(R(0.2, 0.9), 2)
            sh['coast'] = round(R(0.25, 0.85), 2)
        if what in ('relief', 'all'):
            Rl = P['relief']
            Rl['mountains'] = round(R(0.0, 0.6), 2)
            Rl['mountain_size'] = round(R(0.7, 1.6), 2)
            Rl['mountain_area'] = round(R(0.2, 0.8), 2)
            Rl['hills'] = round(R(0.2, 0.7), 2)
            Rl['hill_size'] = round(R(0.6, 1.6), 2)
            Rl['plains'] = round(R(0.0, 0.5), 2)
            Rl['roughness'] = round(R(0.25, 0.7), 2)
            Rl['sharpness'] = round(R(0.7, 1.6), 2)
        if what in ('landforms', 'all'):
            Rl = P['relief']
            Rl['canyons'] = random.choice([0, 0, 0, round(R(0.2, 0.6), 2)])
            Rl['canyon_depth'] = round(Rk * R(15, 40) / 10) * 10
            Rl['canyon_width'] = round(max(0.1, Rk * R(0.04, 0.12)), 2)
            PL = P['plateaus']
            PL['amount'] = random.choice([0, 0, 0, round(R(0.2, 0.5), 2)])
            PL['height'] = round(Rk * R(15, 40) / 10) * 10
            PL['size'] = round(R(0.7, 1.6), 2)
            PL['edge'] = round(R(0.2, 0.7), 2)
            CK = P['cracks']
            CK['seed'] = random.randint(1, 99999)
            CK['amount'] = random.choice([0, 0, round(R(0.3, 0.8), 2)])
            CK['style'] = random.choice(['lines', 'lines', 'lines', 'cells'])
            CK['count'] = random.randint(3, 10)
            CK['curvy'] = round(R(0.0, 0.4), 2)
            CK['width'] = round(max(0.02, Rk * R(0.02, 0.05)), 2)
            CK['depth'] = round(Rk * R(8, 20) / 5) * 5
            CK['ridges'] = round(R(0.0, 0.8), 2)
            CK['cell_size'] = round(max(0.5, Rk * R(0.3, 1.0)) * 2) / 2
            V = P['volcanoes']
            V['seed'] = random.randint(1, 99999)
            V['count'] = random.choice([0, 0, 0, 1, 2])
            V['size_km'] = round(max(0.2, Rk * R(0.2, 0.5)), 1)
            V['height'] = round(V['size_km'] * R(40, 80) / 10) * 10
            V['caldera'] = round(R(0.2, 0.8), 2)
        if what in ('craters', 'all'):
            C = P['craters']
            C['seed'] = random.randint(1, 99999)
            C['count'] = int(R(200, 3000))
            C['min_km'] = round(max(0.02, Rk * R(0.01, 0.03)), 2)
            C['max_km'] = round(max(C['min_km'] * 3, Rk * R(0.25, 0.7)), 2)
            C['size_mix'] = round(R(1.5, 2.2), 2)
            C['depth'] = round(R(0.6, 1.2), 2)
            C['fresh'] = round(R(0.1, 0.6), 2)
            C['ejecta'] = round(R(0.1, 0.7), 2)
            C['rays'] = round(R(0.0, 0.5), 2)
        if what in ('colours', 'all'):
            self.palette()
            C = P['colors']
            C['patches'] = round(R(0.15, 0.7), 2)
            C['patch_size'] = round(R(0.6, 1.6), 2)
            C['jitter'] = round(Rk * R(4, 15) / 10) * 10
            C['crater_floor_amount'] = random.choice([0, 0, round(R(0.2, 0.6), 2)])
            fl = [s_[1] for s_ in C['stops']]
            C['crater_floor'] = [int(max(0, min(255, v * R(0.6, 0.85)))) for v in fl[min(1, len(fl) - 1)]]
        self.refresh_all()
        self.changed(snap=False)
        msg = 'Randomized %s – Undo goes back' % ('everything' if what == 'all' else what)
        self.after(300, lambda: self.status(msg))

    def volcano_seed(self):
        self.snapshot()
        self.P['volcanoes']['seed'] = random.randint(1, 99999)
        self.changed()

    def sample(self):
        path = filedialog.askopenfilename(parent=self, title='Picture to take the colours from',
                                          filetypes=[('Pictures', '*.png *.jpg *.jpeg *.bmp *.tga *.webp *.dds'), ('All files', '*.*')])
        if path:
            try:
                SampleWin(self, path)
            except Exception as ex:
                messagebox.showerror('Could not open picture', str(ex), parent=self)

    def place_toggled(self):
        if self.place_mode.get():
            if self.view.get() != 'live':
                self.view.set('live')
                self.update_view()
            self.status('Place features: click the map or the body to add a %s, drag to move, right-click to remove'
                        % self.feat_type.get().lower())
        else:
            self.status('Live preview – press Build for the full-size maps')
        self.redraw()

    def placing(self):
        return self.place_mode.get() and self.view.get() == 'live' and self.live_view is not None

    def globe_xy(self, lat, lon):
        lv, hit = self.live_view, self.hit
        if lv is None or hit is None:
            return 0.0, 0.0, -1.0
        x, y, vis = tr.project_point(lv['F'], hit, lat, lon)
        f = 512.0 / hit['S']
        return x * f, y * f, 1.0 if vis else -1.0

    def feature_near(self, lat, lon):
        best, bd = None, None
        R = float(self.P['radius']) / 1000.0
        for i, f in enumerate(self.P['features']):
            a = np.radians([lat, f['lat']]); b = np.radians([lon, f['lon']])
            d = np.degrees(np.arccos(np.clip(np.sin(a[0]) * np.sin(a[1]) + np.cos(a[0]) * np.cos(a[1]) * np.cos(b[0] - b[1]), -1, 1)))
            lim = max(3.0, min(40.0, np.degrees(float(f['size']) * 0.5 / R) * 0.7))
            if d <= lim and (bd is None or d < bd):
                best, bd = i, d
        return best

    def feature_remove_click(self, e):
        if not self.placing():
            return
        mp = self.map_point(self.sheet_xy(e))
        if mp is None:
            return
        i = self.feature_near(*mp)
        if i is None:
            return
        self.snapshot()
        kind = self.P['features'][i]['type']
        self.P['features'].pop(i)
        self.feat_ed.rebuild()
        self.changed()
        self.redraw()
        self.status('Removed a %s – Undo brings it back' % kind)

    def feature_marks(self):
        if self.view_geom is None:
            return
        s, ox, oy = self.view_geom
        cv = self.canvas
        R = float(self.P['radius']) / 1000.0
        act = self.fdrag[0] if self.fdrag is not None else -1
        for i, f in enumerate(self.P['features']):
            col = WARM if i == act else '#ffffff'
            lat, lon = float(f['lat']), float(f['lon'])
            ang = min(80.0, np.degrees(float(f['size']) * 0.5 / R))
            ry = max(5.0, ang / 180.0 * 512) * s
            rx = min(ry / max(np.cos(np.radians(lat)), 0.08), 512 * s)
            cx, cy = ox + (536 + lon / 360.0 * 1024) * s, oy + (90 - lat) / 180.0 * 512 * s
            for dx in (-1024 * s, 0, 1024 * s):
                x = cx + dx
                if ox + 536 * s - rx <= x <= ox + 1560 * s + rx:
                    cv.create_oval(x - rx, cy - ry, x + rx, cy + ry, outline=col, width=2, dash=(4, 3))
                    cv.create_text(x, cy, text=f['type'][0].upper(), fill=col, font=(FONT, 9, 'bold'))
            gx, gy, z = self.globe_xy(lat, lon)
            if z > 0 and self.hit is not None:
                gr = max(5.0, float(f['size']) * 0.5 / (R * self.hit['rv']) * 256) * s
                cv.create_oval(ox + gx * s - gr, oy + gy * s - gr, ox + gx * s + gr, oy + gy * s + gr, outline=col, width=2, dash=(4, 3))
        cv.create_rectangle(ox + 536 * s, oy, ox + 1560 * s, oy + 512 * s, outline=ACC, width=1)

    def crater_seed(self):
        self.snapshot()
        self.P['craters']['seed'] = random.randint(1, 99999)
        self.changed(snap=False)

    def sort_stops(self):
        self.P['colors']['stops'].sort(key=lambda s: s[0])
        for e in self.editors:
            e.rebuild()
        self.changed()

    def refresh_all(self):
        for s in self.sliders:
            s.refresh()
        for e in self.editors:
            e.rebuild()
        for s in self.swatches:
            s.refresh()
        for v, path in self.checks:
            v.set(bool(getp(self.P, path)))
        for v, path, names in self.combos:
            v.set(names.get(getp(self.P, path), ''))
        self.v_name.set(self.P['name'])
        self.v_seed.set(str(self.P['seed']))
        self.v_radius.set('%.0f' % float(self.P['radius']))
        for k, v in self.v_files.items():
            v.set(self.P['files'].get(k, '') or '')
        self.pick.configure(values=self.preset_names())
        self.pick.set(self.P['name'])
        self.update_title()
        self.shape_info()
        self.update_view()
        self.update_res_info()

    def update_res_info(self):
        r = self.res.get()
        txt = '%s × %d  ·  %s' % (r, int(r) // 2, RES_INFO.get(r, ''))
        n = int(self.P['craters']['count'])
        if n > 3000:
            txt += '  ·  many craters: a bit longer'
        if r == '8192':
            txt += '  ·  big in game'
        self.res_info.configure(text=txt)

    def update_title(self):
        self.title('%s %s – %s%s' % (tr.APP_NAME, tr.APP_VERSION, self.P['name'], ' *' if self.dirty else ''))

    def changed(self, snap=None):
        self.dirty = True
        self.update_title()
        self.update_res_info()
        self.shape_info()
        if self.view.get() == 'live':
            if self.pending:
                self.after_cancel(self.pending)
            self.pending = self.after(120, self.update_view)
        else:
            self.update_stale()

    def commit_name(self, _e=None):
        new = self.v_name.get().strip()
        old = self.P['name']
        if not new or new == old:
            self.v_name.set(old)
            return
        for k, v in list(self.P['files'].items()):
            if v and old in v:
                self.P['files'][k] = v.replace(old, new)
        self.P['name'] = new
        for k, v in self.v_files.items():
            if old in v.get():
                v.set(v.get().replace(old, new))
        self.changed()

    def commit_seed(self, _e=None):
        try:
            s = int(self.v_seed.get())
        except ValueError:
            self.v_seed.set(str(self.P['seed']))
            return
        if s != self.P['seed']:
            self.snapshot()
            self.P['seed'] = s
            self.changed()

    def commit_radius(self, _e=None):
        try:
            r = float(self.v_radius.get().replace(',', '.'))
            if r < 100:
                raise ValueError
        except ValueError:
            self.v_radius.set('%.0f' % float(self.P['radius']))
            return
        if r != float(self.P['radius']):
            self.snapshot()
            self.P['radius'] = r
            self.changed()

    def random_seed(self):
        self.snapshot()
        self.P['seed'] = random.randint(1, 99999)
        self.v_seed.set(str(self.P['seed']))
        self.changed()

    def commit_files(self, _e=None):
        new = {k: v.get().strip() for k, v in self.v_files.items()}
        new = {k: v for k, v in new.items() if v}
        if new != {k: v for k, v in self.P['files'].items() if v}:
            self.P['files'] = new
            self.changed()

    def commit_entries(self):
        self.commit_name()
        self.commit_seed()
        self.commit_radius()
        self.commit_files()
        self.focus_set()

    def ask_save(self):
        if not self.dirty:
            return True
        r = messagebox.askyesnocancel('Unsaved changes', 'Save the changes to %s first?' % self.P['name'], parent=self)
        if r is None:
            return False
        if r:
            return self.save()
        return True

    def on_pick(self, _e=None):
        name = self.pick.get()
        if name == self.P['name'] and self.preset_file:
            return
        if not self.ask_save():
            self.pick.set(self.P['name'])
            return
        self.load(name)

    def load(self, name):
        path = os.path.join(tr.PRESETS, name + '.json')
        try:
            with open(path) as f:
                raw = json.load(f)
        except Exception as ex:
            messagebox.showerror('Could not load', str(ex), parent=self)
            return
        raw.setdefault('name', name)
        self.P = tr.normalize(raw)
        self.preset_file = path
        self.dirty = False
        self.history = []
        self.stop_live()
        self.live_last = None
        self.rot = [0.0, 0.0]
        self.body = None
        self.undo_btn.configure(state='disabled')
        self.refresh_all()

    def save(self, quiet=False):
        self.commit_entries()
        name = self.P['name'].strip()
        if not name or any(ch in name for ch in '\\/:*?"<>|'):
            messagebox.showerror('Name', 'Please give the body a valid name.', parent=self)
            return False
        path = os.path.join(tr.PRESETS, name + '.json')
        if os.path.exists(path) and os.path.abspath(path) != os.path.abspath(self.preset_file or ''):
            if not messagebox.askyesno('Overwrite', '%s already exists. Overwrite it?' % name, parent=self):
                return False
        self.P = tr.normalize(self.P)
        with open(path, 'w') as f:
            json.dump(self.P, f, indent=1)
        self.preset_file = path
        self.dirty = False
        for e in self.editors:
            e.rebuild()
        self.pick.configure(values=self.preset_names())
        self.pick.set(name)
        self.update_title()
        if not quiet:
            self.status('Saved %s' % os.path.relpath(path, tr.TOOL))
        return True

    def new(self):
        if not self.ask_save():
            return
        name = simpledialog.askstring('New body', 'Name (for example Pilgrim28d).\nIt starts as a copy of %s with a new seed.' % self.P['name'], parent=self)
        if not name:
            return
        name = name.strip()
        if os.path.exists(os.path.join(tr.PRESETS, name + '.json')):
            messagebox.showerror('New', '%s already exists.' % name, parent=self)
            return
        P = copy.deepcopy(self.P)
        P['name'] = name
        P['seed'] = random.randint(1, 99999)
        P['craters']['seed'] = random.randint(1, 99999)
        P['files'] = {'height': name + '_height.dds', 'color': name + '_color.dds', 'normal': name + '_normal.dds'}
        self.P = tr.normalize(P)
        self.preset_file = None
        self.dirty = True
        self.history = []
        self.undo_btn.configure(state='disabled')
        self.refresh_all()
        self.save()

    def save_as(self):
        name = simpledialog.askstring('Save as', 'New name:', parent=self, initialvalue=self.P['name'])
        if not name or name.strip() == self.P['name']:
            return
        self.v_name.set(name.strip())
        self.commit_name()
        self.preset_file = None
        self.save()

    def out_path(self, res=None):
        res = int(res or self.res.get())
        n = self.P['name']
        return os.path.join(tr.OUTROOT, n if res == 4096 else '%s_%d' % (n, res))

    def open_out(self):
        d = self.out_path()
        if not os.path.isdir(d):
            d = tr.OUTROOT
        os.makedirs(d, exist_ok=True)
        open_folder(d)

    def is_stale(self, res=None):
        f = os.path.join(self.out_path(res), self.P['name'] + '_preset.json')
        if not os.path.isfile(f):
            return None
        try:
            with open(f) as fh:
                built = tr.normalize(json.load(fh))
        except Exception:
            return None
        b = tr.normalize(copy.deepcopy(self.P))
        return json.dumps(built, sort_keys=True) != json.dumps(b, sort_keys=True)

    def update_stale(self):
        if self.proc:
            return
        if self.view.get() in ('preview', 'flat') and self.is_stale():
            self.status('Settings changed since this build – press Build to update')

    def live_key(self):
        return json.dumps(self.P, sort_keys=True, default=str)

    def update_view(self, from_live=False):
        self.pending = None
        v = self.view.get()
        if v == 'live':
            key = self.live_key()
            L = self.live_last
            if L is not None:
                col, hm, gx, gy = L['col'], L['hm'], L['gx'], L['gy']
                k = float(self.P['normal_strength'])
                mode = self.show.get()
                if mode == 'Height':
                    g = np.asarray(tr.height_grey(hm)).astype(np.float32)
                    sh = np.clip(g[..., None] * tr.shade_map(gx, gy, k * 0.6)[..., None], 0, 255)
                    tex = np.repeat(sh, 3, -1).astype(np.uint8)
                    flat = Image.fromarray(tex)
                    gtex = np.repeat(g[..., None], 3, -1).astype(np.uint8)
                elif mode == 'Colour, no shading':
                    flat = Image.fromarray(col)
                    gtex = col
                else:
                    flat = Image.fromarray(np.clip(col.astype(np.float32) * tr.shade_map(gx, gy, k)[..., None], 0, 255).astype(np.uint8))
                    gtex = col
                if flat.size != (1024, 512):
                    flat = flat.resize((1024, 512), Image.LANCZOS if flat.size[0] > 1024 else Image.BICUBIC)
                sheet = Image.new('RGB', (1024 + 512 + 24, 512 + 34), (13, 15, 20))
                sheet.paste(flat, (512 + 24, 0))
                d = ImageDraw.Draw(sheet)
                f17 = sheet_font(17)
                hint = 'drag to turn · double-click resets'
                if mode == 'Height':
                    hint = 'height map on the shape · drag to turn'
                d.text((256 - d.textlength(hint, font=f17) / 2, 518), hint, fill=DIM, font=f17)
                rng = 'height map %.0f m to %.0f m' % (float(hm.min()), float(hm.max()))
                d.text((536, 518), rng, fill=DIM, font=f17)
                P = tr.normalize(json.loads(L['key']))
                bk = (L['key'], L['W'], k)
                if self.body is None or self.body[0] != bk:
                    self.body = (bk, tr.body_fields(P, hm, k), P)
                self.live_view = {'tex': gtex, 'k': k, 'sheet': sheet, 'hm': hm, 'F': self.body[1], 'P': self.body[2]}
                sheet = sheet.copy()
                sheet.paste(self.globe(512), (0, 0))
                self.view_src = sheet
            else:
                self.view_src = None
                self.live_view = None
            if not self.proc and not self.place_mode.get():
                self.status('Live preview – press Build for the full-size maps')
            if not from_live:
                self.request_live(key)
            self.update_live_label(key)
        else:
            self.live_lab.configure(text='')
            f = os.path.join(self.out_path(), self.P['name'] + ('_preview.png' if v == 'preview' else '_color.png'))
            if os.path.isfile(f):
                try:
                    self.view_src = Image.open(f).convert('RGB')
                    self.view_src.load()
                except Exception:
                    self.view_src = None
                if not self.proc:
                    self.status('Settings changed since this build – press Build to update' if self.is_stale()
                                else 'Showing build at %s' % self.res.get())
            else:
                self.view_src = None
                if not self.proc:
                    self.status('Nothing built at %s yet – press Build' % self.res.get())
        self.update_export_state()
        self.redraw()

    def globe(self, S):
        lv = self.live_view
        pv = self.P['preview']
        vlat = max(-90.0, min(90.0, float(pv['view_lat']) + self.rot[1]))
        im, hit = tr.render_body(lv['tex'], lv['F'], S, float(pv['tilt']), vlat, float(pv['view_lon']) + self.rot[0],
                                 shadows=bool(self.shadows.get()) and S >= 400, steps=40 if S >= 400 else 28)
        self.hit = hit
        return im

    def shadows_changed(self):
        S = load_settings()
        S['shadows'] = bool(self.shadows.get())
        save_settings(S)
        self.respin(False)

    def sheet_xy(self, e):
        if self.view_geom is None:
            return None
        s, ox, oy = self.view_geom
        return (e.x - ox) / s, (e.y - oy) / s

    def map_point(self, p):
        if p is None:
            return None
        x, y = p
        if 536 <= x < 1560 and 0 <= y < 512:
            return float(90.0 - (y + 0.5) / 512.0 * 180.0), float(((x - 536 + 0.5) / 1024.0 * 360.0) % 360.0)
        hit = self.hit
        if hit is None or not (0 <= x < 512 and 0 <= y < 512):
            return None
        S = hit['S']
        i, j = int(y / 512.0 * S), int(x / 512.0 * S)
        lat = float(hit['lat'][i, j])
        if lat != lat:
            return None
        return lat, float(hit['lon'][i, j])

    def hover(self, e):
        if self.view.get() != 'live' or self.live_view is None:
            return
        mp = self.map_point(self.sheet_xy(e))
        if mp is None:
            self.hover_lab.configure(text='')
            return
        hm = self.live_view['hm']
        H, W = hm.shape
        r = min(H - 1, max(0, int((90 - mp[0]) / 180 * H)))
        c = int(mp[1] / 360 * W) % W
        h = float(hm[r, c])
        F = self.live_view['F']
        Hf, Wf = F['r'].shape
        rr = float(F['r'][min(Hf - 1, max(0, int((90 - mp[0]) / 180 * Hf))), int(mp[1] / 360 * Wf) % Wf]) * float(self.P['radius'])
        txt = 'latitude %6.1f°   map longitude %6.1f°   height %7.0f m   altitude %7.0f m   %6.2f km from the centre' % (
            mp[0], mp[1], h, rr - float(self.P['radius']), rr / 1000.0)
        self.hover_lab.configure(text=txt)

    def drag_start(self, e):
        self.drag = None
        self.fdrag = None
        if self.view.get() != 'live' or self.live_view is None:
            return
        p = self.sheet_xy(e)
        if self.place_mode.get():
            mp = self.map_point(p)
            if mp is None:
                return
            self.snapshot()
            i = self.feature_near(*mp)
            if i is None:
                t = self.feat_type.get().lower()
                f = tr.default_feature(t if t in tr.FEATURE_TYPES else 'crater', float(self.P['radius']))
                f['lat'], f['lon'] = round(mp[0], 1), round(mp[1], 1)
                self.P['features'].append(f)
                i = len(self.P['features']) - 1
                self.fdrag = [i, True]
                self.status('Added a %s at %.1f°, %.1f° – drag to move it, settings on the Features tab' % (t, f['lat'], f['lon']))
            else:
                self.fdrag = [i, False]
            self.redraw()
            return
        if p and (p[0] - 256) ** 2 + (p[1] - 256) ** 2 <= 256 ** 2:
            self.drag = (p[0], p[1], self.rot[0], self.rot[1])

    def drag_move(self, e):
        if self.fdrag is not None:
            mp = self.map_point(self.sheet_xy(e))
            if mp is not None:
                f = self.P['features'][self.fdrag[0]]
                f['lat'], f['lon'] = round(mp[0], 1), round(mp[1], 1)
                self.fdrag[1] = True
                self.redraw(fast=True)
            return
        if self.drag is None:
            return
        p = self.sheet_xy(e)
        if not p:
            return
        x0, y0, r0, r1 = self.drag
        self.rot[0] = (r0 - (p[0] - x0) * 0.35) % 360
        self.rot[1] = max(-180.0, min(180.0, r1 + (p[1] - y0) * 0.35))
        if not getattr(self, 'spin_pending', False):
            self.spin_pending = True
            self.after_idle(lambda: self.respin(True))

    def drag_end(self, _e=None):
        if self.fdrag is not None:
            i, moved = self.fdrag
            self.fdrag = None
            if moved:
                self.feat_ed.rebuild()
                self.changed()
            elif self.history:
                self.history.pop()
                if not self.history:
                    self.undo_btn.configure(state='disabled')
            self.redraw()
            return
        if self.drag is not None:
            self.drag = None
            self.respin(False)

    def drag_reset(self, e):
        if self.place_mode.get():
            return
        p = self.sheet_xy(e)
        if self.view.get() == 'live' and self.live_view is not None and p and (p[0] - 256) ** 2 + (p[1] - 256) ** 2 <= 256 ** 2:
            self.rot = [0.0, 0.0]
            self.respin(False)

    def respin(self, quick):
        self.spin_pending = False
        lv = self.live_view
        if lv is None or self.view.get() != 'live':
            return
        sph = self.globe(256 if quick else 512)
        if quick:
            sph = sph.resize((512, 512), Image.BILINEAR)
        sheet = lv['sheet'].copy()
        sheet.paste(sph, (0, 0))
        self.view_src = sheet
        self.redraw(fast=quick)

    def update_live_label(self, key=None):
        v = self.view.get()
        if v != 'live':
            txt = ''
        elif self.proc:
            txt = 'preview waits while building'
        elif self.live_err:
            txt = 'preview failed: %s' % self.live_err[:60]
        else:
            key = key or self.live_key()
            L = self.live_last
            if L is not None and L['key'] == key:
                txt = ('%d px · %.1f s' % (L['W'], L['dt'])) if L['dt'] >= 0.05 else '%d px' % L['W']
                if L['W'] < self.live_target():
                    txt += ' – sharpening…'
            else:
                txt = 'updating…'
        self.live_lab.configure(text=txt)

    def live_target(self):
        try:
            return int(self.live_size.get())
        except ValueError:
            return 512

    def live_size_changed(self, _e=None):
        S = load_settings()
        S['live_size'] = self.live_target()
        save_settings(S)
        self.update_view()

    def request_live(self, key):
        if self.view.get() != 'live':
            return
        if self.live_after:
            self.after_cancel(self.live_after)
        self.live_after = self.after(200, lambda: self.start_live(key))

    def start_live(self, key):
        self.live_after = None
        if self.proc:
            self.update_live_label(key)
            return
        sizes = (256, self.live_target())
        L = self.live_last
        if L is not None and L['key'] == key and L['W'] >= sizes[-1]:
            return
        P = tr.normalize(copy.deepcopy(self.P))
        if L is not None and L['hk'] == tr.height_key(P) and L['W'] >= sizes[0]:
            sizes = sizes[1:]
        r = self.live_req
        if r is not None and r[1] == key and r[3] == sizes:
            return
        self.live_err = None
        with self.live_lock:
            self.live_gen += 1
            self.live_req = (self.live_gen, key, P, sizes)
            if self.live_thread is None:
                self.live_thread = threading.Thread(target=self.live_worker, daemon=True)
                self.live_thread.start()
        self.update_live_label(key)

    def stop_live(self):
        with self.live_lock:
            self.live_gen += 1
            self.live_req = None

    def live_worker(self):
        while True:
            with self.live_lock:
                req = self.live_req
                if req is None:
                    self.live_thread = None
                    return
            gen, key, P, sizes = req

            def cancel(gen=gen):
                r = self.live_req
                if r is None or r[0] != gen:
                    raise tr.Cancelled()
            try:
                hk = tr.height_key(P)
                for W in sizes:
                    if W != sizes[-1] and ('H', hk, sizes[-1]) in self.live_cache:
                        continue
                    t0 = time.time()
                    col, hm, gx, gy = tr.live_maps(P, W, self.live_cache, cancel, workers=tr.THREADS)
                    self.live_q.put((gen, key, hk, W, (col, hm, gx, gy), None, time.time() - t0))
            except tr.Cancelled:
                continue
            except Exception as ex:
                self.live_q.put((gen, key, '', 0, None, str(ex), 0))
            with self.live_lock:
                if self.live_req is not None and self.live_req[0] == gen:
                    self.live_req = None

    def live_poll(self):
        got = False
        try:
            while True:
                gen, key, hk, W, maps, err, dt = self.live_q.get_nowait()
                if maps is None:
                    if gen == self.live_gen:
                        self.live_err = err
                        got = True
                elif gen == self.live_gen:
                    col, hm, gx, gy = maps
                    self.live_last = {'key': key, 'hk': hk, 'W': W, 'col': col, 'hm': hm, 'gx': gx, 'gy': gy, 'dt': dt}
                    got = True
        except queue.Empty:
            pass
        except tk.TclError:
            return
        if got:
            if self.view.get() == 'live':
                self.update_view(from_live=True)
            else:
                self.update_live_label()
        try:
            self.after(100, self.live_poll)
        except tk.TclError:
            pass

    def schedule_redraw(self):
        if self.redraw_id:
            self.after_cancel(self.redraw_id)
        self.redraw_id = self.after(60, self.redraw)

    def redraw(self, fast=False):
        self.redraw_id = None
        self.canvas.delete('all')
        cw, ch = max(10, self.canvas.winfo_width()), max(10, self.canvas.winfo_height())
        if self.view_src is None:
            self.view_geom = None
            msg = 'Making the preview…' if self.view.get() == 'live' else 'No picture yet'
            self.canvas.create_text(cw // 2, ch // 2, text=msg, fill=DIM, font=(FONT, 12))
            return
        iw, ih = self.view_src.size
        s = min((cw - 16) / iw, (ch - 16) / ih)
        w2, h2 = max(1, int(iw * s)), max(1, int(ih * s))
        im = self.view_src.resize((w2, h2), Image.BILINEAR if fast else Image.LANCZOS)
        self.tkimg = ImageTk.PhotoImage(im)
        self.canvas.create_image(cw // 2, ch // 2, image=self.tkimg)
        self.view_geom = (w2 / float(iw), cw // 2 - w2 / 2.0, ch // 2 - h2 / 2.0)
        if self.placing():
            self.feature_marks()

    def status(self, t):
        self.stat.configure(text=t)

    def log(self, line):
        self.logbox.configure(state='normal')
        self.logbox.insert('end', line + '\n')
        self.logbox.see('end')
        self.logbox.configure(state='disabled')

    def builds(self):
        return [r for r in RES[::-1] if os.path.isfile(os.path.join(self.out_path(r), self.P['name'] + '_height.png'))]

    def update_export_state(self):
        self.export_btn.configure(state='normal' if self.builds() and not self.proc else 'disabled')

    def set_busy(self, busy):
        self.build_btn.configure(state='disabled' if busy else 'normal')
        self.cancel_btn.configure(state='normal' if busy else 'disabled')
        self.update_export_state()

    def run(self, args, done):
        if self.proc:
            return
        cmd = ([sys.executable] if tr.FROZEN else [sys.executable, '-u', GEN]) + args
        self.log('> ' + ' '.join(args[:1] + [os.path.basename(a) for a in args[1:]]))
        try:
            env = dict(os.environ, PYTHONUNBUFFERED='1')
            self.proc = subprocess.Popen(cmd, cwd=tr.TOOL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                         stdin=subprocess.DEVNULL, text=True, bufsize=1, creationflags=NOWIN, env=env)
        except Exception as ex:
            messagebox.showerror('Could not start', str(ex), parent=self)
            return
        self.done_cb = done
        self.stop_live()
        self.update_live_label()
        threading.Thread(target=self.reader, args=(self.proc,), daemon=True).start()
        self.set_busy(True)
        self.after(100, self.poll)

    def reader(self, p):
        for line in p.stdout:
            self.q.put(line.rstrip('\n'))
        p.wait()
        self.q.put(None)

    def poll(self):
        finished = False
        try:
            while True:
                line = self.q.get_nowait()
                if line is None:
                    finished = True
                    break
                self.log(line)
                self.progress(line)
        except queue.Empty:
            pass
        if finished:
            rc = self.proc.returncode
            self.proc = None
            self.set_busy(False)
            self.done_cb(rc)
            if self.view.get() == 'live':
                self.update_view()
        else:
            self.after(100, self.poll)

    def progress(self, line):
        w = line.split()
        try:
            if w and w[0] == 'height' and w[-1].endswith('%'):
                pct = int(w[-1].rstrip('%'))
                self.prog['value'] = 0.6 * pct
                self.status('Shaping the ground – %d%%' % pct)
            elif w and w[0] == 'color' and w[-1].endswith('%'):
                pct = int(w[-1].rstrip('%'))
                self.prog['value'] = 60 + 0.25 * pct
                self.status('Colouring – %d%%' % pct)
            elif 'color' in w and 'done' in w:
                self.prog['value'] = 86
                self.status('Saving the maps')
            elif 'files' in w and 'done' in w:
                self.prog['value'] = 92
                self.status('Making the preview sheet')
            elif 'DONE' in w:
                self.prog['value'] = 100
        except (ValueError, IndexError):
            pass

    def build(self):
        if not self.save(quiet=True):
            return
        self.prog['value'] = 0
        self.status('Starting…')
        self.run(['make', self.preset_file, '--res', self.res.get()], self.built)

    cancelled = False

    def built(self, rc):
        if self.cancelled:
            self.cancelled = False
            self.status('Cancelled')
        elif rc == 0:
            self.prog['value'] = 100
            self.view.set('preview')
            self.update_view()
            self.status('Done – %s at %s' % (self.P['name'], self.res.get()))
        else:
            self.status('Build failed – see the log below')

    def cancel(self):
        if self.proc:
            self.cancelled = True
            self.proc.terminate()

    def export(self):
        self.commit_entries()
        b = self.builds()
        if not b:
            messagebox.showinfo('Build first', 'Press Build first – Export saves the files of a build.', parent=self)
            return
        ExportDialog(self, b)

    def close(self):
        if self.proc:
            if not messagebox.askyesno('Building', 'A build is running. Stop it and quit?', parent=self):
                return
            self.proc.terminate()
        if not self.ask_save():
            return
        self.destroy()


def main():
    if len(sys.argv) > 1 and sys.argv[1] in tr.COMMANDS:
        tr.main()
        return
    if os.name == 'nt':
        try:
            import ctypes
            if tr.FROZEN:
                hwnd = ctypes.windll.kernel32.GetConsoleWindow()
                if hwnd:
                    ctypes.windll.user32.ShowWindow(hwnd, 0)
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
    App().mainloop()


if __name__ == '__main__':
    main()
