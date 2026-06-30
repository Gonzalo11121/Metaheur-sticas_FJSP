# -*- coding: utf-8 -*-
"""
fjsp_parser.py
==============
Lector (parser) de instancias del Problema de Job Shop Flexible (FJSP) en el
*formato de texto antiguo* de FJSPLib, usado por los benchmarks de
Hurink, Jurisch y Thole (1994): subconjuntos edata, rdata y vdata.

Formato del archivo
-------------------
- 1a linea (cabecera):  <n_trabajos>  <n_maquinas>  <flexibilidad_promedio>
    * la flexibilidad promedio es informativa y puede ser entero o decimal.
- Luego, una linea por TRABAJO. Cada linea contiene:
    <n_operaciones>
    y por cada operacion:
        <n_opciones>  (maquina  duracion)  (maquina  duracion) ... [n_opciones pares]
    * Las maquinas vienen en BASE 1 en el archivo (1..n_maquinas).

Ejemplo (extracto de una linea de trabajo):
    5   1   2   21  1   1   53  ...
    -> 5 operaciones
       op1: 1 opcion -> (maquina 2, dur 21)
       op2: 1 opcion -> (maquina 1, dur 53)
       ...

Estructura de datos resultante (clase Instancia)
------------------------------------------------
- n_trabajos, n_maquinas
- trabajos: lista de trabajos; cada trabajo es una lista de operaciones;
  cada operacion es una lista de tuplas (maquina_base0, duracion).
  -> trabajos[j][o] = [(m, p), (m, p), ...]   con m en 0..n_maquinas-1

Solo se usan modulos de la biblioteca estandar de Python.
"""

import os


class Instancia:
    """Contenedor de una instancia FJSP ya parseada."""

    def __init__(self, nombre, n_trabajos, n_maquinas, trabajos, flexibilidad=None):
        self.nombre = nombre                 # str identificador (ej. "edata/la01")
        self.n_trabajos = n_trabajos         # int
        self.n_maquinas = n_maquinas         # int
        self.trabajos = trabajos             # list[list[list[(maquina, dur)]]]
        self.flexibilidad = flexibilidad     # float informativo (cabecera)

        # Precalculos utiles para la metaheuristica -------------------------
        # n_ops_por_trabajo[j] = numero de operaciones del trabajo j
        self.n_ops_por_trabajo = [len(t) for t in trabajos]
        # total de operaciones de la instancia
        self.n_operaciones = sum(self.n_ops_por_trabajo)
        # Lista plana de operaciones como pares (trabajo, indice_operacion)
        self.operaciones = [(j, o)
                            for j in range(n_trabajos)
                            for o in range(self.n_ops_por_trabajo[j])]

    # -- utilidades de acceso ----------------------------------------------
    def opciones(self, j, o):
        """Devuelve la lista de (maquina, duracion) de la operacion (j, o)."""
        return self.trabajos[j][o]

    def duracion(self, j, o, maquina):
        """Duracion de la operacion (j, o) si se ejecuta en 'maquina'."""
        for m, p in self.trabajos[j][o]:
            if m == maquina:
                return p
        raise ValueError(
            "La maquina %d no es elegible para la operacion (%d,%d)" % (maquina, j, o))

    def __repr__(self):
        return ("Instancia(%s, trabajos=%d, maquinas=%d, operaciones=%d, flex=%s)"
                % (self.nombre, self.n_trabajos, self.n_maquinas,
                   self.n_operaciones, self.flexibilidad))


def parsear_archivo(ruta, nombre=None):
    """
    Lee un archivo de instancia FJSP (formato antiguo) y devuelve una Instancia.

    Estrategia robusta:
      1) Se lee la PRIMERA linea como cabecera: n_trabajos, n_maquinas, flex.
         (Esto es necesario porque la flexibilidad puede ser un entero como '2',
          indistinguible por valor del conteo de operaciones de un trabajo.)
      2) El resto del archivo se procesa como un flujo plano de enteros usando
         los contadores autodescriptivos (n_operaciones, n_opciones, pares),
         lo que lo hace inmune a saltos de linea inesperados.
    """
    if nombre is None:
        nombre = os.path.basename(ruta)

    with open(ruta, "r") as f:
        lineas = f.read().splitlines()

    # Descartar lineas totalmente vacias al inicio (por si acaso)
    lineas = [ln for ln in lineas if ln.strip() != ""]
    if not lineas:
        raise ValueError("Archivo vacio: %s" % ruta)

    # --- Cabecera ---------------------------------------------------------
    cab = lineas[0].split()
    if len(cab) < 2:
        raise ValueError("Cabecera invalida en %s: %r" % (ruta, lineas[0]))
    n_trabajos = int(cab[0])
    n_maquinas = int(cab[1])
    flexibilidad = float(cab[2]) if len(cab) >= 3 else None

    # --- Cuerpo: flujo plano de enteros ----------------------------------
    cuerpo = []
    for ln in lineas[1:]:
        cuerpo.extend(ln.split())
    cuerpo = [int(x) for x in cuerpo]

    trabajos = []
    idx = 0  # cursor sobre el flujo 'cuerpo'
    for j in range(n_trabajos):
        if idx >= len(cuerpo):
            raise ValueError(
                "Datos insuficientes leyendo el trabajo %d en %s" % (j, ruta))
        n_ops = cuerpo[idx]; idx += 1
        operaciones = []
        for o in range(n_ops):
            n_opc = cuerpo[idx]; idx += 1
            opciones = []
            for _ in range(n_opc):
                maquina = cuerpo[idx]; idx += 1      # base 1 en el archivo
                dur = cuerpo[idx]; idx += 1
                maquina0 = maquina - 1               # convertimos a base 0
                if not (0 <= maquina0 < n_maquinas):
                    raise ValueError(
                        "Maquina fuera de rango (%d) en %s, trabajo %d, op %d"
                        % (maquina, ruta, j, o))
                if dur < 0:
                    raise ValueError(
                        "Duracion negativa en %s, trabajo %d, op %d" % (ruta, j, o))
                opciones.append((maquina0, dur))
            operaciones.append(opciones)
        trabajos.append(operaciones)

    if idx != len(cuerpo):
        # No es fatal, pero avisa de tokens sobrantes (posible formato distinto)
        raise ValueError(
            "Sobran %d tokens al terminar de parsear %s (formato inesperado)"
            % (len(cuerpo) - idx, ruta))

    return Instancia(nombre, n_trabajos, n_maquinas, trabajos, flexibilidad)


if __name__ == "__main__":
    # Prueba rapida del parser sobre una instancia, si se ejecuta directamente.
    import sys
    if len(sys.argv) > 1:
        inst = parsear_archivo(sys.argv[1])
        print(inst)
        print("Operaciones por trabajo:", inst.n_ops_por_trabajo)
