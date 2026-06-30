# =============================================================================
#  fjsp_core.py
#  Módulo base del framework de optimización para el FJSP.
#
#  Contenido:
#    · FJSPInstance     — carga y representa una instancia del benchmark Hurink.
#    · Solution         — codifica una solución y evalúa su makespan.
#    · solucion_inicial — construye el punto de partida mediante reglas de despacho.
#
#  Formato de archivo (Hurink, text_fjsp_old_format):
#    Línea 1   : <n_trabajos>  <n_máquinas>  <índice_flexibilidad>
#    Líneas 2…n+1 : una por trabajo.
#      <n_ops>  [ <n_maq_posibles>  (<máquina> <tiempo>)… ]…
#    Las máquinas se indexan desde 1 en los archivos originales;
#    internamente se trabaja en base 0.
#
#  Referencia del benchmark:
#    Hurink, J., Jurisch, B. & Thole, M. (1994). Tabu search for the
#    job-shop scheduling problem with multi-purpose machines.
#    OR Spektrum, 15, 205–215.
# =============================================================================

import random


class FJSPInstance:
    """
    Almacena los datos de una instancia del FJSP leída desde disco.

    Atributos
    ---------
    n_jobs       : número de trabajos.
    n_machines   : número de máquinas disponibles.
    flexibilidad : índice de flexibilidad del archivo.
    operaciones  : operaciones[j][o] → [(máquina_base0, tiempo), …]
    total_ops    : suma total de operaciones en la instancia.
    """

    def __init__(self, ruta: str, nombre: str = "", carpeta: str = ""):
        self.ruta         = ruta
        self.nombre       = nombre
        self.carpeta      = carpeta
        self.n_jobs       = 0
        self.n_machines   = 0
        self.flexibilidad = 0.0
        self.operaciones  = []
        self.total_ops    = 0
        self._cargar()

    def _cargar(self):
        with open(self.ruta, "r") as f:
            lineas = [l.strip() for l in f if l.strip()]

        cab = lineas[0].split()
        self.n_jobs       = int(cab[0])
        self.n_machines   = int(cab[1])
        self.flexibilidad = float(cab[2]) if len(cab) > 2 else 0.0

        for j in range(1, self.n_jobs + 1):
            tokens = [int(float(t)) for t in lineas[j].split()]
            idx    = 0
            n_ops  = tokens[idx]; idx += 1
            ops    = []
            for _ in range(n_ops):
                n_maq = tokens[idx]; idx += 1
                alts  = []
                for _ in range(n_maq):
                    maq  = tokens[idx] - 1
                    t    = tokens[idx + 1]
                    idx += 2
                    alts.append((maq, t))
                ops.append(alts)
            self.operaciones.append(ops)

        self.total_ops = sum(len(o) for o in self.operaciones)

    def ops_de_trabajo(self, j: int) -> int:
        return len(self.operaciones[j])

    def __repr__(self):
        return (f"FJSPInstance({self.carpeta}/{self.nombre} | "
                f"{self.n_jobs}j × {self.n_machines}m | "
                f"{self.total_ops} ops | flex={self.flexibilidad})")


