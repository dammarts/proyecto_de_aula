# ──────────────────────────────────────────────────────────────────────────────
#  CONFIGURACIÓN DEL PRESENTADOR
#  Editar estos datos con tu información personal antes de presentar el proyecto
# ──────────────────────────────────────────────────────────────────────────────

CONFIG = {
    'nombre_estudiante': 'Daniel Montoya',
    'nombre_companera':  'Valeria Caro',
    'universidad':       'Universidad Pascual Bravo',
    'facultad':          'Facultad de Ingeniería',
    'materia':           'Investigación de Operaciones',
    'profesor':          'Felipe Duque',
    'semestre':          '2026-I',
}

# ──────────────────────────────────────────────────────────────────────────────
#  EJEMPLO PROPIO  —  AgroMix S.A.S
#  Nivel: ALTO  (4 variables de decisión, 5 restricciones mixtas ≤/≥/=)
#  Método Big-M: variables de holgura s1–s2, exceso e1–e2, artificiales a1–a3
# ──────────────────────────────────────────────────────────────────────────────

PROBLEMA = {
    'titulo': 'AgroMix S.A.S — Optimizacion de Mezcla de Fertilizantes',
    'empresa': 'AgroMix S.A.S',
    'nivel': 'Alto',
    'nivel_descripcion': (
        '4 variables (x1-x4), 5 restricciones mixtas (2x<=, 2x>=, 1x=). '
        'Big-M genera s1-s2, e1-e2, a1-a3. Tableau 6x12. '
        'Solucion: x1=160, x2=0, x3=40, x4=0, Z=$1520.'
    ),
    'descripcion': (
        'AgroMix S.A.S produce dos grados de fertilizante — Premium (P) y '
        'Estandar (E) — mezclando dos nutrientes: Nitrogeno (N) y Fosforo (F). '
        'La planta dispone de 200 kg de N y 150 kg de F por dia. Contratos '
        'minimos obligan a producir al menos 50 kg de Premium y 40 kg de '
        'Estandar. La capacidad total de la mezcladora es exactamente 200 kg/dia '
        '(restriccion de igualdad). Se busca MAXIMIZAR la ganancia neta diaria '
        'asignando cada nutriente al grado de fertilizante mas rentable.'
    ),
    'variables': [
        'x1 (N -> Premium,  $8/kg)',
        'x2 (F -> Premium,  $5/kg)',
        'x3 (N -> Estandar, $6/kg)',
        'x4 (F -> Estandar, $4/kg)',
    ],
    'restricciones_nombres': [
        'Nitrogeno disponible (kg)',
        'Fosforo disponible (kg)',
        'Minimo Premium (kg)',
        'Minimo Estandar (kg)',
        'Capacidad total planta (kg)',
    ],
    # Modelo matemático
    'c':  [8, 5, 6, 4],
    'A':  [
        [1, 0, 1, 0],   # Nitrogeno: x1 + x3 <= 200
        [0, 1, 0, 1],   # Fosforo:   x2 + x4 <= 150
        [1, 1, 0, 0],   # Premium:   x1 + x2 >= 50
        [0, 0, 1, 1],   # Estandar:  x3 + x4 >= 40
        [1, 1, 1, 1],   # Planta:    x1+x2+x3+x4 = 200
    ],
    'b':  [200, 150, 50, 40, 200],
    'tipo': 'max',
    'constraint_types': ['<=', '<=', '>=', '>=', '='],
    'ganancias': [8, 5, 6, 4],
    'modelo_texto': (
        'MAX  Z = 8x1 + 5x2 + 6x3 + 4x4\n'
        '\n'
        's.a.\n'
        '   x1       + x3            <=  200   (Nitrogeno disponible)\n'
        '        x2       + x4       <=  150   (Fosforo disponible)\n'
        '   x1 + x2                  >=   50   (Minimo Premium)\n'
        '             x3 + x4        >=   40   (Minimo Estandar)\n'
        '   x1 + x2 + x3 + x4        =  200   (Capacidad planta)\n'
        '\n'
        '   x1, x2, x3, x4 >= 0'
    ),
    # Solucion esperada: x1=160, x2=0, x3=40, x4=0, Z=1520
    'solucion_optima': {
        'x': [160.0, 0.0, 40.0, 0.0],
        'Z': 1520.0,
    },
}
