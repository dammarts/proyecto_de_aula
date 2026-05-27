from datetime import datetime


# ── Tableau formatter ──────────────────────────────────────────────────────────

def format_tableau(tableau, var_names, basic_vars, iteration,
                   pivot_row=None, pivot_col=None):
    """
    Returns a formatted string of the Simplex tableau.
    pivot_row / pivot_col highlight the NEXT pivot to be applied (or None for optimal).
    """
    m = len(basic_vars)
    col_headers = var_names + ['b']
    row_headers = [var_names[bv] for bv in basic_vars] + ['Z']

    CW = 10   # column width
    BW = 5    # basis-variable column width

    lines = []

    # ── Header ──
    sep = '=' * (BW + 3 + CW * len(col_headers))
    lines.append('\n' + sep)
    if iteration == 0:
        lines.append('  TABLEAU INICIAL')
    else:
        lines.append(f'  ITERACION {iteration}')
    lines.append(sep)

    # ── Column labels ──
    hdr = f"  {'VB':>{BW}} |"
    for j, h in enumerate(col_headers):
        marker = '*' if j == pivot_col else ' '
        hdr += f' {marker}{h:>{CW-2}}'
    lines.append(hdr)
    lines.append('  ' + '-' * BW + '-+' + '-' * (CW * len(col_headers)))

    def _fmt(v):
        if abs(v) < 1e-9:
            return '0'
        if abs(v - round(v)) < 1e-6:
            return str(int(round(v)))
        return f'{v:.3f}'.rstrip('0')

    # ── Data rows ──
    for i, rh in enumerate(row_headers):
        row_vals = tableau[i]
        arr = ' <' if i == pivot_row else '  '
        line = f'  {rh:>{BW}} |'
        for j, val in enumerate(row_vals):
            s = _fmt(val)
            if i == pivot_row and j == pivot_col:
                cell = f'[{s:>6}]'
            else:
                cell = f' {s:>7} '
            line += cell
        line += arr
        lines.append(line)

    lines.append(sep + '\n')
    return '\n'.join(lines)


# ── Iteration detail formatter ────────────────────────────────────────────────

