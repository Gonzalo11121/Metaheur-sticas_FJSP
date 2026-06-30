# -*- coding: utf-8 -*-
"""
graficar.py
===========
Genera graficos para el informe de Busqueda Tabu - FJSP a partir del libro
resultados/resultados.xlsx producido por run_experiments.py:

  1) gap_<familia>.png            -> Gap% del mejor makespan por instancia,
                                      uno por familia de benchmark
                                      (Hurink, Brandimarte, Dauzere).
  2) makespan_std_<familia>.png   -> Makespan promedio +/- desviacion
                                      estandar, uno por familia.
  3) convergencia_<grupo>.png     -> curva de convergencia (mejor makespan vs
                                      iteracion) de una instancia
                                      representativa de cada uno de los 5
                                      grupos (Hurink edata/rdata/vdata,
                                      Brandimarte, Dauzere).

Total de graficos: 3 + 3 + 5 = 11.

Los graficos de gap% y makespan/std usan el resumen real exportado al xlsx.
Los de convergencia se generan ejecutando la metaheuristica con registro de
historial y semilla fija; al ser determinista por semilla, reproduce la
trayectoria de la corrida correspondiente.

En el grafico de la familia Hurink, las 15 instancias se distinguen por
subconjunto (edata/rdata/vdata) tanto en la etiqueta del eje (subset/la01)
como en el color de la barra, ya que el mismo nombre de instancia (la01,
la06, ...) se repite en los tres subconjuntos.

Uso:
  python3 graficar.py                       # usa resultados/resultados.xlsx
  python3 graficar.py --xlsx ruta/al.xlsx
  python3 graficar.py --tiempo 30           # segundos por instancia (convergencia)
  python3 graficar.py --sin-convergencia    # solo los graficos de resumen
"""

import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import openpyxl

from fjsp_parser import parsear_archivo
from taboo_search import resolver
import run_experiments as rx

SALIDA_GRAFICOS = os.path.join(rx.SALIDA_DIR, "graficos")

COLOR_GRUPO = {
    "Hurink_edata": "#4C72B0", "Hurink_rdata": "#DD8452",
    "Hurink_vdata": "#55A868", "Brandimarte": "#C44E52", "Dauzere": "#8172B3",
}

# Familias para los graficos de resumen (gap% y makespan +/- std): agrupan
# los 5 grupos de benchmark en 3 figuras, combinando los tres subconjuntos
# de Hurink en una sola.
FAMILIAS = [
    ("Hurink", ["Hurink_edata", "Hurink_rdata", "Hurink_vdata"]),
    ("Brandimarte", ["Brandimarte"]),
    ("Dauzere", ["Dauzere"]),
]


def leer_resumen(ruta_xlsx):
    """Lee la hoja Resumen_General y devuelve una lista de dicts."""
    wb = openpyxl.load_workbook(ruta_xlsx, data_only=True)
    ws = wb["Resumen_General"]
    filas = list(ws.iter_rows(values_only=True))
    encabezado = filas[0]
    idx = {nombre: i for i, nombre in enumerate(encabezado)}
    datos = []
    for fila in filas[1:]:
        if fila[idx["Instancia"]] is None:
            continue
        datos.append({
            "grupo": _grupo_de_benchmark(fila[idx["Benchmark"]]),
            "benchmark": fila[idx["Benchmark"]],
            "instancia": fila[idx["Instancia"]],
            "mejor": fila[idx["Mejor"]],
            "promedio": fila[idx["Promedio"]],
            "desv_std": fila[idx["Desv_Std"]],
            "gap_mejor": _num(fila[idx["Gap_Mejor%"]]),
        })
    return datos


def _grupo_de_benchmark(benchmark):
    for g in rx.GRUPOS:
        if g["benchmark"] == benchmark:
            return g["clave"]
    return benchmark


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _etiqueta(d, multi_grupo):
    """Etiqueta del eje X: si la familia mezcla varios grupos (caso Hurink),
    antepone el subconjunto para distinguir instancias con el mismo nombre."""
    if multi_grupo:
        sufijo = d["grupo"].split("_", 1)[-1]   # "Hurink_edata" -> "edata"
        return "%s/%s" % (sufijo, d["instancia"])
    return d["instancia"]


def _leyenda(grupos_familia):
    handles = []
    for clave in grupos_familia:
        etiqueta = next((g["benchmark"] for g in rx.GRUPOS if g["clave"] == clave),
                        clave)
        handles.append(plt.Rectangle((0, 0), 1, 1,
                                     color=COLOR_GRUPO.get(clave, "#777777"),
                                     label=etiqueta))
    return handles


