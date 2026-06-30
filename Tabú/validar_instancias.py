# -*- coding: utf-8 -*-
"""
validar_instancias.py
=====================
Verifica la integridad de las instancias usadas por el proyecto: los tres
subconjuntos de Hurink (edata/rdata/vdata), Brandimarte y Dauzere.

Comprobaciones aplicadas a TODAS las instancias:
 1) El archivo parsea sin errores (formato, rango de maquinas, duraciones).
 2) Tamano esperado: numero de trabajos, de maquinas y total de operaciones.

Comprobaciones EXTRA, solo para Hurink (propiedades especificas de ese
benchmark, utiles para detectar errores de transcripcion numerica):
 3) Propiedad A: dentro de una operacion, TODAS las alternativas de maquina
    comparten la misma duracion.
 4) Propiedad B: para una misma instancia (ej. la01), el vector de
    duraciones por operacion es identico en edata, rdata y vdata.

Brandimarte y Dauzere no comparten estas dos propiedades (sus duraciones SI
varian segun la maquina elegida), por lo que en esos benchmarks solo se
aplican las comprobaciones (1) y (2).
"""
import os

from fjsp_parser import parsear_archivo
import run_experiments as rx

# (trabajos, maquinas, ops_por_trabajo) esperados de las instancias LA clasicas
# usadas en Hurink: en este benchmark todos los trabajos tienen el mismo
# numero de operaciones, por lo que se valida tambien ese tercer valor.
ESPERADO_HURINK = {
    "la01": (10, 5, 5),
    "la06": (15, 5, 5),
    "la11": (20, 5, 5),
    "la16": (10, 10, 10),
    "la21": (15, 10, 10),
}

# (trabajos, maquinas, operaciones_totales) esperados. A diferencia de Hurink,
# en Brandimarte y Dauzere el numero de operaciones varia entre trabajos, asi
# que se valida el total de operaciones de la instancia en lugar de por trabajo.
ESPERADO_BRANDIMARTE = {
    "Mk01": (10, 6, 55), "Mk02": (10, 6, 58), "Mk03": (15, 8, 150),
    "Mk04": (15, 8, 90), "Mk05": (15, 4, 106), "Mk06": (10, 15, 150),
    "Mk07": (20, 5, 100), "Mk08": (20, 10, 225), "Mk09": (20, 10, 240),
    "Mk10": (20, 15, 240),
}

ESPERADO_DAUZERE = {
    "01a": (10, 5, 196), "04a": (10, 5, 196), "07a": (15, 8, 293),
    "10a": (15, 8, 293), "13a": (20, 10, 387), "16a": (20, 10, 387),
}


def duracion_por_operacion(inst):
    """Devuelve la lista de duraciones (una por operacion) y verifica la
    propiedad A (duracion identica entre alternativas de una operacion)."""
    dur = []
    for j in range(inst.n_trabajos):
        for o in range(inst.n_ops_por_trabajo[j]):
            duraciones_alt = [p for (_m, p) in inst.opciones(j, o)]
            if len(set(duraciones_alt)) != 1:
                raise AssertionError(
                    "[%s] op (%d,%d) tiene duraciones distintas entre alternativas: %s"
                    % (inst.nombre, j, o, duraciones_alt))
            dur.append(duraciones_alt[0])
    return dur


def _validar_tamano(inst, nj, nm, n_ops_total, ops_por_trabajo=None):
    assert inst.n_trabajos == nj, \
        "%s: trabajos %d != %d" % (inst.nombre, inst.n_trabajos, nj)
    assert inst.n_maquinas == nm, \
        "%s: maquinas %d != %d" % (inst.nombre, inst.n_maquinas, nm)
    assert inst.n_operaciones == n_ops_total, \
        "%s: total ops %d != %d" % (inst.nombre, inst.n_operaciones, n_ops_total)
    if ops_por_trabajo is not None:
        assert all(n == ops_por_trabajo for n in inst.n_ops_por_trabajo), \
            "%s: alguna fila no tiene %d operaciones" % (inst.nombre, ops_por_trabajo)


def validar_hurink():
    """Valida los 15 casos de Hurink: tamano + propiedades A y B."""
    print("=== Hurink (edata / rdata / vdata) ===")
    ok = True
    for inst_name in rx.HURINK_INSTANCIAS:
        nj, nm, opj = ESPERADO_HURINK[inst_name]
        vectores = {}
        for sub in ("edata", "rdata", "vdata"):
            ruta = rx._ruta_hurink(sub)(inst_name)
            inst = parsear_archivo(ruta, nombre="%s/%s" % (sub, inst_name))
            _validar_tamano(inst, nj, nm, nj * opj, ops_por_trabajo=opj)
            vectores[sub] = duracion_por_operacion(inst)
            print("OK  %-12s  trabajos=%2d maquinas=%2d ops=%3d  flex=%.2f"
                  % (inst.nombre, inst.n_trabajos, inst.n_maquinas,
                     inst.n_operaciones, inst.flexibilidad))
        ref = vectores["vdata"]
        for sub in ("edata", "rdata", "vdata"):
            if vectores[sub] != ref:
                ok = False
                for k, (a, b) in enumerate(zip(vectores[sub], ref)):
                    if a != b:
                        print("  !! DISCREPANCIA en %s/%s op#%d: %s=%d vs vdata=%d"
                              % (sub, inst_name, k, sub, a, b))
                        break
    return ok


def validar_grupo_generico(nombre, ruta_fn, instancias, esperado):
    """Valida tamano (trabajos, maquinas, operaciones totales) para un grupo
    que no comparte las propiedades especiales de Hurink."""
    print("\n=== %s ===" % nombre)
    ok = True
    for inst_name in instancias:
        ruta = ruta_fn(inst_name)
        if not os.path.isfile(ruta):
            print("!!  %-12s  ARCHIVO NO ENCONTRADO: %s" % (inst_name, ruta))
            ok = False
            continue
        try:
            inst = parsear_archivo(ruta, nombre="%s/%s" % (nombre, inst_name))
            nj, nm, n_ops = esperado[inst_name]
            _validar_tamano(inst, nj, nm, n_ops)
            print("OK  %-12s  trabajos=%2d maquinas=%2d ops=%3d  flex=%s"
                  % (inst.nombre, inst.n_trabajos, inst.n_maquinas,
                     inst.n_operaciones,
                     ("%.2f" % inst.flexibilidad) if inst.flexibilidad else "n/d"))
        except (AssertionError, ValueError) as e:
            print("!!  %-12s  %s" % (inst_name, e))
            ok = False
    return ok


def main():
    ok_hurink = validar_hurink()
    ok_brandimarte = validar_grupo_generico(
        "Brandimarte", rx._ruta_brandimarte,
        ["Mk%02d" % k for k in range(1, 11)], ESPERADO_BRANDIMARTE)
    ok_dauzere = validar_grupo_generico(
        "Dauzere", rx._ruta_dauzere,
        ["01a", "04a", "07a", "10a", "13a", "16a"], ESPERADO_DAUZERE)

    ok = ok_hurink and ok_brandimarte and ok_dauzere
    print("\nResultado:",
          "TODAS LAS INSTANCIAS CONSISTENTES" if ok else "HAY DISCREPANCIAS")
    return ok


if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)
