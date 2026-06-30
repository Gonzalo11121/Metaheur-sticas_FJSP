=========================================================================
ALGORITMO MEMETICO PARA EL FLEXIBLE JOB SHOP SCHEDULING PROBLEM (FJSP)
Benchmarks: Hurink (1994) / Brandimarte (1993) / Dauzere (1998)
=========================================================================

DESCRIPCION
-----------
Implementacion en Python de un Algoritmo Memetico (Algoritmo Genetico +
Busqueda Local de ruta critica) para resolver el FJSP minimizando el
makespan. El proyecto ejecuta un conjunto de experimentos sobre tres
benchmarks y exporta los resultados en formato de texto y Excel.


ESTRUCTURA
----------
  instancia.py      Parser de instancias (formatos .txt de Hurink y .fjs).
  memetico.py       Decodificador por insercion + Algoritmo Genetico +
                    Busqueda Local de ruta critica.
  experimentos.py   Runner de experimentos: recorre los tres benchmarks,
                    calcula metricas y exporta los resultados.
  instancias/       Instancias organizadas por benchmark:
                      Hurink/      edata, rdata, vdata (cada uno con
                                   la01, la06, la11, la16, la21).
                      Brandimarte/ Mk01 .. Mk10.
                      Dauzere/     01a, 04a, 07a, 10a, 13a, 16a.
  resultados/       Carpeta donde se escriben las salidas.


INSTANCIAS Y UPPER BOUNDS DE REFERENCIA
---------------------------------------
  Hurink (1994)      : edata/rdata/vdata x {la01,la06,la11,la16,la21}.
  Brandimarte (1993) : Mk01..Mk10.
  Dauzere (1998)     : 01a,04a,07a,10a,13a,16a.

  Los upper bounds de Brandimarte y Dauzere provienen de
  Mastrolilli & Gambardella (2000). Los de Hurink son los mejores
  valores conocidos del benchmark original.


REQUISITOS
----------
  Python 3.8 o superior.
  El nucleo algoritmico usa solo la biblioteca estandar.
  La exportacion a Excel requiere openpyxl (ver requirements.txt):

      pip install -r requirements.txt


COMO EJECUTAR
-------------
  Corrida oficial (60 s por ejecucion, 5 repeticiones, 31 instancias):

      python3 experimentos.py

  Prueba rapida (para verificar que todo corre):

      python3 experimentos.py --tiempo 5 --reps 2

  Opciones:
      --tiempo          segundos por ejecucion        (def. 60)
      --reps            repeticiones por instancia    (def. 5)
      --semilla-base    semilla inicial               (def. 100)
      --instancias-dir  carpeta de instancias         (def. instancias)
      --salida-dir      carpeta de resultados         (def. resultados)

  Las semillas usadas son base, base+1, ..., base+reps-1
  (con la base por defecto: 100, 101, 102, 103, 104).

  Nota: la corrida oficial completa son 31 instancias x 5 repeticiones x
  60 segundos = 155 minutos aproximadamente.


SALIDAS (en la carpeta resultados/)
-----------------------------------
  resultados_reporte.txt   Informe legible organizado por benchmark, con
                           una tabla de metricas por subconjunto y el gap
                           promedio por benchmark.
  resultados.xlsx          Libro de Excel con las hojas:
                             Resumen_General
                             Hurink_edata, Hurink_rdata, Hurink_vdata
                             Brandimarte, Dauzere
                             Rep_Hurink_edata, Rep_Hurink_rdata,
                             Rep_Hurink_vdata, Rep_Brandimarte, Rep_Dauzere
                           Las hojas sin prefijo Rep_ contienen el resumen
                           por instancia; las Rep_ contienen una fila por
                           repeticion individual.
  configuracion.txt        Parametros del experimento, semillas utilizadas
                           y hardware detectado automaticamente.


METRICAS
--------
  mejor / promedio / peor   makespan de las repeticiones.
  desv_std                  desviacion estandar muestral (ddof=1).
  gap_mejor_% / gap_prom_%  100*(makespan - UB)/UB.
  iter_prom                 generaciones promedio por ejecucion.
  tiempo_prom_s             segundos promedio por ejecucion.


REFERENCIAS
-----------
  Brandimarte, P. (1993). Routing and scheduling in a flexible job shop
    by tabu search. Annals of Operations Research, 41, 157-183.
  Hurink, J., Jurisch, B., Thole, M. (1994). Tabu search for the job shop
    scheduling problem with multi-purpose machines. OR Spektrum, 15, 205-215.
  Mastrolilli, M., Gambardella, L. M. (2000). Effective neighbourhood
    functions for the flexible job shop problem. Journal of Scheduling,
    3(1), 3-20.
=========================================================================