def grafico_gap(nombre_familia, datos_familia, grupos_familia, ruta):
    validos = [d for d in datos_familia if d["gap_mejor"] is not None]
    multi = len(grupos_familia) > 1
    etiquetas = [_etiqueta(d, multi) for d in validos]
    valores = [d["gap_mejor"] for d in validos]
    colores = [COLOR_GRUPO.get(d["grupo"], "#777777") for d in validos]
    fig, ax = plt.subplots(figsize=(max(7, len(validos) * 0.5), 5))
    ax.bar(range(len(validos)), valores, color=colores)
    ax.set_xticks(range(len(validos)))
    ax.set_xticklabels(etiquetas, rotation=90, fontsize=8)
    ax.set_ylabel("Gap% (mejor vs UB)")
    ax.set_title("Gap%% del mejor makespan por instancia - %s" % nombre_familia)
    ax.axhline(0, color="black", linewidth=0.8)
    if multi:
        ax.legend(handles=_leyenda(grupos_familia), fontsize=8)
    fig.tight_layout()
    fig.savefig(ruta, dpi=130)
    plt.close(fig)


def grafico_std(nombre_familia, datos_familia, grupos_familia, ruta):
    multi = len(grupos_familia) > 1
    etiquetas = [_etiqueta(d, multi) for d in datos_familia]
    medias = [d["promedio"] for d in datos_familia]
    stds = [d["desv_std"] for d in datos_familia]
    colores = [COLOR_GRUPO.get(d["grupo"], "#777777") for d in datos_familia]
    fig, ax = plt.subplots(figsize=(max(7, len(datos_familia) * 0.5), 5))
    ax.bar(range(len(datos_familia)), medias, yerr=stds, color=colores, capsize=3)
    ax.set_xticks(range(len(datos_familia)))
    ax.set_xticklabels(etiquetas, rotation=90, fontsize=8)
    ax.set_ylabel("Makespan promedio (+/- std)")
    ax.set_title("Makespan promedio y desviacion estandar - %s" % nombre_familia)
    if multi:
        ax.legend(handles=_leyenda(grupos_familia), fontsize=8)
    fig.tight_layout()
    fig.savefig(ruta, dpi=130)
    plt.close(fig)


def graficos_resumen(datos):
    rutas = []
    for nombre_familia, grupos_familia in FAMILIAS:
        datos_familia = [d for d in datos if d["grupo"] in grupos_familia]
        if not datos_familia:
            continue
        ruta_gap = os.path.join(SALIDA_GRAFICOS, "gap_%s.png" % nombre_familia)
        ruta_std = os.path.join(SALIDA_GRAFICOS,
                                "makespan_std_%s.png" % nombre_familia)
        grafico_gap(nombre_familia, datos_familia, grupos_familia, ruta_gap)
        grafico_std(nombre_familia, datos_familia, grupos_familia, ruta_std)
        rutas.append(ruta_gap)
        rutas.append(ruta_std)
    return rutas


def grafico_convergencia(limite_tiempo):
    """Una curva por grupo (5 en total), usando la primera instancia de cada uno."""
    rutas = []
    for grupo in rx.GRUPOS:
        inst_name = grupo["instancias"][0]
        ruta_inst = grupo["ruta"](inst_name)
        if not os.path.isfile(ruta_inst):
            continue
        inst = parsear_archivo(ruta_inst, nombre="%s/%s" % (grupo["clave"], inst_name))
        r = resolver(inst, semilla=rx.SEMILLA_BASE, limite_tiempo=limite_tiempo,
                     registrar_historial=True)
        if not r["historial"]:
            continue
        xs = [it for (it, _mk) in r["historial"]]
        ys = [mk for (_it, mk) in r["historial"]]
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(xs, ys, color=COLOR_GRUPO.get(grupo["clave"], "#333333"))
        ax.set_xlabel("Iteracion")
        ax.set_ylabel("Mejor makespan")
        ax.set_title("Convergencia - %s / %s" % (grupo["benchmark"], inst_name))
        fig.tight_layout()
        ruta = os.path.join(SALIDA_GRAFICOS, "convergencia_%s.png" % grupo["clave"])
        fig.savefig(ruta, dpi=130)
        plt.close(fig)
        rutas.append(ruta)
    return rutas


def main():
    ap = argparse.ArgumentParser(description="Graficos Tabu Search FJSP")
    ap.add_argument("--xlsx", default=os.path.join(rx.SALIDA_DIR, "resultados.xlsx"),
                    help="ruta del libro resultados.xlsx")
    ap.add_argument("--tiempo", type=float, default=30.0,
                    help="segundos por instancia para convergencia (def. 30)")
    ap.add_argument("--sin-convergencia", action="store_true",
                    help="genera solo los 6 graficos de resumen (gap% y std)")
    args = ap.parse_args()

    if not os.path.isfile(args.xlsx):
        print("No se encontro el libro '%s'. Ejecuta antes run_experiments.py."
              % args.xlsx)
        return 1

    os.makedirs(SALIDA_GRAFICOS, exist_ok=True)
    datos = leer_resumen(args.xlsx)

    print("Graficos de resumen (gap% y makespan/std, por familia):")
    for ruta in graficos_resumen(datos):
        print("  - %s" % ruta)

    if not args.sin_convergencia:
        print("Graficos de convergencia (uno por grupo):")
        for ruta in grafico_convergencia(args.tiempo):
            print("  - %s" % ruta)
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
