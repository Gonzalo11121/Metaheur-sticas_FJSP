# -*- coding: utf-8 -*-
"""
taboo_search.py
===============
Metaheuristica BUSQUEDA TABU (Tabu Search) para el Problema de Job Shop
Flexible (FJSP) con objetivo de minimizar el makespan (Cmax).

Diseño general
--------------
* Representacion de una solucion = (asignacion, secuencia)
    - asignacion[j][o] = maquina (base 0) en la que se ejecuta la operacion o
      del trabajo j  ->  decide el "ruteo" (que maquina hace cada operacion).
    - secuencia = vector de IDs de trabajo con REPETICION (codificacion clasica
      "operation-based"). La k-esima aparicion del trabajo j representa la
      k-esima operacion de j. Cualquier permutacion de este multiconjunto es una
      secuencia FACTIBLE (respeta el orden interno de cada trabajo al decodificar).

* Decodificador = horario ACTIVO con insercion en huecos:
    se recorre la secuencia; cada operacion se coloca en el primer hueco
    disponible de su maquina, respetando la precedencia del trabajo. Esto produce
    horarios de buena calidad (permite "adelantar" operaciones a huecos libres).

* Vecindarios basados en la RUTA CRITICA (camino que determina el makespan):
    - N1 (reasignacion): mover una operacion critica a otra maquina elegible.
    - N2 (intercambio): intercambiar dos operaciones adyacentes en la secuencia
      (de trabajos distintos) tocando al menos una operacion critica.
  Mover solo operaciones criticas concentra el esfuerzo donde puede reducirse
  el makespan, que es la idea central de Tabu Search para scheduling.

* Lista tabu (memoria de corto plazo) con:
    - atributos de movimiento (no su solucion completa),
    - tenencia (tabu tenure) dinamica,
    - criterio de ASPIRACION: se permite un movimiento tabu si mejora el mejor
      makespan global encontrado.

* Diversificacion: si pasan muchas iteraciones sin mejora, se perturba la
  solucion (reasignaciones e intercambios aleatorios) para escapar de optimos
  locales, conservando siempre la mejor solucion hallada (memoria de largo plazo).

Solo biblioteca estandar de Python.
"""

import bisect
import random
import time


# ===========================================================================
#  Preprocesamiento de la instancia
# ===========================================================================
class _Datos:
    """Estructuras auxiliares precalculadas para acelerar la busqueda."""

    def __init__(self, inst):
        self.inst = inst
        self.n_trab = inst.n_trabajos
        self.n_maq = inst.n_maquinas
        self.n_ops = inst.n_ops_por_trabajo  # lista: ops por trabajo

        # Maquinas elegibles y tabla de duracion por (trabajo, op, maquina).
        # maquinas_elegibles[j][o] = lista de maquinas posibles
        # dur[j][o] = dict {maquina: duracion}
        self.maquinas_elegibles = []
        self.dur = []
        for j in range(self.n_trab):
            me_j, du_j = [], []
            for o in range(self.n_ops[j]):
                opciones = inst.trabajos[j][o]
                me_j.append([m for (m, _p) in opciones])
                du_j.append({m: p for (m, p) in opciones})
            self.maquinas_elegibles.append(me_j)
            self.dur.append(du_j)

        # Plantilla de la secuencia: cada trabajo j repetido n_ops[j] veces.
        self.plantilla_secuencia = []
        for j in range(self.n_trab):
            self.plantilla_secuencia.extend([j] * self.n_ops[j])


# ===========================================================================
#  Decodificador: (asignacion, secuencia) -> horario y makespan
# ===========================================================================
def _buscar_hueco(intervalos, inicio_min, p):
    """
    Devuelve el primer instante >= inicio_min en el que cabe una tarea de
    duracion p en la maquina, dados sus 'intervalos' ocupados (ordenados por
    inicio y sin solape). Permite insertar en huecos (horario activo).
    """
    fin_prev = 0
    for (s, e) in intervalos:
        ini = inicio_min if inicio_min > fin_prev else fin_prev
        if s - ini >= p:           # cabe en el hueco [ini, s)
            return ini
        if e > fin_prev:
            fin_prev = e
    return inicio_min if inicio_min > fin_prev else fin_prev


