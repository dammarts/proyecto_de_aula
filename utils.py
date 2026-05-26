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

    # ── Data rows ──
    for i, rh in enumerate(row_headers):
        row_vals = tableau[i]
        arr = ' <' if i == pivot_row else '  '
        line = f'  {rh:>{BW}} |'
        for j, val in enumerate(row_vals):
            if i == pivot_row and j == pivot_col:
                cell = f'[{val:>6.3f}]'     # highlight pivot element
            else:
                cell = f' {val:>7.3f} '
            line += cell
        line += arr
        lines.append(line)

    lines.append(sep + '\n')
    return '\n'.join(lines)


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