def format_iteration_detail(snap, var_names, n_decision):
    """
    Returns a detailed step-by-step algorithmic explanation for a Simplex
    snapshot (one iteration). Shows:
      - Step 1: Z-row analysis → pivot column selection
      - Step 2: Ratio test     → pivot row selection
      - Step 3: Pivot operation summary
    or an optimality / unbounded / infeasibility conclusion.
    """
    import numpy as np

    T          = snap['tableau']
    basic_vars = snap['basic_vars']
    m          = len(basic_vars)
    n_cols     = T.shape[1] - 1          # exclude b column
    pivot_col  = snap.get('pivot_col')
    pivot_row  = snap.get('pivot_row')
    entering   = snap.get('entering')
    leaving    = snap.get('leaving')
    status     = snap.get('status', 'iterando')

    SEP  = '─' * 64
    SEP2 = '·' * 64
    it   = snap['iteration']
    lines = []

    # ── Header ──
    if it == 0:
        lines += [SEP, '  FLUJO ALGORITMICO — TABLEAU INICIAL', SEP]
    else:
        lines += [SEP, f'  FLUJO ALGORITMICO — ITERACION {it}', SEP]

    basic_set = set(basic_vars)

    # ─ TERMINAL STATES ──────────────────────────────────────────────────────
    if status == 'optimal':
        lines += ['',
                  '  CONCLUSION: SOLUCION OPTIMA ALCANZADA',
                  '  ' + SEP2,
                  '  Criterio de optimalidad (MAX): todos los costos',
                  '  reducidos en la fila Z son >= 0.',
                  '  No existe ninguna variable no basica que pueda',
                  '  mejorar el valor de Z al entrar a la base.',
                  '']
        # List current Z row non-negative values for non-basic vars
        nonbasic_info = []
        for j in range(n_cols):
            if j not in basic_set:
                v = T[-1, j]
                if abs(v) < 1e6:       # skip Big-M columns
                    nonbasic_info.append(f'{var_names[j]}={_fv(v)}')
        if nonbasic_info:
            lines.append('  Costos reducidos no basicos: ' + '  '.join(nonbasic_info))
        lines += ['', '  => La solucion en la base actual ES el optimo global.', '']
        return '\n'.join(lines)

    if status == 'unbounded':
        lines += ['',
                  '  CONCLUSION: PROBLEMA ILIMITADO (UNBOUNDED)',
                  '  ' + SEP2,
                  f'  La columna pivote ({var_names[pivot_col] if pivot_col is not None else "?"}) '
                  f'no tiene ninguna entrada positiva.',
                  '  No existe razon minima valida => Z puede crecer',
                  '  indefinidamente => no hay solucion optima finita.', '']
        return '\n'.join(lines)

    # ─ NORMAL ITERATION ──────────────────────────────────────────────────────
    if pivot_col is None:
        return '\n'.join(lines)

    # PASO 1 — Pivot column
    lines += ['', '  PASO 1 — VARIABLE ENTRANTE (Columna Pivote)', '  ' + SEP2,
              '  Regla: elegir la variable NO basica con el costo',
              '  reducido mas negativo en la fila Z (criterio Dantzig).', '']

    zrow = T[-1, :n_cols]
    cand = [(j, zrow[j]) for j in range(n_cols)
            if j not in basic_set and zrow[j] < -1e-6 and abs(zrow[j]) < 1e9]
    cand_sorted = sorted(cand, key=lambda x: x[1])

    lines.append('  Costos reducidos negativos encontrados:')
    if not cand_sorted:
        lines.append('    (ninguno — pero el solver lo detecto como no optimo)')
    for j, v in cand_sorted:
        marker = '  *** ELEGIDO ***' if j == pivot_col else ''
        lines.append(f'    {var_names[j]:>6} : {_fv(v):>12}{marker}')

    lines += ['',
              f'  => Variable entrante: {entering}',
              f'     (coeficiente mas negativo en fila Z = {_fv(zrow[pivot_col])})', '']

    # PASO 2 — Ratio test
    lines += [SEP2,
              '  PASO 2 — VARIABLE SALIENTE (Prueba de la Razon Minima)', SEP2,
              '  Regla: para cada fila i con a[i, col] > 0 calcular',
              '  razon = b[i] / a[i, col]. La fila con razon MINIMA sale.', '']

    col_vals = T[:m, pivot_col]
    b_vals   = T[:m, -1]

    lines.append(f'  {"Fila (VB)":<10} {"a[i,col]":>10}  {"b[i]":>8}  {"Razon b/a":>12}  Nota')
    lines.append('  ' + '-' * 58)
    valid_ratios = []
    for r in range(m):
        vb_name = var_names[basic_vars[r]]
        a_val   = col_vals[r]
        b_val   = b_vals[r]
        if a_val > 1e-10:
            ratio = b_val / a_val
            valid_ratios.append((r, ratio))
            marker = '  *** MINIMO ***' if r == pivot_row else ''
            lines.append(f'  {vb_name:<10} {_fv(a_val):>10}  {_fv(b_val):>8}  {_fv(ratio):>12}{marker}')
        else:
            reason = 'negativo' if a_val < -1e-10 else 'cero'
            lines.append(f'  {vb_name:<10} {_fv(a_val):>10}  {_fv(b_val):>8}  {"—":>12}  a <= 0, omitir')

    if not valid_ratios:
        lines += ['', '  No hay entradas positivas => problema ILIMITADO']
    else:
        min_ratio = min(r for _, r in valid_ratios)
        lines += ['',
                  f'  => Variable saliente: {leaving}',
                  f'     (razon minima = {_fv(min_ratio)})', '']

    # PASO 3 — Pivot operation
    piv_elem = T[pivot_row, pivot_col]
    lines += [SEP2,
              '  PASO 3 — OPERACION PIVOTE (Eliminacion Gaussiana)', SEP2,
              f'  Elemento pivote: a[{leaving}, {entering}] = {_fv(piv_elem)}', '',
              f'  1. Dividir fila "{leaving}" entre {_fv(piv_elem)}',
              f'     => fila "{leaving}" queda con 1 en columna {entering}.',
              f'  2. Para cada otra fila i:',
              f'     fila_i = fila_i - a[i,{entering}] * fila_{leaving}',
              f'     => columna {entering} queda con 0 en todas las demas filas',
              f'        (incluyendo la fila Z).',
              '',
              f'  => Resultado: {entering} ENTRA a la base, {leaving} SALE.',
              '']

    lines.append(SEP)
    return '\n'.join(lines)


