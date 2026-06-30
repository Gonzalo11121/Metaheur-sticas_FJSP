"""
memetico.py
===========
Algoritmo Memetico (Algoritmo Genetico + Busqueda Local) para el
Flexible Job Shop Scheduling Problem (FJSP), objetivo: minimizar makespan.
"""

import random
import time


# DECODIFICADOR

def decodificar(inst, os_vec, ms_vec):
    """Convierte un cromosoma (OS, MS) en un cronograma y su makespan."""
    n_maq = inst.n_maquinas

    # Intervalos ocupados por maquina, como listas ordenadas de (inicio, fin).
    libres_maq = [[] for _ in range(n_maq)]

    fin_trabajo = [0] * inst.n_trabajos   # fin de la ultima op programada del job
    contador_op = [0] * inst.n_trabajos   # cuantas ops del job ya se programaron
    detalle = []
    makespan = 0

    for job in os_vec:
        o = contador_op[job]
        idx = inst.offset[job] + o            # indice canonico de la operacion
        alt = ms_vec[idx]                     # alternativa elegida
        maquina, dur = inst.trabajos[job][o][alt]

        liberacion = fin_trabajo[job]         # no puede empezar antes que termine
                                              # la operacion previa del trabajo
        inicio = _buscar_inicio(libres_maq[maquina], liberacion, dur)
        fin = inicio + dur

        _insertar(libres_maq[maquina], inicio, fin)
        detalle.append((job, o, maquina, inicio, fin))

        fin_trabajo[job] = fin
        contador_op[job] += 1
        if fin > makespan:
            makespan = fin

    return makespan, fin_trabajo, detalle


def _buscar_inicio(intervalos, liberacion, dur):
    """Primer instante >= liberacion donde cabe una tarea de longitud dur
    sin solaparse con los intervalos ya ocupados (lista ordenada por inicio)."""
    inicio = liberacion
    for (s, e) in intervalos:
        if inicio + dur <= s:        # cabe en el hueco antes de este intervalo
            return inicio
        if inicio < e:               # se solapa: empujar despues del intervalo
            inicio = e
    return inicio


def _insertar(intervalos, s, e):
    """Inserta (s, e) manteniendo la lista ordenada por inicio."""
    lo, hi = 0, len(intervalos)
    while lo < hi:                    # busqueda binaria de la posicion
        mid = (lo + hi) // 2
        if intervalos[mid][0] < s:
            lo = mid + 1
        else:
            hi = mid
    intervalos.insert(lo, (s, e))


# INICIALIZACION DE INDIVIDUOS

def _os_aleatorio(inst, rng):
    """OS aleatorio: multiconjunto de ids de trabajo barajado."""
    seq = []
    for j in range(inst.n_trabajos):
        seq.extend([j] * inst.n_ops[j])
    rng.shuffle(seq)
    return seq


def _os_mwr(inst, rng, aleatoriedad=0.2):
    # Trabajo restante inicial por trabajo (suma de tiempos minimos por op).
    restante = []
    for j in range(inst.n_trabajos):
        s = 0
        for o in range(inst.n_ops[j]):
            s += min(t for (_m, t) in inst.trabajos[j][o])
        restante.append(s)

    siguiente = [0] * inst.n_trabajos          # proxima op pendiente por trabajo
    pendientes = sum(inst.n_ops)
    seq = []
    while pendientes > 0:
        # Trabajos con operaciones aun por programar.
        listos = [j for j in range(inst.n_trabajos)
                  if siguiente[j] < inst.n_ops[j]]
        if rng.random() < aleatoriedad:
            j = rng.choice(listos)
        else:
            j = max(listos, key=lambda x: restante[x])
        o = siguiente[j]
        seq.append(j)
        restante[j] -= min(t for (_m, t) in inst.trabajos[j][o])
        siguiente[j] += 1
        pendientes -= 1
    return seq


def _ms_aleatorio(inst, rng):
    ms = []
    for j in range(inst.n_trabajos):
        for o in range(inst.n_ops[j]):
            ms.append(rng.randrange(len(inst.trabajos[j][o])))
    return ms


def _ms_spt(inst):
    ms = []
    for j in range(inst.n_trabajos):
        for o in range(inst.n_ops[j]):
            alts = inst.trabajos[j][o]
            mejor = min(range(len(alts)), key=lambda a: alts[a][1])
            ms.append(mejor)
    return ms


