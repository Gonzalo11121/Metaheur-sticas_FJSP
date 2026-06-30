# =============================================================================
#  ts_vns.py
#  Algoritmo híbrido TS+VNS con agitación adaptativa para el FJSP.
#
#  La Búsqueda de Vecindad Variable (VNS) gobierna la estructura global:
#  en cada iteración agita la solución incumbente y delega la búsqueda local
#  a la Búsqueda Tabú (TS). La agitación es adaptativa: alterna entre perturbar
#  la dimensión de secuenciación y la de asignación de máquinas según donde
#  se detecta el estancamiento, explotando la estructura bicriteria del FJSP.
#
#  Vecindarios:
#    N1 — Intercambio  : dos posiciones de la secuencia se intercambian.
#    N2 — Reasignación : una operación crítica cambia de máquina elegible.
#    N3 — Inserción    : una operación se extrae y se reinserta en otra posición.
#
#  Referencias:
#    Glover, F. (1986). Computers & Operations Research, 13(5), 533–549.
#    Mladenović, N. & Hansen, P. (1997). Computers & Operations Research, 24(11).
#    Mastrolilli, M. & Gambardella, L.M. (2000). Journal of Scheduling, 3, 3–20.
# =============================================================================

import random
import time
from fjsp_core import FJSPInstance, Solution, solucion_inicial


# =============================================================================
#  VECINDARIOS
# =============================================================================

def _pos_criticas(sol: Solution) -> list:
    criticas = set(sol.ruta_critica())
    prox     = [0] * sol.instancia.n_jobs
    pos      = []
    for p, j in enumerate(sol.secuencia):
        if (j, prox[j]) in criticas:
            pos.append(p)
        prox[j] += 1
    return pos if pos else list(range(len(sol.secuencia)))


def vecino_N1(sol: Solution, rng) -> tuple:
    """Intercambio de dos posiciones en la secuencia (prioriza posiciones críticas)."""
    nuevo = sol.copiar()
    pos   = _pos_criticas(sol)
    i     = rng.choice(pos)
    k     = rng.randrange(len(nuevo.secuencia))
    if i == k:
        k = (k + 1) % len(nuevo.secuencia)
    nuevo.secuencia[i], nuevo.secuencia[k] = nuevo.secuencia[k], nuevo.secuencia[i]
    nuevo.decode()
    return nuevo, ("N1", min(i, k), max(i, k))


def vecino_N2(sol: Solution, rng) -> tuple:
    """Reasignación de una operación crítica a otra máquina elegible."""
    nuevo = sol.copiar()
    inst  = sol.instancia
    criticas = sol.ruta_critica()
    rng.shuffle(criticas)
    mov = None
    for (j, o) in criticas:
        alts = inst.operaciones[j][o]
        if len(alts) > 1:
            act  = nuevo.asignacion[(j, o)]
            opts = [x for x in range(len(alts)) if x != act]
            nuevo.asignacion[(j, o)] = rng.choice(opts)
            mov = ("N2", j, o, act)
            break
    nuevo.decode()
    return nuevo, mov


def vecino_N3(sol: Solution, rng) -> tuple:
    """Inserción: una operación se extrae de su posición y se reinserta en otra."""
    nuevo = sol.copiar()
    n     = len(nuevo.secuencia)
    i     = rng.randrange(n)
    elem  = nuevo.secuencia.pop(i)
    k     = rng.randrange(n)
    nuevo.secuencia.insert(k, elem)
    nuevo.decode()
    return nuevo, ("N3", i, k)


VECINDARIOS = [vecino_N1, vecino_N2, vecino_N3]


# =============================================================================
#  BÚSQUEDA TABÚ
# =============================================================================

def busqueda_tabu(sol: Solution, rng,
                  max_iter: int = 60,
                  tenencia: int = 10,
                  tam_vec: int  = 20) -> Solution:
    """
    Mejora localmente una solución mediante Búsqueda Tabú.
    En cada iteración se muestrea el vecindario combinado N1∪N2∪N3.
    Se selecciona el mejor candidato no tabú o que satisfaga el criterio
    de aspiración (supera la mejor solución global conocida).
    El movimiento ejecutado queda prohibido durante 'tenencia' iteraciones.
    """
    actual     = sol.copiar()
    mejor      = actual.copiar()
    lista_tabu = {}

    for it in range(max_iter):
        candidatos = []
        for _ in range(tam_vec):
            vec, mov = rng.choice(VECINDARIOS)(actual, rng)
            if mov is not None:
                candidatos.append((vec, mov))
        if not candidatos:
            break
        candidatos.sort(key=lambda c: c[0].makespan)
        elegido = None
        for vec, mov in candidatos:
            if lista_tabu.get(mov, 0) <= it or vec.makespan < mejor.makespan:
                elegido = (vec, mov)
                break
        if elegido is None:
            elegido = candidatos[0]
        actual, mov = elegido
        lista_tabu[mov] = it + tenencia
        if actual.makespan < mejor.makespan:
            mejor = actual.copiar()

    return mejor