def _fv(v):
    """Format a single float compactly (no trailing zeros)."""
    import numpy as np
    if abs(v) < 1e-9:
        return '0'
    if abs(v - round(v)) < 1e-6:
        return str(int(round(v)))
    return f'{v:.4f}'.rstrip('0').rstrip('.')


# ── Solution formatter ─────────────────────────────────────────────────────────

def format_solution(x, Z, var_names_decision, tipo,
                    restricciones_nombres=None, slacks=None):
    """Returns a formatted string with the optimal solution."""
    tipo_label = 'MAXIMO' if tipo == 'max' else 'MINIMO'
    sep = '*' * 55
    lines = ['\n' + sep, f'  SOLUCION OPTIMA ENCONTRADA', sep, '']
    lines.append('  Variables de decision:')
    for xi, name in zip(x, var_names_decision):
        lines.append(f'    {name:12s} = {xi:.4f}')
    lines.append(f'\n  Valor {tipo_label} de Z* = {Z:.4f}')

    if slacks is not None and restricciones_nombres:
        lines.append('\n  Variables de holgura (recursos no usados):')
        for i, (s, name) in enumerate(zip(slacks, restricciones_nombres)):
            estado = 'ACTIVA (recurso agotado)' if abs(s) < 1e-6 else f'holgura = {s:.4f}'
            lines.append(f'    s{i+1} ({name}): {estado}')

    lines.append('\n' + sep + '\n')
    return '\n'.join(lines)


# ── Dual / Sensitivity formatter ──────────────────────────────────────────────

def format_dual_analysis(dual_vals, sens_b, sens_c, b, c,
                         constraint_names, var_names_decision, tipo):
    """
    Returns a formatted string with three analysis sections:
      1. Shadow prices (dual variables w*)
      2. Sensitivity ranges for RHS (b)
      3. Sensitivity ranges for objective coefficients (c)
    """
    import numpy as np
    sep  = '═' * 55
    sep2 = '─' * 55
    lines = ['\n' + sep,
             '  ANALISIS DUAL Y SENSIBILIDAD',
             sep, '']

    # ── 1. Shadow prices ──
    lines.append('  1. Precios Sombra (Variables Duales  w*)')
    lines.append('  ' + sep2)
    lines.append(f'  {"Restriccion":<30} {"w*":>8}   Interpretacion')
    lines.append('  ' + sep2)
    for i, (name, wi) in enumerate(zip(constraint_names, dual_vals)):
        wi_clean = 0.0 if abs(wi) < 1e-6 else wi
        if abs(wi_clean) < 1e-6:
            interp = 'Recurso con holgura (no limitante)'
        else:
            sign_str = 'sube' if wi_clean > 0 else 'baja'
            interp = f'+1 unidad -> Z {sign_str} ${abs(wi_clean):.4f}'
        lines.append(f'  w{i+1} ({name:<26}) {wi_clean:>8.4f}   {interp}')

    # ── 2. RHS sensitivity ──
    lines.append('')
    lines.append('  2. Rangos de Sensibilidad — Lado Derecho (b)')
    lines.append('  ' + sep2)
    lines.append(f'  {"Restriccion":<30} {"b actual":>9}  {"Rango valido"}')
    lines.append('  ' + sep2)
    for i, (name, (lo, hi)) in enumerate(zip(constraint_names, sens_b)):
        lo_str = f'{lo:.2f}' if np.isfinite(lo) else '-inf'
        hi_str = f'{hi:.2f}' if np.isfinite(hi) else '+inf'
        lines.append(f'  b{i+1} ({name:<26}) {b[i]:>9.2f}  [{lo_str}, {hi_str}]')

    # ── 3. Objective sensitivity ──
    lines.append('')
    lines.append('  3. Rangos de Sensibilidad — Funcion Objetivo (c)')
    lines.append('  ' + sep2)
    lines.append(f'  {"Variable":<14} {"c actual":>9}  {"Rango valido"}')
    lines.append('  ' + sep2)
    for j, (name, (lo, hi)) in enumerate(zip(var_names_decision, sens_c)):
        lo_str = f'{lo:.2f}' if np.isfinite(lo) else '-inf'
        hi_str = f'{hi:.2f}' if np.isfinite(hi) else '+inf'
        lines.append(f'  {name:<14} {c[j]:>9.2f}  [{lo_str}, {hi_str}]')

    lines.append('\n' + sep + '\n')
    return '\n'.join(lines)