def _ms_balanceo_carga(inst, rng):
    carga = [0] * inst.n_maquinas
    ms = [0] * inst.total_ops
    # Recorremos en orden aleatorio para diversificar entre individuos.
    orden = list(range(inst.n_trabajos))
    rng.shuffle(orden)
    for j in orden:
        for o in range(inst.n_ops[j]):
            alts = inst.trabajos[j][o]
            mejor_a, mejor_val = 0, None
            for a, (m, t) in enumerate(alts):
                val = carga[m] + t
                if mejor_val is None or val < mejor_val:
                    mejor_val, mejor_a = val, a
            m_sel, t_sel = alts[mejor_a]
            carga[m_sel] += t_sel
            ms[inst.offset[j] + o] = mejor_a
    return ms


def crear_poblacion(inst, tam, rng):
    """Genera la poblacion inicial mezclando individuos aleatorios y
    heuristicos (SPT y balanceo de carga) para sembrar buena diversidad."""
    poblacion = []
    for k in range(tam):
        # OS: ~25% por regla MWR (clave en edata), resto aleatorio.
        if rng.random() < 0.25:
            os_vec = _os_mwr(inst, rng)
        else:
            os_vec = _os_aleatorio(inst, rng)
        # MS: mezcla de SPT, balanceo de carga y aleatorio.
        r = rng.random()
        if r < 0.20:
            ms_vec = _ms_spt(inst)              # ~20% SPT
        elif r < 0.50:
            ms_vec = _ms_balanceo_carga(inst, rng)  # ~30% balanceo
        else:
            ms_vec = _ms_aleatorio(inst, rng)   # ~50% aleatorio
        poblacion.append([os_vec, ms_vec])
    return poblacion

# OPERADORES GENETICOS

def cruce_pox(os1, os2, inst, rng):
    trabajos = list(range(inst.n_trabajos))
    rng.shuffle(trabajos)
    corte = rng.randint(1, inst.n_trabajos - 1) if inst.n_trabajos > 1 else 1
    j1 = set(trabajos[:corte])

    hijo = [None] * len(os1)
    # 1) Copiar de os1 las posiciones cuyos trabajos pertenecen a J1.
    for i, job in enumerate(os1):
        if job in j1:
            hijo[i] = job
    # 2) Rellenar los huecos con la subsecuencia de os2 (trabajos de J2).
    relleno = [job for job in os2 if job not in j1]
    it = iter(relleno)
    for i in range(len(hijo)):
        if hijo[i] is None:
            hijo[i] = next(it)
    return hijo


def cruce_uniforme_ms(ms1, ms2, rng):
    """Cruce uniforme para la parte MS: cada gen se hereda de un padre al azar."""
    return [ms1[i] if rng.random() < 0.5 else ms2[i] for i in range(len(ms1))]


def mutar_os(os_vec, rng):
    """Mutacion OS por intercambio de dos posiciones (in place sobre copia)."""
    nuevo = os_vec[:]
    if len(nuevo) >= 2:
        i, k = rng.sample(range(len(nuevo)), 2)
        nuevo[i], nuevo[k] = nuevo[k], nuevo[i]
    return nuevo


def mutar_ms(ms_vec, inst, rng, prob_gen=0.10):
    """Mutacion MS: con probabilidad prob_gen, reasigna cada operacion a otra
    maquina elegible elegida al azar."""
    nuevo = ms_vec[:]
    for j in range(inst.n_trabajos):
        for o in range(inst.n_ops[j]):
            n_alt = len(inst.trabajos[j][o])
            if n_alt > 1 and rng.random() < prob_gen:
                nuevo[inst.offset[j] + o] = rng.randrange(n_alt)
    return nuevo

# BUSQUEDA LOCAL (componente memetico) basada en RUTA CRITICA

