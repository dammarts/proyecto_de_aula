import numpy as np

BIG_M = 1_000_000


class SimplexSolver:
    """
    Solves LP problems (MAX or MIN) with mixed constraints (<=, >=, =)
    using the Big-M method. Slack, excess and artificial variables are
    added automatically. Each iteration is recorded in self.history.

    Column order in tableau:
        [ x1…xn | s1…sns | e1…ene | a1…ana | b ]
    """

    def __init__(self, c, A, b, tipo='max', constraint_types=None):
        self.tipo = tipo
        self.n_vars = len(c)
        self.n_constraints = len(b)
        self.constraint_types = constraint_types or ['<='] * len(b)
        # For MIN convert to MAX by negating c; restore Z at the end
        self.c = np.array(c, dtype=float) if tipo == 'max' else -np.array(c, dtype=float)
        self.A = np.array(A, dtype=float)
        self.b = np.array(b, dtype=float)
        self.tableau = None
        self.basic_vars = []
        self.history = []
        self.status = None
        self.n_slack = 0
        self.n_excess = 0
        self.n_artif = 0

    # ── Variable names ─────────────────────────────────────────────────────

    def var_names(self):
        names = [f'x{i+1}' for i in range(self.n_vars)]
        s = e = a = 1
        for t in self.constraint_types:
            if t == '<=':
                names.append(f's{s}'); s += 1
        for t in self.constraint_types:
            if t == '>=':
                names.append(f'e{e}'); e += 1
        for t in self.constraint_types:
            if t in ('>=', '='):
                names.append(f'a{a}'); a += 1
        return names

    # ── Build tableau ──────────────────────────────────────────────────────

    def _build_tableau(self):
        m, n = self.n_constraints, self.n_vars
        ctypes = self.constraint_types

        slack_rows   = [i for i, t in enumerate(ctypes) if t == '<=']
        excess_rows  = [i for i, t in enumerate(ctypes) if t == '>=']
        artif_rows   = [i for i, t in enumerate(ctypes) if t in ('>=', '=')]

        ns = len(slack_rows)
        ne = len(excess_rows)
        na = len(artif_rows)
        self.n_slack  = ns
        self.n_excess = ne
        self.n_artif  = na

        total_vars = n + ns + ne + na
        T = np.zeros((m + 1, total_vars + 1))   # +1 for b column

        # Decision-variable columns
        T[:m, :n] = self.A
        # RHS
        T[:m, -1] = self.b

        # Slack columns (one per <= row)
        for k, row_i in enumerate(slack_rows):
            T[row_i, n + k] = 1.0

        # Excess columns (one per >= row)
        for k, row_i in enumerate(excess_rows):
            T[row_i, n + ns + k] = -1.0

        # Artificial columns (one per >= or = row) + Big-M in Z row
        artif_base = n + ns + ne
        for k, row_i in enumerate(artif_rows):
            T[row_i, artif_base + k] = 1.0
            T[m, artif_base + k] = BIG_M    # penalty: drive artificials to 0

        # Initial basis
        basic_vars = [None] * m
        slack_k = 0
        artif_k = 0
        for i, t in enumerate(ctypes):
            if t == '<=':
                basic_vars[i] = n + slack_k
                slack_k += 1
            else:                                # >= or =
                basic_vars[i] = artif_base + artif_k
                artif_k += 1

        self.basic_vars = basic_vars

        # Eliminate artificials from Z row (they are initially basic)
        for k in range(na):
            col = artif_base + k
            row_i = artif_rows[k]
            if T[m, col] != 0:
                T[m] -= T[m, col] * T[row_i]

        # Objective row: decision variables
        T[m, :n] -= self.c   # add negated objective (maximization form)

        self.tableau = T

    # ── Pivot selection ────────────────────────────────────────────────────

    def _pivot_column(self):
        z = self.tableau[-1, :-1]
        idx = int(np.argmin(z))
        return idx if z[idx] < -1e-9 else -1

    def _pivot_row(self, col):
        m = self.n_constraints
        col_vals = self.tableau[:m, col]
        b_vals   = self.tableau[:m, -1]
        with np.errstate(divide='ignore', invalid='ignore'):
            ratios = np.where(col_vals > 1e-10, b_vals / col_vals, np.inf)
        idx = int(np.argmin(ratios))
        return idx if ratios[idx] < np.inf else -1

    # ── Pivot operation ────────────────────────────────────────────────────

    def _pivot(self, row, col):
        self.tableau[row] /= self.tableau[row, col]
        for i in range(len(self.tableau)):
            if i != row:
                self.tableau[i] -= self.tableau[i, col] * self.tableau[row]
        self.basic_vars[row] = col

    # ── Snapshot ───────────────────────────────────────────────────────────

    def _snap(self, iteration, pivot_col=None, pivot_row=None,
              entering=None, leaving=None, status='iterando'):
        return {
            'tableau':    self.tableau.copy(),
            'basic_vars': self.basic_vars.copy(),
            'iteration':  iteration,
            'pivot_col':  pivot_col,
            'pivot_row':  pivot_row,
            'entering':   entering,
            'leaving':    leaving,
            'status':     status,
        }

    # ── Main solve loop ────────────────────────────────────────────────────

    def solve(self):
        self._build_tableau()
        names = self.var_names()
        self.history = []

        for it in range(300):
            col = self._pivot_column()
            if col == -1:
                self.history.append(self._snap(it, status='optimal'))
                self.status = 'optimal'
                break

            row = self._pivot_row(col)
            if row == -1:
                self.history.append(self._snap(it, col, status='unbounded'))
                self.status = 'unbounded'
                break

            entering = names[col]
            leaving  = names[self.basic_vars[row]]
            self.history.append(self._snap(it, col, row, entering, leaving))
            self._pivot(row, col)
        else:
            self.history.append(self._snap(300, status='max_iterations'))
            self.status = 'max_iterations'

        # Infeasibility: any artificial still in basis with positive value?
        if self.status == 'optimal':
            artif_start = self.n_vars + self.n_slack + self.n_excess
            for i, bv in enumerate(self.basic_vars):
                if bv is not None and bv >= artif_start:
                    if self.tableau[i, -1] > 1e-6:
                        self.status = 'infeasible'
                        break

        return self.status

    # ── Extract results ────────────────────────────────────────────────────

    def get_solution(self):
        if self.status != 'optimal':
            return None, None
        n = self.n_vars
        x = np.zeros(n)
        for i, bv in enumerate(self.basic_vars):
            if bv is not None and bv < n:
                x[bv] = self.tableau[i, -1]
        Z = self.tableau[-1, -1]
        if self.tipo == 'min':
            Z = -Z
        return x, Z

    def get_slack_values(self):
        """Returns values of slack variables s1…sns only."""
        n  = self.n_vars
        ns = self.n_slack
        s = np.zeros(ns)
        for i, bv in enumerate(self.basic_vars):
            if bv is not None and n <= bv < n + ns:
                s[bv - n] = self.tableau[i, -1]
        return s
