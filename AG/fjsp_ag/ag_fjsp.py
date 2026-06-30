

import random
import time


#  DECODIFICADOR
def _insertar_en_hueco(intervalos, est, dur):
    inicio = est
    # Buscar el primer hueco valido entre intervalos ya ocupados.
    for k in range(len(intervalos)):
        ini_k, fin_k = intervalos[k]
        # Inicio del hueco anterior a este intervalo: max(est, fin del previo)
        hueco_ini = inicio
        if hueco_ini + dur <= ini_k:
            # Cabe antes del intervalo k.
            intervalos.insert(k, [hueco_ini, hueco_ini + dur])
            return hueco_ini
        # No cabe: avanzar despues de este intervalo.
        if inicio < fin_k:
            inicio = fin_k
    # No cupo en ningun hueco intermedio: va al final.
    intervalos.append([inicio, inicio + dur])
    return inicio


def decodificar(inst, os_vec, ms_vec):
    """Construye el schedule activo y devuelve (makespan, asignaciones).

    'asignaciones' es una lista por operacion global con
    (trabajo, op, maquina, inicio, fin), util para depurar o graficar Gantt.
    """
    # Intervalos ocupados por maquina.
    ocup = [[] for _ in range(inst.n_machines)]
    fin_job = [0] * inst.n_jobs      # fin de la ultima operacion programada del trabajo
    sig_op = [0] * inst.n_jobs       # indice de la proxima operacion de cada trabajo
    makespan = 0
    asignaciones = [None] * inst.total_ops

    for j in os_vec:
        o = sig_op[j]
        gid = inst.op_global[(j, o)]
        alt = ms_vec[gid]
        maquina, dur = inst.trabajos[j][o][alt]
        est = fin_job[j]                          # earliest start por precedencia
        inicio = _insertar_en_hueco(ocup[maquina], est, dur)
        fin = inicio + dur
        fin_job[j] = fin
        sig_op[j] += 1
        if fin > makespan:
            makespan = fin
        asignaciones[gid] = (j, o, maquina, inicio, fin)

    return makespan, asignaciones



#  INICIALIZACION
def _os_base(inst):
    """Vector OS canonico: cada trabajo repetido segun su numero de operaciones."""
    base = []
    for j in range(inst.n_jobs):
        base.extend([j] * inst.n_ops_por_job[j])
    return base


def _ms_aleatorio(inst, rng):
    """MS con maquina elegida al azar"""
    ms = [0] * inst.total_ops
    for gid, (j, o) in enumerate(inst.op_jo):
        ms[gid] = rng.randrange(len(inst.trabajos[j][o]))
    return ms


def _ms_tiempo_minimo(inst):
    """MS greedy"""
    ms = [0] * inst.total_ops
    for gid, (j, o) in enumerate(inst.op_jo):
        alts = inst.trabajos[j][o]
        mejor = min(range(len(alts)), key=lambda a: alts[a][1])
        ms[gid] = mejor
    return ms


def _ms_carga_balanceada(inst, rng):
    """asigna cada operacion"""
    carga = [0] * inst.n_machines
    ms = [0] * inst.total_ops
    orden = list(range(inst.total_ops))
    rng.shuffle(orden)
    for gid in orden:
        j, o = inst.op_jo[gid]
        alts = inst.trabajos[j][o]
        mejor_a, mejor_val = 0, None
        for a, (m, t) in enumerate(alts):
            val = carga[m] + t
            if mejor_val is None or val < mejor_val:
                mejor_val, mejor_a = val, a
        ms[gid] = mejor_a
        m, t = alts[mejor_a]
        carga[m] += t
    return ms


def crear_individuo(inst, rng, modo):
    """Crea (os_vec, ms_vec). 'modo' define la heuristica de la parte MS."""
    os_vec = _os_base(inst)[:]
    rng.shuffle(os_vec)
    if modo == "spt":
        ms_vec = _ms_tiempo_minimo(inst)
    elif modo == "balance":
        ms_vec = _ms_carga_balanceada(inst, rng)
    else:
        ms_vec = _ms_aleatorio(inst, rng)
    return [os_vec, ms_vec]


