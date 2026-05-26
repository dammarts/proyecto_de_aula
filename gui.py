import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import numpy as np

try:
    import matplotlib
    matplotlib.use('TkAgg')
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MPL = True
except ImportError:
    MPL = False

from simplex import SimplexSolver
from problema import PROBLEMA, CONFIG
import utils


# ══════════════════════════════════════════════════════════════════════════════
class AppGUI:
# ══════════════════════════════════════════════════════════════════════════════

    # ── Color palette ─────────────────────────────────────────────────────────
    C_DARK      = '#1a237e'
    C_DARK2     = '#283593'
    C_ACCENT    = '#1565c0'
    C_BG        = '#f0f2f5'
    C_CARD      = '#ffffff'
    C_GREEN     = '#1b5e20'
    C_RED       = '#b71c1c'
    C_LIGHT     = '#e8eaf6'
    C_TXT       = '#212121'
    C_MUTED     = '#757575'
    C_TERMINAL  = '#1e1e1e'
    C_TERM_FG   = '#d4d4d4'
    C_CODE_BG   = '#263238'
    C_CODE_FG   = '#a5d6a7'

    F_TITLE   = ('Segoe UI', 14, 'bold')
    F_HEAD    = ('Segoe UI', 11, 'bold')
    F_BODY    = ('Segoe UI', 10)
    F_SMALL   = ('Segoe UI', 9)
    F_BOLD    = ('Segoe UI', 10, 'bold')
    F_MONO    = ('Courier New', 9)
    F_MONO10  = ('Courier New', 10)

    # ── Init ───────────────────────────────────────────────────────────────────
    def __init__(self, root):
        self.root = root
        self.root.title('Solucionador PL — Metodo Simplex')
        self.root.geometry('1400x860')
        self.root.minsize(1100, 720)
        self.root.configure(bg=self.C_BG)

        # Solver tab state
        self.n_var  = tk.IntVar(value=3)
        self.n_con  = tk.IntVar(value=4)
        self.tipo_v = tk.StringVar(value='max')
        self.entries_c = []
        self.entries_A = []
        self.entries_b = []
        self.last_solver = None

        # Example tab state
        self.ex_solver   = None
        self.ex_history  = []
        self.ex_varnames = []
        self.ex_iter     = 0

        # LP solver extra state
        self.entries_rnames  = []
        self.entries_ctypes  = []
        self.entries_signs_c = []   # list of (StringVar, Button) for objective signs
        self.entries_signs_A = []   # 2D list of (StringVar, Button) for constraint signs
        self.lp_preview      = None

        self._apply_styles()
        self._build_header()
        self._build_notebook()

    # ── ttk styles ─────────────────────────────────────────────────────────────
    def _apply_styles(self):
        s = ttk.Style()
        s.theme_use('clam')
        s.configure('TNotebook',     background=self.C_BG, borderwidth=0)
        s.configure('TNotebook.Tab', background='#c5cae9', foreground=self.C_TXT,
                    padding=[22, 9], font=('Segoe UI', 10))
        s.map('TNotebook.Tab',
              background=[('selected', self.C_DARK)],
              foreground=[('selected', 'white')])
        s.configure('Treeview',
                    background=self.C_CARD, foreground=self.C_TXT,
                    rowheight=24, font=self.F_BODY, fieldbackground=self.C_CARD)
        s.configure('Treeview.Heading',
                    background=self.C_LIGHT, foreground=self.C_DARK,
                    font=self.F_BOLD, relief='flat')
        s.map('Treeview', background=[('selected', self.C_ACCENT)],
              foreground=[('selected', 'white')])

    # ── Header bar ─────────────────────────────────────────────────────────────
    def _build_header(self):
        h = tk.Frame(self.root, bg=self.C_DARK, height=62)
        h.pack(fill='x')
        h.pack_propagate(False)

        lf = tk.Frame(h, bg=self.C_DARK)
        lf.pack(side='left', padx=20, fill='y')
        tk.Label(lf, text='SOLUCIONADOR DE PROGRAMACION LINEAL',
                 font=('Segoe UI', 15, 'bold'), fg='white', bg=self.C_DARK
                 ).pack(anchor='w', pady=(10, 0))
        tk.Label(lf, text='Metodo Simplex (Big-M)  |  Restricciones Mixtas  <=  >=  =  |  Investigacion de Operaciones',
                 font=self.F_SMALL, fg='#9fa8da', bg=self.C_DARK).pack(anchor='w')

        rf = tk.Frame(h, bg=self.C_DARK)
        rf.pack(side='right', padx=20, fill='y')
        tk.Label(rf, text=f"{CONFIG['nombre_estudiante']}  |  {CONFIG['nombre_companera']}",
                 font=self.F_BOLD, fg='white', bg=self.C_DARK
                 ).pack(anchor='e', pady=(14, 0))
        tk.Label(rf, text=f"{CONFIG['semestre']}  |  {CONFIG['universidad']}",
                 font=('Segoe UI', 8), fg='#9fa8da', bg=self.C_DARK).pack(anchor='e')

    # ── Notebook ───────────────────────────────────────────────────────────────
    def _build_notebook(self):
        nb = ttk.Notebook(self.root)
        nb.pack(fill='both', expand=True, padx=8, pady=(4, 8))

        t1 = tk.Frame(nb, bg=self.C_BG)
        t2 = tk.Frame(nb, bg=self.C_BG)
        t3 = tk.Frame(nb, bg=self.C_BG)

        nb.add(t1, text='   Solucionador LP   ')
        nb.add(t2, text='   Ejemplo Propio   ')
        nb.add(t3, text='   Acerca del Proyecto   ')

        self._tab_solver(t1)
        self._tab_example(t2)
        self._tab_about(t3)

    # ── Helper: card (LabelFrame) ──────────────────────────────────────────────
    def _card(self, parent, title='', **kw):
        return tk.LabelFrame(parent, text=f'  {title}  ' if title else '',
                             bg=self.C_CARD, fg=self.C_DARK,
                             font=self.F_BOLD, relief='groove', bd=1, **kw)

    # ── Helper: styled button ──────────────────────────────────────────────────
    def _btn(self, parent, text, cmd, color=None, fg='white', **kw):
        color = color or self.C_ACCENT
        return tk.Button(parent, text=text, command=cmd, font=self.F_BOLD,
                         bg=color, fg=fg, relief='flat', cursor='hand2',
                         activebackground=self.C_DARK2, activeforeground='white',
                         padx=12, pady=5, **kw)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 — SOLUCIONADOR LP
    # ══════════════════════════════════════════════════════════════════════════

    def _tab_solver(self, parent):
        pw = tk.PanedWindow(parent, orient='horizontal', bg='#9fa8da',
                            sashwidth=7, sashrelief='flat', sashpad=3,
                            showhandle=True, handlesize=12, handlepad=40)
        pw.pack(fill='both', expand=True, padx=8, pady=8)

        left  = tk.Frame(pw, bg=self.C_BG)
        right = tk.Frame(pw, bg=self.C_BG)

        pw.add(left,  minsize=260, width=500)
        pw.add(right, minsize=280)

        self._solver_controls(left)
        self._solver_output(right)

    # ── Controls (left panel) ──────────────────────────────────────────────────
    def _solver_controls(self, parent):
        dim = self._card(parent, 'Dimensiones y Tipo de Problema')
        dim.pack(fill='x', pady=(0, 6))

        grid = tk.Frame(dim, bg=self.C_CARD)
        grid.pack(fill='x', padx=10, pady=8)

        tk.Label(grid, text='Variables (n):', font=self.F_BODY, bg=self.C_CARD,
                 fg=self.C_TXT).grid(row=0, column=0, sticky='w', padx=4)
        ttk.Spinbox(grid, from_=2, to=6, textvariable=self.n_var,
                    width=5, font=self.F_BODY).grid(row=0, column=1, padx=6)

        tk.Label(grid, text='Restricciones (m):', font=self.F_BODY, bg=self.C_CARD,
                 fg=self.C_TXT).grid(row=0, column=2, sticky='w', padx=10)
        ttk.Spinbox(grid, from_=1, to=8, textvariable=self.n_con,
                    width=5, font=self.F_BODY).grid(row=0, column=3, padx=6)

        tipo_row = tk.Frame(dim, bg=self.C_CARD)
        tipo_row.pack(fill='x', padx=10, pady=(0, 4))
        tk.Label(tipo_row, text='Objetivo:', font=self.F_BODY, bg=self.C_CARD).pack(side='left', padx=4)
        ttk.Radiobutton(tipo_row, text='Maximizar', variable=self.tipo_v, value='max').pack(side='left', padx=6)
        ttk.Radiobutton(tipo_row, text='Minimizar', variable=self.tipo_v, value='min').pack(side='left', padx=6)

        self._btn(dim, 'Generar Tabla de Entrada', self._gen_table,
                  color=self.C_ACCENT).pack(padx=10, pady=(4, 10))

        # Scrollable area for the dynamic input grid
        wrap = tk.Frame(parent, bg=self.C_BG)
        wrap.pack(fill='both', expand=True)

        canvas = tk.Canvas(wrap, bg=self.C_BG, highlightthickness=0)
        vsb = ttk.Scrollbar(wrap, orient='vertical',   command=canvas.yview)
        hsb = ttk.Scrollbar(wrap, orient='horizontal', command=canvas.xview)
        canvas.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side='right',  fill='y')
        hsb.pack(side='bottom', fill='x')
        canvas.pack(side='left', fill='both', expand=True)

        self.input_canvas = canvas
        self.input_inner = tk.Frame(canvas, bg=self.C_BG)
        self.input_win = canvas.create_window((0, 0), window=self.input_inner,
                                              anchor='nw')
        self.input_inner.bind('<Configure>',
                              lambda e: canvas.configure(
                                  scrollregion=canvas.bbox('all')))
        self._lp_bind_scroll = self._bind_mousewheel(self.input_canvas)
        self._lp_bind_scroll(self.input_inner)

    # ── Sign-toggle cell helper ────────────────────────────────────────────────
    def _make_sign_cell(self, parent, bg_cell, upd_fn, entry_width=4):
        """Return ((sv, btn), entry, frame) — a sign button + magnitude entry."""
        sv   = tk.StringVar(value='+')
        cell = tk.Frame(parent, bg=bg_cell)

        btn = tk.Button(cell, text='+', font=('Courier New', 9, 'bold'),
                        width=2, relief='groove', cursor='hand2',
                        bg='#c8e6c9', fg='#1b5e20', bd=1, padx=1)
        btn.pack(side='left', padx=(0, 1), pady=1)

        entry = tk.Spinbox(cell, width=entry_width, font=self.F_BODY, justify='center',
                           from_=0, to=9999, increment=1,
                           relief='solid', bd=1, bg=bg_cell,
                           command=upd_fn)
        entry.delete(0, 'end')
        entry.insert(0, '0')
        entry.pack(side='left', pady=1)
        entry.bind('<KeyRelease>', lambda _: upd_fn())

        def _toggle(b=btn, s=sv):
            if s.get() == '+':
                s.set('-'); b.configure(text='-', bg='#ffcdd2', fg='#b71c1c')
            else:
                s.set('+'); b.configure(text='+', bg='#c8e6c9', fg='#1b5e20')
            upd_fn()

        btn.configure(command=_toggle)
        return (sv, btn), entry, cell

    # ── Generate dynamic input table ───────────────────────────────────────────
    def _gen_table(self):
        for w in self.input_inner.winfo_children():
            w.destroy()
        self.entries_c       = []
        self.entries_A       = []
        self.entries_b       = []
        self.entries_rnames  = []
        self.entries_ctypes  = []
        self.entries_signs_c = []
        self.entries_signs_A = []
        self.lp_preview      = None

        n = self.n_var.get()
        m = self.n_con.get()
        tipo = self.tipo_v.get()
        tipo_lbl = 'MAX' if tipo == 'max' else 'MIN'

        card = self._card(self.input_inner,
                          f'Modelo  ({tipo_lbl} Z  |  {n} variables  |  {m} restricciones)')
        card.pack(fill='x', padx=4, pady=4)
        f = tk.Frame(card, bg=self.C_CARD)
        f.pack(fill='x', padx=10, pady=10)

        def upd(*_): self._update_lp_preview(n, m, tipo)

        # ── Objective section header ──
        obj_bar = tk.Frame(f, bg='#e8f5e9')
        obj_bar.grid(row=0, column=0, columnspan=n + 4, sticky='ew', pady=(0, 2))
        tk.Label(obj_bar,
                 text=f'  FUNCION OBJETIVO  ({tipo_lbl} Z)  —  Ingrese la ganancia o costo unitario de cada variable',
                 font=self.F_BOLD, bg='#e8f5e9', fg='#1b5e20').pack(side='left', padx=6, pady=3)

        # Variable column headers
        tk.Label(f, text='', bg=self.C_CARD, width=16).grid(row=1, column=0, padx=2)
        for j in range(n):
            tk.Label(f, text=f'x{j+1}', font=self.F_BOLD, bg=self.C_CARD,
                     fg=self.C_DARK, width=7, anchor='center').grid(row=1, column=j + 1, padx=2)

        # Objective entries with sign toggles (green background)
        tk.Label(f, text=f'{tipo_lbl}  Z =', font=('Segoe UI', 10, 'bold'),
                 bg=self.C_CARD, fg='#1b5e20', anchor='e').grid(
                 row=2, column=0, sticky='e', padx=6, pady=4)
        for j in range(n):
            (sv, btn), e, cell = self._make_sign_cell(f, '#c8e6c9', upd)
            cell.grid(row=2, column=j + 1, padx=3, pady=4)
            self.entries_signs_c.append((sv, btn))
            self.entries_c.append(e)

        # ── Constraints section header ──
        ttk.Separator(f, orient='horizontal').grid(row=3, column=0,
                      columnspan=n + 4, sticky='ew', pady=(6, 0))
        con_bar = tk.Frame(f, bg='#fff3e0')
        con_bar.grid(row=4, column=0, columnspan=n + 4, sticky='ew', pady=(0, 2))
        tk.Label(con_bar,
                 text='  RESTRICCIONES  (≤ / ≥ / =)  —  Nombre | Coeficientes (A) | Tipo | Limite (b)',
                 font=self.F_BOLD, bg='#fff3e0', fg='#e65100').pack(side='left', padx=6, pady=3)

        # Constraint column headers
        tk.Label(f, text='Nombre (opcional)', font=self.F_SMALL,
                 bg=self.C_CARD, fg=self.C_MUTED, anchor='w').grid(
                 row=5, column=0, sticky='w', padx=4)
        for j in range(n):
            tk.Label(f, text=f'x{j+1}', font=self.F_BOLD, bg=self.C_CARD,
                     fg=self.C_DARK, width=7, anchor='center').grid(row=5, column=j + 1, padx=2)
        tk.Label(f, text='Tipo', font=self.F_BOLD, bg=self.C_CARD,
                 fg=self.C_DARK).grid(row=5, column=n + 1, padx=4)
        tk.Label(f, text='b  (limite)', font=self.F_BOLD, bg=self.C_CARD,
                 fg='#e65100').grid(row=5, column=n + 2, padx=4)

        # Constraint rows
        row_bgs = ['#fafafa', self.C_CARD]
        for i in range(m):
            rbg = row_bgs[i % 2]
            # Name entry (pink)
            rne = tk.Entry(f, width=16, font=self.F_SMALL, justify='left',
                           relief='solid', bd=1, bg='#fce4ec')
            rne.insert(0, f'Restriccion {i + 1}')
            rne.grid(row=6 + i, column=0, padx=4, pady=2, sticky='ew')
            rne.bind('<KeyRelease>', upd)
            self.entries_rnames.append(rne)

            row_e     = []
            row_signs = []
            for j in range(n):
                (sv, btn), e, cell = self._make_sign_cell(f, rbg, upd)
                cell.grid(row=6 + i, column=j + 1, padx=2, pady=2)
                row_signs.append((sv, btn))
                row_e.append(e)
            self.entries_A.append(row_e)
            self.entries_signs_A.append(row_signs)

            # Constraint type selector
            cv = tk.StringVar(value='<=')
            cb = ttk.Combobox(f, textvariable=cv, values=['<=', '>=', '='],
                              width=4, state='readonly', font=self.F_SMALL)
            cb.grid(row=6 + i, column=n + 1, padx=4, pady=2)
            cb.bind('<<ComboboxSelected>>', upd)
            self.entries_ctypes.append(cv)

            be = tk.Entry(f, width=7, font=self.F_BODY, justify='center',
                          relief='solid', bd=1, bg='#fff8e1')  # amber = limit
            be.insert(0, '0')
            be.grid(row=6 + i, column=n + 2, padx=4, pady=2)
            be.bind('<KeyRelease>', upd)
            self.entries_b.append(be)

        # ── Live formula preview ──
        ttk.Separator(f, orient='horizontal').grid(row=6 + m, column=0,
                      columnspan=n + 4, sticky='ew', pady=(8, 2))
        prev_bar = tk.Frame(f, bg='#263238')
        prev_bar.grid(row=7 + m, column=0, columnspan=n + 4, sticky='ew')
        tk.Label(prev_bar,
                 text='  Vista previa del modelo (se actualiza al escribir):',
                 font=self.F_SMALL, bg='#263238', fg='#80cbc4').pack(
                 side='left', padx=6, pady=2)

        self.lp_preview = tk.Text(
            f, font=self.F_MONO, height=m + 3,
            bg='#1e272e', fg='#a5d6a7', relief='flat',
            wrap='none', state='disabled', takefocus=False)
        self.lp_preview.grid(row=8 + m, column=0, columnspan=n + 4,
                             sticky='ew', pady=(0, 4))

        # ── Action buttons ──
        btn_row = tk.Frame(f, bg=self.C_CARD)
        btn_row.grid(row=9 + m, column=0, columnspan=n + 4, pady=12)
        self._btn(btn_row, '  Resolver  ', self._solve_custom,
                  color=self.C_GREEN).pack(side='left', padx=4)
        self._btn(btn_row, 'Limpiar', self._clear_inputs,
                  color=self.C_RED).pack(side='left', padx=4)

        upd()  # initial preview render
        self.root.after(50, lambda: self._lp_bind_scroll(self.input_inner))

    def _entry(self, parent, w=6, val='0'):
        e = tk.Entry(parent, width=w, font=self.F_BODY, justify='center',
                     relief='solid', bd=1, bg='#fafafa')
        e.insert(0, val)
        return e

    def _clear_inputs(self):
        for e in self.entries_c:
            e.delete(0, 'end'); e.insert(0, '0')
        for sv, btn in self.entries_signs_c:
            sv.set('+'); btn.configure(text='+', bg='#c8e6c9', fg='#1b5e20')
        for row_e, row_s in zip(self.entries_A, self.entries_signs_A):
            for e in row_e:
                e.delete(0, 'end'); e.insert(0, '0')
            for sv, btn in row_s:
                sv.set('+'); btn.configure(text='+', bg='#c8e6c9', fg='#1b5e20')
        for e in self.entries_b:
            e.delete(0, 'end'); e.insert(0, '0')
        for cv in self.entries_ctypes:
            cv.set('<=')
        self._update_lp_preview(self.n_var.get(), self.n_con.get(), self.tipo_v.get())

    def _update_lp_preview(self, n, m, tipo):
        if self.lp_preview is None:
            return
        try:
            if not self.lp_preview.winfo_exists():
                return
        except Exception:
            return

        tipo_lbl = 'MAX' if tipo == 'max' else 'MIN'
        vnames = [f'x{j+1}' for j in range(n)]

        def _val(e):
            try:
                return float(e.get())
            except ValueError:
                return None

        def _term(v, name):
            if v == 1:  return name
            if v == -1: return f'-{name}'
            return f'{v:g}{name}'

        def _build_expr(vals, names):
            terms = [(v, n) for v, n in zip(vals, names) if v != 0]
            if not terms:
                return '0'
            result = _term(terms[0][0], terms[0][1])
            for v, n in terms[1:]:
                if v < 0:
                    result += f' - {_term(-v, n)}'
                else:
                    result += f' + {_term(v, n)}'
            return result

        # Objective (apply sign toggles)
        c_vals = []
        for j, e in enumerate(self.entries_c):
            v = _val(e) or 0
            if j < len(self.entries_signs_c) and self.entries_signs_c[j][0].get() == '-':
                v = -abs(v)
            c_vals.append(v)
        obj = _build_expr(c_vals, vnames)
        lines = [f'{tipo_lbl}  Z = {obj}', '', 's.a.']

        for i in range(m):
            rname = ''
            if i < len(self.entries_rnames):
                try:
                    rname = self.entries_rnames[i].get().strip()
                except Exception:
                    pass
            ctype = '<='
            if i < len(self.entries_ctypes):
                try:
                    ctype = self.entries_ctypes[i].get()
                except Exception:
                    pass
            a_vals = []
            if i < len(self.entries_A):
                for j, e in enumerate(self.entries_A[i]):
                    v = _val(e) or 0
                    if (i < len(self.entries_signs_A) and
                            j < len(self.entries_signs_A[i]) and
                            self.entries_signs_A[i][j][0].get() == '-'):
                        v = -abs(v)
                    a_vals.append(v)
            b_str = '?'
            if i < len(self.entries_b):
                v = _val(self.entries_b[i])
                if v is not None:
                    b_str = f'{v:g}'
            lhs = _build_expr(a_vals, vnames)
            suffix = f'   ({rname})' if rname else ''
            lines.append(f'  {lhs}  {ctype}  {b_str}{suffix}')

        lines += ['', '  ' + ',  '.join(f'{nm} >= 0' for nm in vnames)]

        self.lp_preview.configure(state='normal')
        self.lp_preview.delete('1.0', 'end')
        self.lp_preview.insert('1.0', '\n'.join(lines))
        self.lp_preview.configure(state='disabled')

    # ── Output panel (right) ───────────────────────────────────────────────────
    def _solver_output(self, parent):
        top = self._card(parent, 'Proceso de Solucion — Iteraciones del Tableau Simplex')
        top.pack(fill='both', expand=True, pady=(0, 6))

        self.out_text = scrolledtext.ScrolledText(
            top, font=self.F_MONO, state='disabled',
            bg=self.C_TERMINAL, fg=self.C_TERM_FG,
            wrap='none', relief='flat', insertbackground='white')
        self.out_text.pack(fill='both', expand=True, padx=6, pady=6)

        if MPL:
            graph_card = self._card(parent, 'Visualizacion de la Solucion')
            graph_card.pack(fill='x', pady=(0, 6))
            graph_card.configure(height=240)
            graph_card.pack_propagate(False)

            self.fig = Figure(figsize=(9, 2.8), dpi=82, facecolor=self.C_TERMINAL)
            self.ax  = self.fig.add_subplot(111)
            self.ax.set_facecolor('#2d2d2d')
            self.ax.text(0.5, 0.5, 'La grafica aparece al resolver un problema.',
                         transform=self.ax.transAxes, ha='center', va='center',
                         color='#9e9e9e', fontsize=10)
            self.mpl_canvas = FigureCanvasTkAgg(self.fig, master=graph_card)
            self.mpl_canvas.get_tk_widget().pack(fill='both', expand=True, padx=6, pady=6)
            self.mpl_canvas.draw()

    # ── Solve custom problem ───────────────────────────────────────────────────
    def _solve_custom(self):
        if not self.entries_c:
            messagebox.showwarning('Aviso', 'Primero genere la tabla de entrada.')
            return
        try:
            c = []
            for j, e in enumerate(self.entries_c):
                v = float(e.get())
                if j < len(self.entries_signs_c) and self.entries_signs_c[j][0].get() == '-':
                    v = -abs(v)
                c.append(v)
            A = []
            for i, row_e in enumerate(self.entries_A):
                row = []
                for j, e in enumerate(row_e):
                    v = float(e.get())
                    if (i < len(self.entries_signs_A) and
                            j < len(self.entries_signs_A[i]) and
                            self.entries_signs_A[i][j][0].get() == '-'):
                        v = -abs(v)
                    row.append(v)
                A.append(row)
            b = [float(e.get()) for e in self.entries_b]
        except ValueError:
            messagebox.showerror('Error', 'Ingrese valores numericos validos en todos los campos.')
            return
        if any(bi < 0 for bi in b):
            messagebox.showerror('Error', 'Los valores b deben ser no negativos.')
            return

        n = len(c)
        m = len(b)
        tipo = self.tipo_v.get()
        ctypes = ([cv.get() for cv in self.entries_ctypes]
                  if self.entries_ctypes else ['<='] * m)

        solver = SimplexSolver(c, A, b, tipo, constraint_types=ctypes)
        status = solver.solve()
        var_all = solver.var_names()
        self.last_solver = solver

        self._write_output(self.out_text, '')
        body = ''

        if status == 'optimal':
            x, Z = solver.get_solution()
            slacks = solver.get_slack_values()
            for snap in solver.history:
                body += utils.format_tableau(
                    snap['tableau'], var_all, snap['basic_vars'],
                    snap['iteration'], snap['pivot_row'], snap['pivot_col'])
                if snap.get('entering'):
                    body += f"  => Entra: {snap['entering']}   Sale: {snap['leaving']}\n"
                if snap['status'] == 'optimal':
                    body += '  => OPTIMO ALCANZADO\n'
            rest_nombres = None
            if self.entries_rnames:
                rest_nombres = [e.get().strip() or f'R{i+1}'
                                for i, e in enumerate(self.entries_rnames)]
            body += utils.format_solution(x, Z, [f'x{i+1}' for i in range(n)],
                                          tipo, restricciones_nombres=rest_nombres,
                                          slacks=slacks)
            self._write_output(self.out_text, body)
            if MPL:
                if n == 2:
                    self._graph_2d(c, A, b, x, tipo)
                else:
                    self._graph_bar(x, [f'x{i+1}' for i in range(n)], Z, tipo)
        else:
            msgs = {
                'unbounded': 'El problema es ILIMITADO — no existe solucion optima finita.',
                'infeasible': 'El problema es INFACTIBLE.',
                'max_iterations': 'Se alcanzo el maximo de iteraciones.',
            }
            self._write_output(self.out_text, f'\n\nESTADO: {msgs.get(status, status)}\n')

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 — EJEMPLO PROPIO
    # ══════════════════════════════════════════════════════════════════════════

    def _tab_example(self, parent):
        p = PROBLEMA
        left = tk.Frame(parent, bg=self.C_BG, width=450)
        left.pack(side='left', fill='y', padx=(8, 4), pady=8)
        left.pack_propagate(False)

        right = tk.Frame(parent, bg=self.C_BG)
        right.pack(side='right', fill='both', expand=True, padx=(4, 8), pady=8)

        self._example_left(left, p)
        self._example_right(right, p)

    # ── Left: description ──────────────────────────────────────────────────────
    def _example_left(self, parent, p):
        n = len(p['c'])
        ctypes = p.get('constraint_types', ['<='] * len(p['b']))

        # Title + level
        title_card = self._card(parent)
        title_card.pack(fill='x', pady=(0, 6))
        tk.Label(title_card, text=p['titulo'],
                 font=('Segoe UI', 11, 'bold'), fg=self.C_DARK,
                 bg=self.C_CARD, wraplength=420, justify='left'
                 ).pack(padx=12, pady=(10, 2), anchor='w')
        lvl_bg = self.C_RED if p['nivel'] == 'Alto' else '#e65100'
        lf = tk.Frame(title_card, bg=lvl_bg)
        lf.pack(fill='x', padx=12, pady=(2, 2))
        tk.Label(lf, text=f"  Nivel de Dificultad: {p['nivel'].upper()}  ",
                 font=self.F_BOLD, fg='white', bg=lvl_bg).pack(side='left', pady=4)
        tk.Label(title_card, text=p['nivel_descripcion'],
                 font=self.F_SMALL, fg=self.C_MUTED, bg=self.C_CARD,
                 wraplength=420, justify='left').pack(padx=12, pady=(2, 8), anchor='w')

        # Description
        desc_card = self._card(parent, 'Descripcion del Problema')
        desc_card.pack(fill='x', pady=(0, 6))
        tk.Label(desc_card, text=p['descripcion'],
                 font=self.F_SMALL, fg=self.C_TXT, bg=self.C_CARD,
                 wraplength=420, justify='left').pack(padx=12, pady=8, anchor='w')

        # Data table — dynamic columns based on number of variables
        tbl_card = self._card(parent, 'Tabla de Coeficientes, Tipos y Limites')
        tbl_card.pack(fill='x', pady=(0, 6))

        var_cols = [f'x{j+1}' for j in range(n)]
        cols = ('Restriccion',) + tuple(var_cols) + ('Tipo', 'b')
        tv = ttk.Treeview(tbl_card, columns=cols, show='headings',
                          height=len(p['b']) + 1)
        tv.heading('Restriccion', text='Restriccion')
        tv.column('Restriccion', width=160, anchor='w')
        for vc in var_cols:
            tv.heading(vc, text=vc)
            tv.column(vc, width=46, anchor='center')
        tv.heading('Tipo', text='Tipo')
        tv.column('Tipo', width=42, anchor='center')
        tv.heading('b', text='b')
        tv.column('b', width=52, anchor='center')

        tv.tag_configure('even',     background='#f5f5f5')
        tv.tag_configure('odd',      background=self.C_CARD)
        tv.tag_configure('leq',      background='#e3f2fd')
        tv.tag_configure('geq',      background='#fce4ec')
        tv.tag_configure('eq',       background='#f3e5f5')
        tv.tag_configure('ganancia', background='#e8f5e9', foreground=self.C_GREEN)

        type_tags = {'<=': 'leq', '>=': 'geq', '=': 'eq'}
        for i, name in enumerate(p['restricciones_nombres']):
            a_row = [p['A'][i][j] for j in range(n)]
            tag = type_tags.get(ctypes[i], 'even' if i % 2 == 0 else 'odd')
            tv.insert('', 'end',
                      values=(name,) + tuple(a_row) + (ctypes[i], p['b'][i]),
                      tags=(tag,))
        tv.insert('', 'end',
                  values=('Ganancia ($/kg)',) + tuple(p['c']) + ('—', '—'),
                  tags=('ganancia',))

        # Legend for constraint colors
        leg = tk.Frame(tbl_card, bg=self.C_CARD)
        leg.pack(fill='x', padx=8, pady=(0, 4))
        for color, lbl in [('#e3f2fd', '<=  holgura'),
                           ('#fce4ec', '>=  exceso + artif.'),
                           ('#f3e5f5', '=   artificial')]:
            dot = tk.Frame(leg, bg=color, width=12, height=12, relief='solid', bd=1)
            dot.pack(side='left', padx=(4, 1))
            tk.Label(leg, text=lbl, font=('Segoe UI', 8),
                     bg=self.C_CARD, fg=self.C_TXT).pack(side='left', padx=(0, 10))

        tv.pack(fill='x', padx=8, pady=(6, 2))

        # Mathematical model
        model_card = self._card(parent, 'Modelo Matematico')
        model_card.pack(fill='x', pady=(0, 6))
        mt = tk.Text(model_card, font=self.F_MONO10, height=9,
                     bg=self.C_CODE_BG, fg=self.C_CODE_FG,
                     relief='flat', wrap='none', state='normal')
        mt.pack(fill='x', padx=8, pady=8)
        mt.insert('1.0', p['modelo_texto'])
        mt.configure(state='disabled')

    # ── Right: solution display ────────────────────────────────────────────────
    def _example_right(self, parent, p):
        # Controls bar
        ctrl = tk.Frame(parent, bg=self.C_BG)
        ctrl.pack(fill='x', pady=(0, 6))

        self._btn(ctrl, '  Resolver Ejemplo  ', self._solve_example,
                  color=self.C_GREEN).pack(side='left', padx=4)

        self.ex_iter_lbl = tk.Label(ctrl, text='Iteracion: —',
                                    font=self.F_BODY, bg=self.C_BG, fg=self.C_TXT)
        self.ex_iter_lbl.pack(side='left', padx=16)

        self._btn(ctrl, 'Siguiente >', self._ex_next,
                  color=self.C_ACCENT).pack(side='right', padx=4)
        self._btn(ctrl, '< Anterior', self._ex_prev,
                  color=self.C_ACCENT).pack(side='right', padx=4)

        # Tableau display
        tab_card = self._card(parent, 'Tableau Simplex — Navegacion por Iteraciones')
        tab_card.pack(fill='both', expand=True, pady=(0, 6))

        self.ex_text = scrolledtext.ScrolledText(
            tab_card, font=self.F_MONO10, state='disabled',
            bg=self.C_TERMINAL, fg=self.C_TERM_FG,
            wrap='none', relief='flat')
        self.ex_text.pack(fill='both', expand=True, padx=6, pady=6)

        # Solution summary
        sol_card = self._card(parent, 'Resultado Final e Interpretacion')
        sol_card.pack(fill='x', pady=(0, 6))
        sol_card.configure(height=130)
        sol_card.pack_propagate(False)

        self.ex_sol_lbl = tk.Label(
            sol_card,
            text="Presione 'Resolver Ejemplo' para ver la solucion optima.",
            font=self.F_BODY, fg=self.C_MUTED, bg=self.C_CARD,
            wraplength=700, justify='left')
        self.ex_sol_lbl.pack(padx=12, pady=12, anchor='w')

        # Export button
        self._btn(parent, 'Exportar Resultados a .txt',
                  self._export_example, color='#4a148c').pack(pady=4, anchor='e', padx=4)

    # ── Solve example ──────────────────────────────────────────────────────────
    def _solve_example(self):
        p = PROBLEMA
        n = len(p['c'])
        ctypes = p.get('constraint_types', ['<='] * len(p['b']))

        solver = SimplexSolver(p['c'], p['A'], p['b'], p['tipo'],
                               constraint_types=ctypes)
        status = solver.solve()

        self.ex_solver   = solver
        self.ex_history  = solver.history
        self.ex_varnames = solver.var_names()

        if status == 'optimal':
            x, Z = solver.get_solution()
            slacks = solver.get_slack_values()

            self.ex_iter = len(self.ex_history) - 1
            self._show_ex_iter()

            # Build interpretation line
            parts = [f'x{i+1}={x[i]:.0f}' for i in range(n) if x[i] > 1e-6]
            zero_parts = [f'x{i+1}=0' for i in range(n) if x[i] <= 1e-6]
            val_str = '  |  '.join(parts + zero_parts)
            sol_lines = [
                f'Solucion Optima:  {val_str}',
                f'Ganancia Maxima:  Z* = ${Z:.2f}',
                '',
                'Interpretacion: AgroMix debe asignar '
                + ', '.join(f'{x[i]:.0f} kg de {p["variables"][i]}'
                            for i in range(n) if x[i] > 1e-6)
                + f' para obtener una ganancia maxima de ${Z:.2f}/dia.',
            ]
            if slacks.size > 0:
                ns = solver.n_slack
                slack_names = p['restricciones_nombres']
                leq_idx = [i for i, t in enumerate(ctypes) if t == '<=']
                slack_info = '  |  '.join(
                    f's{k+1}={slacks[k]:.1f} ({slack_names[leq_idx[k]]})'
                    for k in range(ns))
                sol_lines.append(f'\nHolguras: {slack_info}')
            self.ex_sol_lbl.configure(
                text='\n'.join(sol_lines),
                font=('Segoe UI', 10, 'bold'), fg=self.C_GREEN)
        else:
            self.ex_sol_lbl.configure(
                text=f'Estado: {status}', fg=self.C_RED)

    # ── Navigation ─────────────────────────────────────────────────────────────
    def _show_ex_iter(self):
        if not self.ex_history:
            return
        idx  = max(0, min(self.ex_iter, len(self.ex_history) - 1))
        snap = self.ex_history[idx]
        total = len(self.ex_history)

        ent = snap.get('entering') or '—'
        sal = snap.get('leaving')  or '—'
        self.ex_iter_lbl.configure(
            text=f"Iteracion {snap['iteration']} de {total-1}  |  Entra: {ent}  |  Sale: {sal}")

        text = utils.format_tableau(
            snap['tableau'], self.ex_varnames, snap['basic_vars'],
            snap['iteration'], snap['pivot_row'], snap['pivot_col'])

        if snap['status'] == 'optimal':
            text += '\n  => OPTIMO ALCANZADO\n'
        elif snap.get('entering'):
            text += f"\n  => Siguiente pivote: entra {ent}, sale {sal}\n"

        self._write_output(self.ex_text, text)

    def _ex_prev(self):
        if self.ex_iter > 0:
            self.ex_iter -= 1
            self._show_ex_iter()

    def _ex_next(self):
        if self.ex_history and self.ex_iter < len(self.ex_history) - 1:
            self.ex_iter += 1
            self._show_ex_iter()

    # ── Export ─────────────────────────────────────────────────────────────────
    def _export_example(self):
        if self.ex_solver is None:
            messagebox.showwarning('Aviso', "Primero resuelva el ejemplo.")
            return
        p = PROBLEMA
        n = len(p['c'])
        x, Z = self.ex_solver.get_solution()
        if x is None:
            messagebox.showerror('Error', 'No se encontro solucion optima.')
            return

        fp = filedialog.asksaveasfilename(
            defaultextension='.txt',
            filetypes=[('Archivo de texto', '*.txt')],
            initialfile='solucion_AgroMix.txt',
            title='Guardar resultados')
        if not fp:
            return

        utils.export_results(
            titulo=p['titulo'],
            modelo=p['modelo_texto'],
            history=self.ex_history,
            x=x, Z=Z, tipo=p['tipo'],
            var_names_all=self.ex_varnames,
            var_names_decision=self.ex_varnames[:n],
            restricciones_nombres=p['restricciones_nombres'],
            slacks=self.ex_solver.get_slack_values(),
            filepath=fp, config=CONFIG)
        messagebox.showinfo('Exportacion exitosa', f'Archivo guardado en:\n{fp}')

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3 — ACERCA DEL PROYECTO
    # ══════════════════════════════════════════════════════════════════════════

    def _tab_about(self, parent):
        left = tk.Frame(parent, bg=self.C_BG, width=460)
        left.pack(side='left', fill='y', padx=(8, 4), pady=8)
        left.pack_propagate(False)

        right = tk.Frame(parent, bg=self.C_BG)
        right.pack(side='right', fill='both', expand=True, padx=(4, 8), pady=8)

        self._about_presenter(left)
        self._about_algorithm(right)

    # ── Presenter info ─────────────────────────────────────────────────────────
    def _about_presenter(self, parent):
        pcard = self._card(parent, 'Presentadores del Proyecto')
        pcard.pack(fill='x', pady=(0, 8))

        # Student name strip (highlighted)
        for key, label in [('nombre_estudiante', 'Estudiante 1'),
                            ('nombre_companera',  'Estudiante 2')]:
            strip = tk.Frame(pcard, bg='#e8eaf6')
            strip.pack(fill='x', padx=12, pady=(6, 2))
            tk.Label(strip, text=f'{label}:', font=self.F_BOLD, fg=self.C_DARK,
                     bg='#e8eaf6', width=14, anchor='w').pack(side='left', padx=(8, 0), pady=4)
            tk.Label(strip, text=CONFIG[key], font=('Segoe UI', 10, 'bold'),
                     fg=self.C_DARK, bg='#e8eaf6').pack(side='left', pady=4)

        ttk.Separator(pcard, orient='horizontal').pack(fill='x', padx=12, pady=6)

        fields = [
            ('Universidad', CONFIG['universidad']),
            ('Facultad',    CONFIG['facultad']),
            ('Materia',     CONFIG['materia']),
            ('Profesor',    CONFIG['profesor']),
            ('Semestre',    CONFIG['semestre']),
        ]
        for lbl, val in fields:
            row = tk.Frame(pcard, bg=self.C_CARD)
            row.pack(fill='x', padx=12, pady=3)
            tk.Label(row, text=f'{lbl}:', font=self.F_BOLD, fg=self.C_DARK,
                     bg=self.C_CARD, width=14, anchor='w').pack(side='left')
            tk.Label(row, text=val, font=self.F_BODY, fg=self.C_TXT,
                     bg=self.C_CARD).pack(side='left')
        tk.Frame(pcard, bg=self.C_CARD, height=6).pack()

        # Difficulty card
        p = PROBLEMA
        dcard = self._card(parent, 'Ejemplo Propio — Dificultad')
        dcard.pack(fill='x', pady=(0, 8))

        lvl_frame = tk.Frame(dcard, bg=self.C_RED, height=38)
        lvl_frame.pack(fill='x', padx=12, pady=(8, 4))
        lvl_frame.pack_propagate(False)
        tk.Label(lvl_frame, text=f"  NIVEL: {p['nivel'].upper()}  ",
                 font=('Segoe UI', 13, 'bold'), fg='white', bg=self.C_RED
                 ).pack(pady=5)

        tk.Label(dcard, text=p['nivel_descripcion'],
                 font=self.F_SMALL, fg=self.C_TXT, bg=self.C_CARD,
                 wraplength=420, justify='left').pack(padx=12, pady=4, anchor='w')
        tk.Label(dcard, text=p['titulo'],
                 font=self.F_BOLD, fg=self.C_DARK, bg=self.C_CARD,
                 wraplength=420).pack(padx=12, pady=(4, 10), anchor='w')

    # ── Algorithm description ──────────────────────────────────────────────────
    def _about_algorithm(self, parent):
        algo_card = self._card(parent, 'Algoritmo Simplex con Metodo Big-M — Restricciones Mixtas')
        algo_card.pack(fill='both', expand=True)

        canvas = tk.Canvas(algo_card, bg=self.C_CARD, highlightthickness=0)
        vsb = ttk.Scrollbar(algo_card, orient='vertical', command=canvas.yview)
        inner = tk.Frame(canvas, bg=self.C_CARD)
        inner.bind('<Configure>',
                   lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=inner, anchor='nw')
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side='right', fill='y', padx=(0, 4), pady=6)
        canvas.pack(side='left', fill='both', expand=True, padx=(6, 0), pady=6)
        _algo_bind = self._bind_mousewheel(canvas)
        self.root.after(100, lambda: _algo_bind(inner))

        # Variable legend strip
        leg_f = tk.Frame(inner, bg='#e8eaf6', relief='flat', bd=0)
        leg_f.pack(fill='x', padx=6, pady=(4, 2))
        tk.Label(leg_f, text='Variables auxiliares segun tipo de restriccion:',
                 font=self.F_BOLD, bg='#e8eaf6', fg=self.C_DARK).pack(
                 side='left', padx=(10, 16), pady=6)
        for bg, fg, txt in [('#e3f2fd', '#0d47a1', '<=  +s (holgura)'),
                             ('#fce4ec', '#880e4f', '>=  -e (exceso)  +a (artif., Big-M)'),
                             ('#f3e5f5', '#4a148c', ' =  +a (artif., Big-M)')]:
            tk.Label(leg_f, text=f'  {txt}  ', font=self.F_SMALL,
                     bg=bg, fg=fg, relief='solid', bd=1).pack(
                     side='left', padx=4, pady=4)

        steps = [
            ('#1565c0', '1. Identificar tipos de restriccion',
             'Clasificar cada restriccion como <=, >= o =. '
             'Cada tipo determina que variables auxiliares se agregan al modelo '
             'para convertirlo a forma estandar de igualdades.'),
            ('#1565c0', '2. Agregar variables auxiliares',
             '— Restriccion <=: agregar variable de holgura +s (representa recurso no usado).\n'
             '— Restriccion >=: agregar exceso -e (representa excedente sobre el minimo) '
             'Y variable artificial +a para la base inicial.\n'
             '— Restriccion =: agregar solo variable artificial +a.'),
            ('#1565c0', '3. Penalizacion Big-M en la funcion objetivo',
             'A cada variable artificial se le asigna un coeficiente de penalizacion '
             'M = 1,000,000 en la fila Z. Esto obliga al algoritmo Simplex a expulsar '
             'las artificiales de la base antes de alcanzar el optimo real.'),
            ('#1565c0', '4. Ajuste inicial de la fila Z',
             'Las variables artificiales comienzan en la base. Para mantener '
             'la consistencia del tableau se resta M veces cada fila con artificial '
             'de la fila Z. Esto elimina los coeficientes M de las columnas artificiales.'),
            ('#283593', '5. Tableau inicial — columna pivote',
             'Identificar la columna con el coeficiente mas negativo en la fila Z '
             '(criterio de Dantzig). Esa variable entra a la base. '
             'Si no hay negativos, la solucion actual es optima.'),
            ('#283593', '6. Prueba de la razon minima — fila pivote',
             'Dividir b_i entre a_ij (solo coeficientes positivos) y tomar '
             'el cociente minimo. La fila correspondiente sale de la base. '
             'Si ningun coeficiente es positivo, el problema es ilimitado.'),
            ('#283593', '7. Operacion pivote — eliminacion gaussiana',
             'Dividir la fila pivote entre el elemento pivote (queda 1). '
             'Luego aplicar eliminacion gaussiana para poner a 0 todos los '
             'demas elementos de la columna pivote, incluida la fila Z.'),
            ('#283593', '8. Verificacion de optimalidad e infactibilidad',
             'Repetir pasos 5-7 hasta que la fila Z no tenga negativos (optimo). '
             'Si al final alguna variable artificial permanece en la base con '
             'valor > 0, el problema es INFACTIBLE (no existe solucion factible).'),
        ]

        for color, title, desc in steps:
            sf = tk.Frame(inner, bg=self.C_LIGHT, pady=4)
            sf.pack(fill='x', padx=6, pady=3)
            num_lbl = title.split('.')[0].strip()
            num = tk.Label(sf, text=num_lbl, font=('Segoe UI', 13, 'bold'),
                           fg='white', bg=color, width=3, anchor='center')
            num.pack(side='left', padx=(8, 10), pady=6)
            txt_f = tk.Frame(sf, bg=self.C_LIGHT)
            txt_f.pack(side='left', fill='both', expand=True, pady=4, padx=(0, 8))
            tk.Label(txt_f, text=title, font=self.F_BOLD, fg=self.C_DARK,
                     bg=self.C_LIGHT, anchor='w').pack(fill='x')
            tk.Label(txt_f, text=desc, font=self.F_SMALL, fg=self.C_TXT,
                     bg=self.C_LIGHT, wraplength=530, justify='left',
                     anchor='w').pack(fill='x')

        # Example note
        note = tk.Frame(inner, bg='#fff8e1')
        note.pack(fill='x', padx=6, pady=(6, 4))
        p = PROBLEMA
        ct = p.get('constraint_types', [])
        n_leq = ct.count('<=')
        n_geq = ct.count('>=')
        n_eq  = ct.count('=')
        tk.Label(note,
                 text=f'Ejemplo propio — AgroMix S.A.S: {len(p["c"])} variables, '
                      f'{len(p["b"])} restricciones ({n_leq}x<=, {n_geq}x>=, {n_eq}x=). '
                      f'Big-M genera {n_leq} holguras, {n_geq} excesos y '
                      f'{n_geq + n_eq} artificiales. Tableau de '
                      f'{len(p["b"])+1} filas x '
                      f'{len(p["c"]) + n_leq + n_geq + (n_geq+n_eq) + 1} columnas.\n'
                      f'Solucion optima: x1=160, x2=0, x3=40, x4=0  =>  Z* = $1520/dia.\n'
                      f'Casos especiales detectados: ilimitado (sin fila pivote), '
                      f'infactible (artificial en base), degenerado (empate en razon minima).',
                 font=self.F_SMALL, fg='#5d4037', bg='#fff8e1',
                 wraplength=560, justify='left').pack(padx=12, pady=8)

    # ══════════════════════════════════════════════════════════════════════════
    # MATPLOTLIB GRAPHS
    # ══════════════════════════════════════════════════════════════════════════

    def _graph_2d(self, c, A, b, x_opt, tipo):
        A, b, c = np.array(A), np.array(b), np.array(c)
        lim = max(float(np.max(b)), 10.0) * 1.35
        x1v = np.linspace(0, lim, 500)
        X1, X2 = np.meshgrid(x1v, np.linspace(0, lim, 500))

        feas = np.ones_like(X1, dtype=bool)
        for i in range(len(b)):
            feas &= (A[i, 0] * X1 + A[i, 1] * X2 <= b[i])
        feas &= (X1 >= 0) & (X2 >= 0)

        self.ax.clear()
        self.ax.set_facecolor('#2d2d2d')
        self.ax.contourf(X1, X2, feas.astype(float),
                         levels=[0.5, 1.5], alpha=0.22, colors=['#42a5f5'])

        clrs = ['#ff7043', '#66bb6a', '#ab47bc', '#26c6da', '#ffca28', '#ec407a']
        for i in range(len(b)):
            if A[i, 1] != 0:
                x2l = (b[i] - A[i, 0] * x1v) / A[i, 1]
                mask = (x2l >= 0) & (x2l <= lim)
                self.ax.plot(x1v[mask], x2l[mask],
                             color=clrs[i % len(clrs)], lw=1.5,
                             label=f'R{i+1}', alpha=0.85)
            elif A[i, 0] != 0:
                self.ax.axvline(b[i] / A[i, 0],
                                color=clrs[i % len(clrs)], lw=1.5, label=f'R{i+1}')

        Z_opt = c[0] * x_opt[0] + c[1] * x_opt[1]
        if c[1] != 0:
            x2z = (Z_opt - c[0] * x1v) / c[1]
            mk = (x2z >= 0) & (x2z <= lim)
            self.ax.plot(x1v[mk], x2z[mk], 'y--', lw=2,
                         label=f'Z={Z_opt:.2f}', alpha=0.9)

        self.ax.plot(x_opt[0], x_opt[1], '*', color='#ffeb3b', markersize=14,
                     label=f'Optimo ({x_opt[0]:.2f}, {x_opt[1]:.2f})', zorder=5)
        self._style_ax(self.ax, 'x1', 'x2', 'Region Factible y Punto Optimo', lim)
        self.fig.tight_layout()
        self.mpl_canvas.draw()

    def _graph_bar(self, x, var_names, Z, tipo):
        self.ax.clear()
        self.ax.set_facecolor('#2d2d2d')
        clrs = ['#42a5f5', '#66bb6a', '#ff7043', '#ab47bc', '#ffca28', '#26c6da']
        bars = self.ax.bar(var_names, x, color=clrs[:len(x)],
                           alpha=0.85, edgecolor='white', lw=0.5)
        for bar, val in zip(bars, x):
            self.ax.text(bar.get_x() + bar.get_width() / 2,
                         bar.get_height() + max(x, default=0) * 0.01,
                         f'{val:.3f}', ha='center', va='bottom',
                         color='#e0e0e0', fontsize=9)
        tipo_lbl = 'MAX' if tipo == 'max' else 'MIN'
        self._style_ax(self.ax, 'Variables', 'Valor optimo',
                       f'Solucion Optima  |  Z* = {Z:.4f}  ({tipo_lbl})')
        self.fig.tight_layout()
        self.mpl_canvas.draw()

    def _style_ax(self, ax, xlabel, ylabel, title, xlim=None):
        ax.set_xlabel(xlabel, color='#bdbdbd', fontsize=9)
        ax.set_ylabel(ylabel, color='#bdbdbd', fontsize=9)
        ax.set_title(title, color='#e0e0e0', fontsize=10, fontweight='bold')
        ax.tick_params(colors='#9e9e9e', labelsize=8)
        for spine in ax.spines.values():
            spine.set_color('#555')
        if xlim:
            ax.set_xlim(0, xlim)
            ax.set_ylim(0, xlim)
        try:
            ax.legend(fontsize=7, loc='upper right',
                      facecolor='#3d3d3d', edgecolor='#555', labelcolor='#e0e0e0')
        except Exception:
            pass

    # ══════════════════════════════════════════════════════════════════════════
    # UTILITIES
    # ══════════════════════════════════════════════════════════════════════════

    def _bind_mousewheel(self, canvas):
        """Bind mouse-wheel scrolling to a Canvas and every widget inside it.
        Returns a function that can be called on the inner frame (or any frame)
        to recursively attach the binding after dynamic content is generated."""
        def _scroll(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), 'units')

        canvas.bind('<MouseWheel>', _scroll)

        def _bind_tree(widget):
            try:
                widget.bind('<MouseWheel>', _scroll)
            except Exception:
                pass
            for child in widget.winfo_children():
                _bind_tree(child)

        return _bind_tree

    @staticmethod
    def _write_output(widget, text):
        widget.configure(state='normal')
        widget.delete('1.0', 'end')
        widget.insert('1.0', text)
        widget.configure(state='disabled')
        widget.see('1.0')