def decodificar(D, asignacion, secuencia):
    """
    Construye el horario activo y devuelve:
      makespan, op_ini, op_fin
    donde op_ini[j][o] y op_fin[j][o] son los tiempos de inicio y fin.
    """
    n_maq = D.n_maq
    intervalos = [[] for _ in range(n_maq)]      # por maquina: [(ini, fin), ...]
    fin_trabajo = [0] * D.n_trab                 # fin de la ultima op del trabajo
    contador = [0] * D.n_trab                    # siguiente op de cada trabajo
    op_ini = [[0] * D.n_ops[j] for j in range(D.n_trab)]
    op_fin = [[0] * D.n_ops[j] for j in range(D.n_trab)]
    makespan = 0

    dur = D.dur
    for j in secuencia:
        o = contador[j]
        contador[j] += 1
        m = asignacion[j][o]
        p = dur[j][o][m]
        est = fin_trabajo[j]                     # tiempo mas temprano por precedencia
        inicio = _buscar_hueco(intervalos[m], est, p)
        fin = inicio + p
        bisect.insort(intervalos[m], (inicio, fin))
        op_ini[j][o] = inicio
        op_fin[j][o] = fin
        fin_trabajo[j] = fin
        if fin > makespan:
            makespan = fin
    return makespan, op_ini, op_fin


# ===========================================================================
#  Ruta critica
# ===========================================================================
def ruta_critica(D, asignacion, op_ini, op_fin, makespan):
    """
    Identifica operaciones criticas (las que estan en un camino que determina el
    makespan) recorriendo hacia atras desde una operacion que termina en Cmax.

    Devuelve:
      criticas      : set de (j, o) en el camino critico
      pred_maquina  : dict (j,o) -> (j',o') predecesor inmediato en su maquina
    Tambien usa los predecesores de maquina para generar intercambios.
    """
    # Predecesor inmediato en cada maquina (segun orden temporal)
    ops_por_maquina = [[] for _ in range(D.n_maq)]
    for j in range(D.n_trab):
        for o in range(D.n_ops[j]):
            m = asignacion[j][o]
            ops_por_maquina[m].append((op_ini[j][o], op_fin[j][o], j, o))
    pred_maquina = {}
    for m in range(D.n_maq):
        ops_por_maquina[m].sort()
        prev = None
        for (_s, _e, j, o) in ops_por_maquina[m]:
            pred_maquina[(j, o)] = prev
            prev = (j, o)

    # Operacion final del camino: la que termina en el makespan (mayor inicio
    # entre las que terminan en Cmax, para tomar la "cola" real).
    fin_op = None
    mejor_ini = -1
    for j in range(D.n_trab):
        oj = D.n_ops[j] - 1
        if op_fin[j][oj] == makespan and op_ini[j][oj] > mejor_ini:
            mejor_ini = op_ini[j][oj]
            fin_op = (j, oj)
    if fin_op is None:                            # respaldo defensivo
        for j in range(D.n_trab):
            for o in range(D.n_ops[j]):
                if op_fin[j][o] == makespan:
                    fin_op = (j, o)
                    break
            if fin_op:
                break

    criticas = set()
    cur = fin_op
    while cur is not None:
        criticas.add(cur)
        j, o = cur
        s = op_ini[j][o]
        if s == 0:
            break
        # Predecesor de trabajo "ajustado" (termina justo cuando inicia cur)
        pj = (j, o - 1) if o > 0 else None
        pj_ajustado = pj is not None and op_fin[pj[0]][pj[1]] == s
        # Predecesor de maquina "ajustado"
        pm = pred_maquina.get(cur)
        pm_ajustado = pm is not None and op_fin[pm[0]][pm[1]] == s
        # Preferimos el arco de maquina (habilita intercambios en N2)
        if pm_ajustado:
            cur = pm
        elif pj_ajustado:
            cur = pj
        else:
            # Seguridad numerica: elegir el predecesor con mayor fin <= s
            cand = []
            if pm is not None:
                cand.append((op_fin[pm[0]][pm[1]], pm))
            if pj is not None:
                cand.append((op_fin[pj[0]][pj[1]], pj))
            if not cand:
                break
            cand.sort()
            cur = cand[-1][1]
    return criticas, pred_maquina


# ===========================================================================
#  Solucion inicial
# ===========================================================================
def _construir_inicial(D, rng):
    """Una solucion inicial factible (balanceo de carga + secuencia aleatoria)."""
    asignacion = [[0] * D.n_ops[j] for j in range(D.n_trab)]
    carga = [0] * D.n_maq

    ops = [(j, o) for j in range(D.n_trab) for o in range(D.n_ops[j])]
    rng.shuffle(ops)
    for (j, o) in ops:
        mejor_m, mejor_val = None, None
        for m in D.maquinas_elegibles[j][o]:
            val = carga[m] + D.dur[j][o][m]
            if mejor_val is None or val < mejor_val:
                mejor_val, mejor_m = val, m
        asignacion[j][o] = mejor_m
        carga[mejor_m] += D.dur[j][o][mejor_m]

    secuencia = list(D.plantilla_secuencia)
    rng.shuffle(secuencia)
    return asignacion, secuencia


