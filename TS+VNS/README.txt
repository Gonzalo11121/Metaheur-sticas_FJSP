TS+VNS para el Flexible Job Shop Scheduling Problem (FJSP)
==========================================================

Algoritmo: Busqueda Tabu + Busqueda de Vecindad Variable con agitacion adaptativa
Autor    : Benjamin Velasquez Reyes
Curso    : Metaheuristicas / Optimizacion Combinatoria
           Universidad Andres Bello, Ing. Civil en Informatica


REQUISITOS
----------
Python 3.8 o superior.
Instalar dependencias:

    pip install -r requirements.txt


ESTRUCTURA
----------
TS_VNS/
  fjsp_core.py              Parser de instancias y representacion de soluciones
  ts_vns.py                 Algoritmo TS+VNS
  experimentos.py           Script principal de experimentacion
  requirements.txt          Dependencias
  instancias/
    Hurink/
      edata/                la01, la06, la11, la16, la21  (.txt)
      rdata/                la01, la06, la11, la16, la21  (.txt)
      vdata/                la01, la06, la11, la16, la21  (.txt)
    Brandimarte/            Mk01 - Mk10  (.fjs)
    Dauzere/                01a, 04a, 07a, 10a, 13a, 16a  (.fjs)
  resultados/               Carpeta de salida (se genera al correr)


USO
---
Desde la carpeta TS_VNS/, ejecutar:

    python experimentos.py

El script corre las 31 instancias con 5 repeticiones cada una (~2 horas).
Al terminar genera en resultados/:

    resultados_reporte.txt    Reporte legible por benchmark
    resultados.xlsx           Tablas por benchmark y repeticiones individuales
    configuracion.txt         Parametros y entorno de ejecucion


BENCHMARKS Y REFERENCIAS
-------------------------
Hurink (edata/rdata/vdata):
  Hurink, E., Jurisch, B. & Thole, M. (1994). Tabu search for the job-shop
  scheduling problem with multi-purpose machines. OR Spektrum, 15, 205-215.

Brandimarte:
  Brandimarte, P. (1993). Routing and scheduling in a flexible job shop by
  tabu search. Annals of Operations Research, 22, 158-183.

Dauzere:
  Dauzere-Peres, S. & Paulli, J. (1997). An integrated approach for modeling
  and solving the general multiprocessor job-shop scheduling problem using
  tabu search. Annals of Operations Research, 70, 281-306.

Upper bounds de referencia:
  Mastrolilli, M. & Gambardella, L.M. (2000). Effective neighborhood functions
  for the flexible job shop problem. Journal of Scheduling, 3(1), 3-20.


PARAMETROS DEL ALGORITMO
-------------------------
  max_iter      = 40     Iteraciones del bucle VNS
  k_max         = 4      Maxima intensidad de agitacion
  tabu_iter     = 40     Iteraciones de Busqueda Tabu por llamada
  tenencia      = 10     Longitud de la lista tabu
  tiempo_limite = 60 s   Presupuesto computacional por instancia
  repeticiones  = 5      Corridas independientes por instancia
  semilla_base  = 100    Semillas: 100, 101, 102, 103, 104