def _ruta_critica(inst, detalle, makespan):
    EPS = 1e-9
    info = {}        # (job,o) -> (maquina, inicio, fin)
    pos_en_os = {}   # (job,o) -> posicion en el orden de programacion
    por_maquina = {}
    for i, (job, o, m, s, e) in enumerate(detalle):
        info[(job, o)] = (m, s, e)
        pos_en_os[(job, o)] = i
        por_maquina.setdefault(m, []).append((s, job, o))

    # Predecesor en cada maquina (operacion inmediatamente anterior por inicio).
    maq_pred = {}
    for m, lst in por_maquina.items():
        lst.sort()
        anterior = None
        for (s, job, o) in lst:
            maq_pred[(job, o)] = anterior
            anterior = (job, o)

    # Traza hacia atras desde las operaciones que terminan en el makespan.
    criticos = set()
    pila = [(job, o) for (job, o, m, s, e) in detalle
            if abs(e - makespan) < EPS]
    while pila:
        nodo = pila.pop()
        if nodo in criticos:
            continue
        criticos.add(nodo)
        job, o = nodo
        m, s, e = info[nodo]
        if s <= EPS:
            continue
        # Arco de precedencia de trabajo (operacion previa del mismo trabajo).
        if o > 0:
            pj = (job, o - 1)
            if abs(info[pj][2] - s) < EPS:
                pila.append(pj)
        # Arco de secuencia de maquina (op previa en la misma maquina).
        mp = maq_pred.get(nodo)
        if mp is not None and abs(info[mp][2] - s) < EPS:
            pila.append(mp)
    return criticos, maq_pred, pos_en_os


def busqueda_local(inst, individuo, rng, max_pruebas):
    os_vec, ms_vec = individuo
    mk, _, detalle = decodificar(inst, os_vec, ms_vec)

    for _ in range(max_pruebas):
        criticos, maq_pred, pos_en_os = _ruta_critica(inst, detalle, mk)
        mejoro = False

        # Vecindario 1: swaps de arcos de maquina criticos 
        # Candidatos: pares (predecesor_maquina, operacion) ambos criticos.
        candidatos = []
        for nodo in criticos:
            mp = maq_pred.get(nodo)
            if mp is not None and mp in criticos:
                candidatos.append((pos_en_os[mp], pos_en_os[nodo]))
        rng.shuffle(candidatos)
        for (i, k) in candidatos:
            os_vec[i], os_vec[k] = os_vec[k], os_vec[i]
            mk2, _, det2 = decodificar(inst, os_vec, ms_vec)
            if mk2 < mk:
                mk, detalle = mk2, det2
                mejoro = True
                break
            else:
                os_vec[i], os_vec[k] = os_vec[k], os_vec[i]   # revertir

        # Vecindario 2: reasignacion de maquina de operaciones criticas 
        if not mejoro:
            criticos_lst = list(criticos)
            rng.shuffle(criticos_lst)
            for (job, o) in criticos_lst:
                idx = inst.offset[job] + o
                alts = inst.trabajos[job][o]
                if len(alts) <= 1:
                    continue
                alt_actual = ms_vec[idx]
                # Probar alternativas ordenadas por menor tiempo de proceso.
                for a in sorted(range(len(alts)), key=lambda x: alts[x][1]):
                    if a == alt_actual:
                        continue
                    ms_vec[idx] = a
                    mk2, _, det2 = decodificar(inst, os_vec, ms_vec)
                    if mk2 < mk:
                        mk, detalle = mk2, det2
                        mejoro = True
                        break
                    else:
                        ms_vec[idx] = alt_actual   # revertir
                if mejoro:
                    break

        if not mejoro:
            break   # optimo local: no hay vecino mejor

    return mk


# SELECCION

def seleccion_torneo(poblacion, fitness, rng, k=3):
    mejor = rng.randrange(len(poblacion))
    for _ in range(k - 1):
        c = rng.randrange(len(poblacion))
        if fitness[c] < fitness[mejor]:
            mejor = c
    return mejor

# BUCLE PRINCIPAL DEL ALGORITMO MEMETICO