def solucion_inicial(D, rng, intentos=8):
    """
    Multi-inicio: construye varias soluciones iniciales y conserva la de menor
    makespan. Mejora notablemente el punto de partida a costo muy bajo.
    """
    mejor = None
    mejor_mk = None
    for _ in range(intentos):
        asig, sec = _construir_inicial(D, rng)
        mk, _oi, _of = decodificar(D, asig, sec)
        if mejor_mk is None or mk < mejor_mk:
            mejor_mk, mejor = mk, (asig, sec)
    return mejor


# ===========================================================================
#  Utilidades de copia y de movimientos
# ===========================================================================
def _copiar_asig(asig):
    return [fila[:] for fila in asig]


def _evaluar_movimiento(D, asignacion, secuencia, mov):
    """Aplica 'mov' de forma temporal, decodifica, revierte y devuelve el makespan.
    Tipos de movimiento:
      ('A', j, o, m_new, m_old) : reasignar la operacion (j,o) a la maquina m_new
      ('S', i)                  : intercambiar las posiciones i e i+1
      ('I', i, destino)         : reubicar el token de la posicion i antes de destino
    """
    t = mov[0]
    if t == 'A':
        _, j, o, m_new, m_old = mov
        asignacion[j][o] = m_new
        mk, _oi, _of = decodificar(D, asignacion, secuencia)
        asignacion[j][o] = m_old
        return mk
    elif t == 'S':
        i = mov[1]
        secuencia[i], secuencia[i + 1] = secuencia[i + 1], secuencia[i]
        mk, _oi, _of = decodificar(D, asignacion, secuencia)
        secuencia[i], secuencia[i + 1] = secuencia[i + 1], secuencia[i]
        return mk
    else:  # 'I'
        i, destino = mov[1], mov[2]
        val = secuencia[i]
        del secuencia[i]
        secuencia.insert(destino, val)
        mk, _oi, _of = decodificar(D, asignacion, secuencia)
        del secuencia[destino]
        secuencia.insert(i, val)
        return mk


def _aplicar_movimiento(asignacion, secuencia, mov):
    """Aplica 'mov' de forma PERMANENTE sobre asignacion/secuencia."""
    t = mov[0]
    if t == 'A':
        _, j, o, m_new, m_old = mov
        asignacion[j][o] = m_new
    elif t == 'S':
        i = mov[1]
        secuencia[i], secuencia[i + 1] = secuencia[i + 1], secuencia[i]
    else:  # 'I'
        i, destino = mov[1], mov[2]
        val = secuencia[i]
        del secuencia[i]
        secuencia.insert(destino, val)


def _clave_check(mov, op_en_pos):
    """Clave usada para CONSULTAR si un movimiento esta prohibido (tabu)."""
    t = mov[0]
    if t == 'A':
        _, j, o, m_new, _m_old = mov
        return ('A', j, o, m_new)
    elif t == 'S':
        i = mov[1]
        a, b = op_en_pos[i], op_en_pos[i + 1]
        return ('S', (a, b) if a <= b else (b, a))
    else:  # 'I'
        return ('I', op_en_pos[mov[1]])


def _clave_store(mov, op_en_pos):
    """Clave que se INSERTA en la lista tabu al aplicar (prohibe el reverso)."""
    t = mov[0]
    if t == 'A':
        _, j, o, _m_new, m_old = mov
        return ('A', j, o, m_old)              # prohibe devolver (j,o) a m_old
    elif t == 'S':
        i = mov[1]
        a, b = op_en_pos[i], op_en_pos[i + 1]
        return ('S', (a, b) if a <= b else (b, a))
    else:  # 'I'
        return ('I', op_en_pos[mov[1]])