#  OPERADORES GENETICOS
def cruce_pox(p1_os, p2_os, inst, rng):
    """POX: divide el conjunto de trabajos en dos grupos. El hijo conserva de
    p1 las posiciones cuyos trabajos estan en el grupo J1 y completa el resto
    con el orden relativo de p2 (trabajos del grupo J2). Preserva precedencias."""
    jobs = list(range(inst.n_jobs))
    rng.shuffle(jobs)
    corte = rng.randint(1, inst.n_jobs - 1) if inst.n_jobs > 1 else 1
    J1 = set(jobs[:corte])

    hijo = [None] * len(p1_os)
    # Conservar de p1 las posiciones de trabajos en J1.
    for i, g in enumerate(p1_os):
        if g in J1:
            hijo[i] = g
    # Rellenar huecos con los genes de p2 que NO estan en J1, en orden.
    resto = [g for g in p2_os if g not in J1]
    it = iter(resto)
    for i in range(len(hijo)):
        if hijo[i] is None:
            hijo[i] = next(it)
    return hijo


def cruce_uniforme_ms(p1_ms, p2_ms, rng):
    return [p1_ms[i] if rng.random() < 0.5 else p2_ms[i]
            for i in range(len(p1_ms))]


def mutar_os(os_vec, rng):
    n = len(os_vec)
    if rng.random() < 0.5:
        i, k = rng.randrange(n), rng.randrange(n)
        os_vec[i], os_vec[k] = os_vec[k], os_vec[i]
    else:
        i = rng.randrange(n)
        g = os_vec.pop(i)
        k = rng.randrange(n)
        os_vec.insert(k, g)


def mutar_ms(ms_vec, inst, rng, prob_gen, sesgo_spt):
    for gid, (j, o) in enumerate(inst.op_jo):
        alts = inst.trabajos[j][o]
        if len(alts) <= 1:
            continue
        if rng.random() < prob_gen:
            if rng.random() < sesgo_spt:
                ms_vec[gid] = min(range(len(alts)), key=lambda a: alts[a][1])
            else:
                ms_vec[gid] = rng.randrange(len(alts))


def seleccion_torneo(poblacion, fitness, rng, k):
    """Seleccion por torneo de tamano k: devuelve el indice del ganador
    (menor makespan = mejor)."""
    mejor = rng.randrange(len(poblacion))
    for _ in range(k - 1):
        c = rng.randrange(len(poblacion))
        if fitness[c] < fitness[mejor]:
            mejor = c
    return mejor