def memetico(inst, semilla, tiempo_max=60.0,
             tam_poblacion=40, prob_cruce=0.9, prob_mut=0.2,
             elitismo=2, pruebas_ls=30, prob_ls=0.5):
    rng = random.Random(semilla)
    t0 = time.perf_counter()

    # --- Poblacion inicial y evaluacion ---
    poblacion = crear_poblacion(inst, tam_poblacion, rng)
    fitness = []
    evaluaciones = 0
    for ind in poblacion:
        mk, _, _ = decodificar(inst, ind[0], ind[1])
        fitness.append(mk)
        evaluaciones += 1

    mejor_idx = min(range(len(fitness)), key=lambda i: fitness[i])
    mejor_mk = fitness[mejor_idx]
    mejor_ind = [poblacion[mejor_idx][0][:], poblacion[mejor_idx][1][:]]

    generaciones = 0
    historial = [mejor_mk]
    estancado = 0          # generaciones sin mejora del mejor global

    #  Evolucion hasta agotar el presupuesto temporal 
    while time.perf_counter() - t0 < tiempo_max:
        generaciones += 1

        # Elitismo: conservar los 'elitismo' mejores.
        orden = sorted(range(len(poblacion)), key=lambda i: fitness[i])
        nueva_pob = [[poblacion[i][0][:], poblacion[i][1][:]]
                     for i in orden[:elitismo]]
        nueva_fit = [fitness[i] for i in orden[:elitismo]]

        # Intensificacion: busqueda local sobre el mejor elite cada generacion.
        if time.perf_counter() - t0 < tiempo_max:
            mk_el = busqueda_local(inst, nueva_pob[0], rng, pruebas_ls)
            nueva_fit[0] = mk_el

        # Generar descendencia hasta completar la poblacion.
        while len(nueva_pob) < tam_poblacion:
            # Cortar la generacion si se acaba el tiempo a mitad de camino.
            if time.perf_counter() - t0 >= tiempo_max:
                break

            p1 = seleccion_torneo(poblacion, fitness, rng)
            p2 = seleccion_torneo(poblacion, fitness, rng)

            #  Cruce 
            if rng.random() < prob_cruce:
                hijo_os = cruce_pox(poblacion[p1][0], poblacion[p2][0], inst, rng)
                hijo_ms = cruce_uniforme_ms(poblacion[p1][1], poblacion[p2][1], rng)
            else:
                hijo_os = poblacion[p1][0][:]
                hijo_ms = poblacion[p1][1][:]

            #  Mutacion 
            if rng.random() < prob_mut:
                hijo_os = mutar_os(hijo_os, rng)
            if rng.random() < prob_mut:
                hijo_ms = mutar_ms(hijo_ms, inst, rng)

            hijo = [hijo_os, hijo_ms]

            # Busqueda local (memetico) sobre parte de la descendencia 
            if rng.random() < prob_ls:
                mk_hijo = busqueda_local(inst, hijo, rng, pruebas_ls)
            else:
                mk_hijo, _, _ = decodificar(inst, hijo[0], hijo[1])
            evaluaciones += 1

            nueva_pob.append(hijo)
            nueva_fit.append(mk_hijo)

        poblacion, fitness = nueva_pob, nueva_fit

        # Actualizar el mejor global.
        idx = min(range(len(fitness)), key=lambda i: fitness[i])
        if fitness[idx] < mejor_mk:
            mejor_mk = fitness[idx]
            mejor_ind = [poblacion[idx][0][:], poblacion[idx][1][:]]
            estancado = 0
        else:
            estancado += 1

        # Diversificacion: si el mejor no mejora en muchas generaciones, se
        # reemplaza la mitad peor de la poblacion por individuos nuevos
        # (manteniendo los mejores). Ayuda a escapar de optimos locales en las
        # instancias mas dificiles sin perder lo ya encontrado.
        if estancado >= 15:
            orden = sorted(range(len(poblacion)), key=lambda i: fitness[i])
            mitad = tam_poblacion // 2
            frescos = crear_poblacion(inst, tam_poblacion - mitad, rng)
            nueva_pob = [poblacion[i] for i in orden[:mitad]] + frescos
            nueva_fit = [fitness[i] for i in orden[:mitad]]
            for ind in frescos:
                mk, _, _ = decodificar(inst, ind[0], ind[1])
                nueva_fit.append(mk)
                evaluaciones += 1
            poblacion, fitness = nueva_pob, nueva_fit
            estancado = 0

        historial.append(mejor_mk)

    tiempo_total = time.perf_counter() - t0

    return {
        "makespan": mejor_mk,
        "iteraciones": generaciones,
        "evaluaciones": evaluaciones,
        "tiempo": tiempo_total,
        "mejor_individuo": mejor_ind,
        "historial": historial,
    }