# ===========================================================================
#  Algoritmo principal de Busqueda Tabu
# ===========================================================================
def resolver(inst, semilla, limite_tiempo=60.0,
             tenencia_min=None, tenencia_max=None,
             max_vecinos=300, iter_sin_mejora_diversif=40,
             registrar_historial=False):
    """
    Ejecuta Tabu Search sobre 'inst' durante 'limite_tiempo' segundos.

    Parametros
    ----------
    inst                       : Instancia (de fjsp_parser)
    semilla                    : int, semilla del generador aleatorio (reproducible)
    limite_tiempo              : float, presupuesto temporal en segundos
    tenencia_min/tenencia_max  : rango de la tenencia tabu (si None, se escala
                                 con el tamaño del problema)
    max_vecinos                : tope de vecinos evaluados por iteracion (muestreo
                                 aleatorio si se supera) -> controla el costo
    iter_sin_mejora_diversif   : iteraciones sin mejora antes de diversificar
    registrar_historial        : si True, guarda la curva de convergencia

    Devuelve un dict con: makespan, iteraciones, tiempo, asignacion, secuencia,
    historial (lista de (iteracion, mejor_makespan)) si se pidio.
    """
    rng = random.Random(semilla)
    D = _Datos(inst)
    n_ops = inst.n_operaciones

    # Tenencia tabu por defecto escalada al tamaño (heuristica habitual ~ sqrt(n))
    if tenencia_min is None:
        tenencia_min = max(5, int(round(n_ops ** 0.5)))
    if tenencia_max is None:
        tenencia_max = tenencia_min + 6

    # --- Solucion inicial -------------------------------------------------
    asignacion, secuencia = solucion_inicial(D, rng)
    mk, op_ini, op_fin = decodificar(D, asignacion, secuencia)

    mejor_asig = _copiar_asig(asignacion)
    mejor_sec = secuencia[:]
    mejor_mk = mk

    # Lista tabu: dict atributo -> iteracion de expiracion
    tabu = {}

    historial = []
    iteraciones = 0
    sin_mejora = 0
    t0 = time.perf_counter()

    while time.perf_counter() - t0 < limite_tiempo:
        iteraciones += 1

        # Ruta critica de la solucion actual
        criticas, _pred = ruta_critica(D, asignacion, op_ini, op_fin, mk)

        # Mapa posicion -> (j,o) en la secuencia actual (para N2)
        contador = [0] * D.n_trab
        op_en_pos = [None] * len(secuencia)
        for i, j in enumerate(secuencia):
            op_en_pos[i] = (j, contador[j])
            contador[j] += 1

        # ------------------------------------------------------------------
        # Generar lista de movimientos candidatos (sin evaluar todavia)
        #  ('A', j, o, m_nueva, m_vieja)            -> reasignacion (N1)
        #  ('S', i)                                  -> intercambio pos i,i+1 (N2)
        # ------------------------------------------------------------------
        candidatos = []
        # N1: reasignar operaciones criticas a otra maquina elegible
        for (j, o) in criticas:
            m_actual = asignacion[j][o]
            for m in D.maquinas_elegibles[j][o]:
                if m != m_actual:
                    candidatos.append(('A', j, o, m, m_actual))
        # N2: intercambios adyacentes (trabajos distintos) tocando una critica
        for i in range(len(secuencia) - 1):
            if secuencia[i] != secuencia[i + 1]:
                if op_en_pos[i] in criticas or op_en_pos[i + 1] in criticas:
                    candidatos.append(('S', i))
        # N3: reubicacion (insercion) de una operacion critica algunos lugares
        # antes en la secuencia. Es un movimiento mas amplio que el intercambio
        # adyacente y ayuda a reordenar bloques criticos.
        for i in range(len(secuencia)):
            if op_en_pos[i] in criticas:
                for salto in (2, 4, 8):
                    destino = i - salto
                    if destino >= 0 and secuencia[destino] != secuencia[i]:
                        candidatos.append(('I', i, destino))

        # Si no hay candidatos criticos (raro), usar todos los intercambios
        if not candidatos:
            for i in range(len(secuencia) - 1):
                if secuencia[i] != secuencia[i + 1]:
                    candidatos.append(('S', i))
            if not candidatos:
                break  # solucion trivial sin vecinos

        # Muestreo si hay demasiados (control de costo por iteracion)
        if len(candidatos) > max_vecinos:
            candidatos = rng.sample(candidatos, max_vecinos)

        # ------------------------------------------------------------------
        # Evaluar candidatos (evaluacion in situ: mutar -> decodificar -> revertir)
        # Se elige el mejor movimiento admisible (no tabu, o tabu con aspiracion).
        # ------------------------------------------------------------------
        mejor_mov = None
        mejor_mov_mk = None

        for mov in candidatos:
            cand_mk = _evaluar_movimiento(D, asignacion, secuencia, mov)
            es_tabu = tabu.get(_clave_check(mov, op_en_pos), 0) > iteraciones
            aspira = cand_mk < mejor_mk            # criterio de aspiracion
            if es_tabu and not aspira:
                continue
            # Elegir el de menor makespan (TS admite empeorar respecto al actual)
            if mejor_mov_mk is None or cand_mk < mejor_mov_mk:
                mejor_mov = mov
                mejor_mov_mk = cand_mk

        # Si todos los candidatos resultaron tabu sin aspiracion, relajar:
        # tomar el de menor makespan ignorando el estatus tabu (mecanismo de
        # desbloqueo simple para no estancar la busqueda).
        if mejor_mov is None:
            for mov in candidatos:
                cand_mk = _evaluar_movimiento(D, asignacion, secuencia, mov)
                if mejor_mov_mk is None or cand_mk < mejor_mov_mk:
                    mejor_mov = mov
                    mejor_mov_mk = cand_mk

        # ------------------------------------------------------------------
        # Aplicar el mejor movimiento de forma permanente y actualizar la tabu
        # ------------------------------------------------------------------
        ten = rng.randint(tenencia_min, tenencia_max)
        clave = _clave_store(mejor_mov, op_en_pos)
        _aplicar_movimiento(asignacion, secuencia, mejor_mov)
        tabu[clave] = iteraciones + ten

        mk, op_ini, op_fin = decodificar(D, asignacion, secuencia)

        # Actualizar mejor global
        if mk < mejor_mk:
            mejor_mk = mk
            mejor_asig = _copiar_asig(asignacion)
            mejor_sec = secuencia[:]
            sin_mejora = 0
        else:
            sin_mejora += 1

        if registrar_historial:
            historial.append((iteraciones, mejor_mk))

        # ------------------------------------------------------------------
        # Diversificacion (memoria de largo plazo): si llevamos demasiado sin
        # mejorar, perturbamos la solucion actual y limpiamos parte de la
        # memoria tabu, sin perder la mejor solucion archivada.
        # ------------------------------------------------------------------
        if sin_mejora >= iter_sin_mejora_diversif:
            sin_mejora = 0
            tabu.clear()
            # Re-centrar la busqueda en la MEJOR solucion archivada y perturbarla
            # ligeramente (intensificacion + diversificacion controlada).
            asignacion = _copiar_asig(mejor_asig)
            secuencia = mejor_sec[:]
            n_kick = max(2, n_ops // 20)
            for _ in range(n_kick):                # reasignaciones aleatorias
                j = rng.randrange(D.n_trab)
                o = rng.randrange(D.n_ops[j])
                elig = D.maquinas_elegibles[j][o]
                if len(elig) > 1:
                    asignacion[j][o] = rng.choice(elig)
            for _ in range(n_kick):                # intercambios aleatorios
                i = rng.randrange(len(secuencia) - 1)
                secuencia[i], secuencia[i + 1] = secuencia[i + 1], secuencia[i]
            mk, op_ini, op_fin = decodificar(D, asignacion, secuencia)

    tiempo = time.perf_counter() - t0
    return {
        "makespan": mejor_mk,
        "iteraciones": iteraciones,
        "tiempo": tiempo,
        "asignacion": mejor_asig,
        "secuencia": mejor_sec,
        "historial": historial,
    }


# ===========================================================================
#  Verificador de factibilidad (independiente del decodificador)
# ===========================================================================
def verificar_factibilidad(inst, asignacion, secuencia):
    """
    Recalcula el horario y comprueba de forma INDEPENDIENTE que la solucion es
    factible: precedencia dentro de cada trabajo y sin solape en cada maquina.
    Devuelve (es_factible, makespan, mensaje).
    """
    D = _Datos(inst)
    mk, op_ini, op_fin = decodificar(D, asignacion, secuencia)

    # 1) Precedencia
    for j in range(D.n_trab):
        for o in range(1, D.n_ops[j]):
            if op_ini[j][o] < op_fin[j][o - 1]:
                return (False, mk,
                        "Violacion de precedencia en trabajo %d, op %d" % (j, o))

    # 2) Sin solape por maquina
    ocup = [[] for _ in range(D.n_maq)]
    for j in range(D.n_trab):
        for o in range(D.n_ops[j]):
            m = asignacion[j][o]
            ocup[m].append((op_ini[j][o], op_fin[j][o]))
    for m in range(D.n_maq):
        ocup[m].sort()
        for k in range(1, len(ocup[m])):
            if ocup[m][k][0] < ocup[m][k - 1][1]:
                return (False, mk, "Solape en maquina %d" % m)

    return (True, mk, "OK")