# ── Export ─────────────────────────────────────────────────────────────────────

def export_results(titulo, modelo, history, x, Z, tipo,
                   var_names_all, var_names_decision,
                   restricciones_nombres, slacks, filepath, config):
    """Writes the complete solution process to a UTF-8 text file."""
    lines = [
        '=' * 70,
        '  PROYECTO DE AULA — INVESTIGACION DE OPERACIONES',
        '  SOLUCIONADOR DE PROGRAMACION LINEAL — METODO SIMPLEX',
        '=' * 70,
        f"  Estudiante  : {config.get('nombre_estudiante', 'N/A')}",
        f"  Universidad : {config.get('universidad', 'N/A')}",
        f"  Materia     : {config.get('materia', 'N/A')}",
        f"  Profesor    : {config.get('profesor', 'N/A')}",
        f"  Semestre    : {config.get('semestre', 'N/A')}",
        f"  Fecha       : {datetime.now().strftime('%Y-%m-%d  %H:%M')}",
        '=' * 70,
        '',
        f'PROBLEMA: {titulo}',
        '',
        'MODELO MATEMATICO:',
        modelo,
        '',
        'PROCESO DE SOLUCION (Metodo Simplex):',
        '',
    ]

    for snap in history:
        it   = snap['iteration']
        T    = snap['tableau']
        bv   = snap['basic_vars']
        pc   = snap['pivot_col']
        pr   = snap['pivot_row']
        ent  = snap.get('entering')
        sal  = snap.get('leaving')
        st   = snap.get('status', '')

        block = format_tableau(T, var_names_all, bv, it, pr, pc)
        if ent:
            block += f'  => Entra: {ent}   Sale: {sal}\n'
        if st == 'optimal':
            block += '  => OPTIMO ALCANZADO\n'
        lines.append(block)

    lines.append(
        format_solution(x, Z, var_names_decision, tipo, restricciones_nombres, slacks)
    )

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


# ══════════════════════════════════════════════════════════════════════════════
# TRANSPORTATION METHOD FORMATTERS
# ══════════════════════════════════════════════════════════════════════════════

LARGE = 1_000_000


def _cell_str(alloc_val, cost_val, highlight=False):
    """Format a single allocation cell: cost[qty]"""
    if cost_val >= LARGE / 2:
        c_str = '  M '
    else:
        c_str = f'{int(cost_val):>3}'
    q_str = f'[{int(round(alloc_val)):>3}]' if alloc_val > 1e-9 else '[   ]'
    marker = '*' if highlight else ' '
    return f'{marker}{c_str}{q_str}'


def format_transport_table(alloc, costs, supply, demand,
                            origins, destinations,
                            loop=None, entering=None):
    """
    Returns a formatted string of the transportation allocation table.
    Cells in `loop` are highlighted with ±.
    """
    m, n = alloc.shape
    loop_plus  = set(loop[0::2]) if loop else set()
    loop_minus = set(loop[1::2]) if loop else set()
    enter_set  = {entering} if entering else set()

    CW = 12   # cell width
    OW = 12   # origin label width
    sep = '-' * (OW + 2 + CW * n + n + 10)

    lines = []
    # Header
    hdr = f"  {'':>{OW}} |"
    for d in destinations:
        hdr += f' {d:^{CW}}'
    hdr += f'  | Oferta'
    lines.append(hdr)
    lines.append('  ' + sep)

    # Rows
    for i in range(m):
        line = f"  {origins[i]:>{OW}} |"
        for j in range(n):
            av = alloc[i, j]
            cv = costs[i, j]
            if (i, j) in loop_plus:
                marker = '+'
            elif (i, j) in loop_minus:
                marker = '-'
            elif (i, j) in enter_set:
                marker = '*'
            else:
                marker = ' '
            if cv >= LARGE / 2:
                cell = f'{marker}  M [{int(round(av)):>3}]'
            else:
                cell = f'{marker}{int(cv):>3}[{int(round(av)):>3}]'
            line += f' {cell:>{CW}}'
        # Supply
        used = alloc[i].sum()
        line += f'  | {int(supply[i]):>5}  (usado={int(round(used)):>3})'
        lines.append(line)

    lines.append('  ' + sep)
    # Demand row
    dem_line = f"  {'Demanda':>{OW}} |"
    for j in range(n):
        cov = int(round(alloc[:, j].sum()))
        dem_line += f' {int(demand[j]):>4}({cov:>3})'
    lines.append(dem_line)
    return '\n'.join(lines)