class Solution:
    """
    Solución del FJSP mediante codificación de doble vector.

    secuencia  : permutación con repetición de índices de trabajo.
                 La k-ésima aparición del trabajo j representa su k-ésima
                 operación. Toda permutación válida respeta automáticamente
                 las precedencias internas de cada trabajo.

    asignacion : (j, o) → índice de alternativa elegida en operaciones[j][o].

    La evaluación se realiza con decode(), que simula la ejecución mediante
    inserción por la izquierda y calcula el makespan Cmax.
    """

    def __init__(self, instancia: FJSPInstance):
        self.instancia    = instancia
        self.secuencia    = []
        self.asignacion   = {}
        self.makespan     = None
        self.inicio       = {}
        self.fin          = {}
        self.maquina_de   = {}
        self.iter_vns        = 0
        self.iter_tabu       = 0
        self.iter_mejor      = 0
        self.tiempo_mejor_s  = 0.0

    def copiar(self) -> "Solution":
        c = Solution(self.instancia)
        c.secuencia      = list(self.secuencia)
        c.asignacion     = dict(self.asignacion)
        c.makespan       = self.makespan
        c.iter_vns       = self.iter_vns
        c.iter_tabu      = self.iter_tabu
        c.iter_mejor     = self.iter_mejor
        c.tiempo_mejor_s = self.tiempo_mejor_s
        return c

    def decode(self) -> int:
        """
        Decodifica la solución a un programa activo por inserción a la izquierda.
        Cada operación se programa en el instante más temprano compatible con
        la disponibilidad de su máquina y el término de su predecesora en el trabajo.
        """
        inst          = self.instancia
        libre_maq     = [0] * inst.n_machines
        libre_trab    = [0] * inst.n_jobs
        prox          = [0] * inst.n_jobs
        self.inicio.clear(); self.fin.clear(); self.maquina_de.clear()

        for j in self.secuencia:
            o            = prox[j]
            idx          = self.asignacion[(j, o)]
            maq, tiempo  = inst.operaciones[j][o][idx]
            ini          = max(libre_maq[maq], libre_trab[j])
            fin          = ini + tiempo
            libre_maq[maq]  = fin
            libre_trab[j]   = fin
            prox[j]        += 1
            self.inicio[(j, o)]    = ini
            self.fin[(j, o)]       = fin
            self.maquina_de[(j, o)]= maq

        self.makespan = max(libre_maq) if inst.n_machines else 0
        return self.makespan

    def ruta_critica(self) -> list:
        """
        Retorna las operaciones cuyo retraso incrementaría el makespan.
        Incluye la operación terminal (fin == Cmax) y su cadena de predecesoras
        en el mismo trabajo. Restringir los vecindarios a estas operaciones
        reduce el esfuerzo computacional sin comprometer la capacidad de mejora.
        """
        if self.makespan is None:
            self.decode()
        terminales   = [(j, o) for (j, o), f in self.fin.items() if f == self.makespan]
        predecesoras = [(j, oo) for (j, o) in terminales for oo in range(o)]
        criticas     = list(set(terminales + predecesoras))
        return criticas if criticas else list(self.fin.keys())


def solucion_inicial(inst: FJSPInstance, semilla: int = None) -> Solution:
    """
    Construye una solución inicial combinando dos reglas de despacho:

    Asignación — Mínima Carga Global (MCG):
      Cada operación se asigna a la máquina que minimiza la suma de su
      tiempo de procesamiento y la carga acumulada de esa máquina,
      distribuyendo el trabajo de forma equilibrada.

    Secuenciación — Permutación aleatoria con semilla fija:
      Se genera y baraja una permutación con repetición de los trabajos,
      garantizando reproducibilidad mediante la semilla indicada.
    """
    rng   = random.Random(semilla)
    sol   = Solution(inst)
    carga = [0] * inst.n_machines

    for j in range(inst.n_jobs):
        for o in range(inst.ops_de_trabajo(j)):
            alts     = inst.operaciones[j][o]
            mejor    = min(range(len(alts)), key=lambda i: carga[alts[i][0]] + alts[i][1])
            sol.asignacion[(j, o)] = mejor
            maq, t   = alts[mejor]
            carga[maq] += t

    seq = [j for j in range(inst.n_jobs) for _ in range(inst.ops_de_trabajo(j))]
    rng.shuffle(seq)
    sol.secuencia = seq
    sol.decode()
    return sol


if __name__ == "__main__":
    import os
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instancias")
    for root, _, files in os.walk(base):
        for fn in files:
            if fn == "la01.txt" and os.path.basename(root) == "edata":
                inst = FJSPInstance(os.path.join(root, fn), "la01", "edata")
                print(inst)
                s = solucion_inicial(inst, semilla=42)
                print(f"Makespan inicial : {s.makespan}")
                print(f"Ops. críticas    : {len(s.ruta_critica())}")