# =============================================================================
#  AGITACIÓN ADAPTATIVA
# =============================================================================

def agitar(sol: Solution, k: int, modo: str, rng) -> Solution:
    """
    Perturba la solución incumbente para escapar de la cuenca del óptimo local.
    La intensidad k controla cuántos movimientos aleatorios se aplican.
    El modo alterna entre 'secuencia' y 'asignacion' de forma adaptativa:
    cuando una dimensión se estanca, se dirige la perturbación hacia la otra.
    """
    nuevo = sol.copiar()
    inst  = sol.instancia
    if modo == "secuencia":
        for _ in range(k):
            i, j = rng.sample(range(len(nuevo.secuencia)), 2)
            nuevo.secuencia[i], nuevo.secuencia[j] = nuevo.secuencia[j], nuevo.secuencia[i]
    else:
        ops_flex = [(j, o) for j in range(inst.n_jobs)
                    for o in range(inst.ops_de_trabajo(j))
                    if len(inst.operaciones[j][o]) > 1]
        if ops_flex:
            for _ in range(k):
                j, o = rng.choice(ops_flex)
                nuevo.asignacion[(j, o)] = rng.randrange(len(inst.operaciones[j][o]))
    nuevo.decode()
    return nuevo


# =============================================================================
#  ALGORITMO PRINCIPAL  TS+VNS
# =============================================================================

def ts_vns(inst: FJSPInstance,
           max_iter: int  = 40,
           k_max: int     = 4,
           tabu_iter: int = 60,
           tenencia: int  = 10,
           tiempo_limite  = None,
           semilla        = None,
           registrar_convergencia: bool = False) -> tuple:
    """
    Híbrido TS+VNS con agitación adaptativa para el FJSP.

    Flujo:
      1. Solución inicial (MCG + permutación aleatoria) refinada con TS.
      2. Bucle VNS:
         a. Agitar incumbente con intensidad k en el modo actual.
         b. Refinar con TS.
         c. Mejora → k=1, actualizar incumbente.
            Sin mejora → k+1. Si k > k_max → cambiar modo de agitación.

    Métricas registradas en la solución retornada:
      .iter_vns       — iteraciones del bucle VNS ejecutadas.
      .iter_tabu      — pasos de Búsqueda Tabú totales acumulados.
      .iter_mejor     — iteración VNS en que se halló el mejor makespan.
      .tiempo_mejor_s — tiempo transcurrido (s) al hallar el mejor makespan.
    """
    rng  = random.Random(semilla)
    t0   = time.time()

    mejor       = solucion_inicial(inst, semilla=semilla)
    mejor       = busqueda_tabu(mejor, rng, max_iter=tabu_iter, tenencia=tenencia)
    total_tabu  = tabu_iter
    historico   = [mejor.makespan]
    modo        = "secuencia"
    sin_mejora  = 0

    mejor.iter_vns      = 0
    mejor.iter_tabu     = total_tabu
    mejor.iter_mejor    = 0
    mejor.tiempo_mejor_s = time.time() - t0

    for it in range(max_iter):
        if tiempo_limite and (time.time() - t0) > tiempo_limite:
            break
        k           = 1
        mejoro      = False
        while k <= k_max:
            cand       = agitar(mejor, k, modo, rng)
            cand       = busqueda_tabu(cand, rng, max_iter=tabu_iter, tenencia=tenencia)
            total_tabu += tabu_iter
            if cand.makespan < mejor.makespan:
                mejor                = cand.copiar()
                mejor.iter_mejor     = it
                mejor.tiempo_mejor_s = time.time() - t0
                k                    = 1
                mejoro               = True
            else:
                k += 1
        if not mejoro:
            sin_mejora += 1
            modo = "asignacion" if modo == "secuencia" else "secuencia"
        else:
            sin_mejora = 0
        if registrar_convergencia:
            historico.append(mejor.makespan)

    mejor.iter_vns  = it + 1
    mejor.iter_tabu = total_tabu
    return mejor, historico


if __name__ == "__main__":
    import os
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instancias")
    for root, _, files in os.walk(base):
        for fn in files:
            if fn == "la01.txt" and os.path.basename(root) == "edata":
                inst = FJSPInstance(os.path.join(root, fn), "la01", "edata")
                print(inst)
                sol, hist = ts_vns(inst, max_iter=30, semilla=1,
                                   tiempo_limite=20, registrar_convergencia=True)
                print(f"  Makespan final    : {sol.makespan}")
                print(f"  Iteraciones VNS   : {sol.iter_vns}")
                print(f"  Iteraciones Tabú  : {sol.iter_tabu}")
                print(f"  Iter. del mejor   : {sol.iter_mejor}")
                print(f"  Tiempo al mejor   : {sol.tiempo_mejor_s:.2f} s")
                print(f"  Convergencia      : {hist[0]} → {hist[-1]}")