def format_transport_snap(snap, origins, destinations):
    """Format a complete history snapshot for display."""
    m, n = snap['m'], snap['n']
    alloc = snap['allocation']
    costs = snap['costs']
    supply = snap['supply']
    demand = snap['demand']

    sep  = '=' * 68
    sep2 = '-' * 68
    lines = [f'\n{sep}', f'  {snap["label"]}', sep]

    stype = snap['type']

    # ── Balance info ──
    if stype == 'balance':
        ts = snap['supply_orig'].sum()
        td = snap['demand_orig'].sum()
        lines.append(f'  Oferta total = {int(ts)}   Demanda total = {int(td)}')
        if snap['dummy_col']:
            lines.append(f'  => Problema NO balanceado (oferta > demanda)')
            lines.append(f'  => Se agrega destino ficticio con demanda = {int(ts-td)} y costo = 0')
        elif snap['dummy_row']:
            lines.append(f'  => Problema NO balanceado (demanda > oferta)')
            lines.append(f'  => Se agrega origen ficticio con oferta = {int(td-ts)} y costo = 0')
        else:
            lines.append('  => Problema BALANCEADO (oferta = demanda)')
        lines.append(sep + '\n')
        return '\n'.join(lines)

    # ── Table ──
    loop     = snap.get('loop')
    entering = snap.get('entering')
    lines.append(format_transport_table(
        alloc, costs, supply, demand, origins, destinations, loop, entering))
    lines.append('')

    real_c = sum(
        alloc[i, j] * costs[i, j]
        for i in range(m) for j in range(n)
        if alloc[i, j] > 1e-9 and costs[i, j] < LARGE / 2
    )
    lines.append(f'  Costo parcial = ${real_c:,.0f}')

    # ── VAM steps ──
    if stype == 'initial' and snap.get('steps'):
        lines.append(f'\n  {sep2}')
        lines.append('  Pasos de asignacion:')
        for k, st in enumerate(snap['steps'], 1):
            r, c = st['cell']
            lines.append(f'  Paso {k}: {origins[r]} -> {destinations[c]} = {int(st["qty"])} unidades')
        lines.append(sep2)

    # ── MODI iteration ──
    if stype == 'modi':
        u = snap['u']; v = snap['v']
        lines.append(f'\n  Variables duales:')
        u_str = '  u = [' + ', '.join(
            f'u{i+1}={u[i]:.0f}' if u[i] is not None else f'u{i+1}=?' for i in range(m)) + ']'
        v_str = '  v = [' + ', '.join(
            f'v{j+1}={v[j]:.0f}' if v[j] is not None else f'v{j+1}=?' for j in range(n)) + ']'
        lines += [u_str, v_str, '']

        d = snap.get('d', {})
        if d:
            lines.append('  Costos de oportunidad d_ij (celdas no basicas):')
            for (i, j), dval in sorted(d.items()):
                flag = '  <=== ENTRA' if (i, j) == entering else ''
                lines.append(f'    d({origins[i]},{destinations[j]}) = '
                              f'{costs[i,j]:.0f} - ({u[i]:.0f}) - ({v[j]:.0f}) = {dval:.2f}{flag}')

        if entering:
            oi, oj = entering
            lines.append(f'\n  Celda entrante: ({origins[oi]}, {destinations[oj]})'
                         f'  d = {snap["d"].get(entering, 0):.2f}')
        if loop:
            signs = ['+' if k % 2 == 0 else '-' for k in range(len(loop))]
            loop_str = ' -> '.join(
                f'({origins[r]},{destinations[c]}){s}'
                for (r, c), s in zip(loop, signs))
            lines.append(f'  Ciclo: {loop_str}')
            lines.append(f'  theta (θ) = {snap["theta"]:.0f}')

        if snap['status'] == 'optimal':
            lines.append(f'\n  >>> SOLUCION OPTIMA ALCANZADA  (Costo = ${real_c:,.0f}) <<<')

    lines.append(sep + '\n')
    return '\n'.join(lines)