#  BUCLE PRINCIPAL DEL ALGORITMO GENETICO
def resolver_ag(inst, semilla, presupuesto_seg,
                tam_poblacion=100, prob_cruce=0.9, prob_mut_os=0.2,
                prob_mut_ms_ind=0.3, prob_mut_ms_gen=0.15, sesgo_spt=0.5,
                k_torneo=3, elitismo=2, estancamiento_max=120,
                frac_inmigrantes=0.15, registrar_historial=False):
    
    rng = random.Random(semilla)
    t0 = time.perf_counter()
    poblacion = []
    for i in range(tam_poblacion):
        if i == 0:
            modo = "spt"
        elif i < tam_poblacion * 0.25:
            modo = "balance"
        else:
            modo = "rand"
        poblacion.append(crear_individuo(inst, rng, modo))

    # Evaluacion inicial
    fitness = []
    asig_cache = []
    for ind in poblacion:
        mk, asg = decodificar(inst, ind[0], ind[1])
        fitness.append(mk)
        asig_cache.append(asg)
    evaluaciones = tam_poblacion

    # Mejor global
    bi = min(range(len(fitness)), key=lambda i: fitness[i])
    mejor_mk = fitness[bi]
    mejor_asig = asig_cache[bi]

    generaciones = 0
    estancamiento = 0   # generaciones sin mejora del mejor global
    mejor_mk_prev = mejor_mk

    historial = []
    if registrar_historial:
        historial.append((0.0, 0, mejor_mk))

    while time.perf_counter() - t0 < presupuesto_seg:
        # Elitismo: conservar los 'elitismo' mejores.
        orden = sorted(range(len(fitness)), key=lambda i: fitness[i])
        nueva_pob = [[poblacion[i][0][:], poblacion[i][1][:]]
                     for i in orden[:elitismo]]
        nuevo_fit = [fitness[i] for i in orden[:elitismo]]
        nuevo_asig = [asig_cache[i] for i in orden[:elitismo]]

        if estancamiento >= estancamiento_max:
            n_imm = int(tam_poblacion * frac_inmigrantes)
            for _ in range(n_imm):
                ind = crear_individuo(inst, rng, "rand")
                mk, asg = decodificar(inst, ind[0], ind[1])
                evaluaciones += 1
                nueva_pob.append(ind)
                nuevo_fit.append(mk)
                nuevo_asig.append(asg)
                if mk < mejor_mk:
                    mejor_mk = mk
                    mejor_asig = asg
            estancamiento = 0

        # Generar el resto de la poblacion.
        while len(nueva_pob) < tam_poblacion:
            ip1 = seleccion_torneo(poblacion, fitness, rng, k_torneo)
            ip2 = seleccion_torneo(poblacion, fitness, rng, k_torneo)
            p1, p2 = poblacion[ip1], poblacion[ip2]

            # --- Cruce ---
            if rng.random() < prob_cruce:
                hijo_os = cruce_pox(p1[0], p2[0], inst, rng)
                hijo_ms = cruce_uniforme_ms(p1[1], p2[1], rng)
            else:
                hijo_os = p1[0][:]
                hijo_ms = p1[1][:]

            # --- Mutacion ---
            if rng.random() < prob_mut_os:
                mutar_os(hijo_os, rng)
            if rng.random() < prob_mut_ms_ind:
                mutar_ms(hijo_ms, inst, rng, prob_mut_ms_gen, sesgo_spt)

            # --- Evaluacion del hijo ---
            mk, asg = decodificar(inst, hijo_os, hijo_ms)
            evaluaciones += 1
            nueva_pob.append([hijo_os, hijo_ms])
            nuevo_fit.append(mk)
            nuevo_asig.append(asg)

            if mk < mejor_mk:
                mejor_mk = mk
                mejor_asig = asg

            # Cortar si se agoto el tiempo a mitad de generacion.
            if time.perf_counter() - t0 >= presupuesto_seg:
                break

        poblacion = nueva_pob
        fitness = nuevo_fit
        asig_cache = nuevo_asig
        generaciones += 1

        # Actualizar contador de estancamiento.
        if min(fitness) < mejor_mk_prev:
            estancamiento = 0
        else:
            estancamiento += 1
        mejor_mk_prev = mejor_mk

        if registrar_historial:
            historial.append((time.perf_counter() - t0, generaciones, mejor_mk))

    tiempo = time.perf_counter() - t0
    resultado = {
        "makespan": mejor_mk,
        "generaciones": generaciones,
        "tiempo": tiempo,
        "asignaciones": mejor_asig,
        "evaluaciones": evaluaciones,
    }
    if registrar_historial:
        resultado["historial"] = historial
    return resultado


if __name__ == "__main__":
    # Prueba rapida con presupuesto corto.
    from fjsp_parser import leer_instancia
    inst = leer_instancia("instancias/edata/la01.txt", "edata/la01")
    res = resolver_ag(inst, semilla=100, presupuesto_seg=5.0)
    print("Instancia edata/la01 | UB=609")
    print("  Mejor makespan :", res["makespan"])
    print("  Generaciones   :", res["generaciones"])
    print("  Evaluaciones   :", res["evaluaciones"])
    print("  Tiempo (s)     :", round(res["tiempo"], 2))
