ALGORITMO GENETICO PARA EL JOB SHOP FLEXIBLE (FJSP)
Benchmarks: Hurink (1994), Brandimarte (1993), Dauzere-Peres & Paulli (1997)

DESCRIPCION: implementacion en Python de un Algoritmo Genetico (AG) para minimizar el
makespan (Cmax) en el Job Shop Flexible. El proyecto evalua la metaheuristica
sobre tres benchmarks de la literatura:

  Hurink, Jurisch & Thole (1994): subconjuntos edata, rdata y vdata,
    instancias la01, la06, la11, la16, la21 (15 instancias en total).
  Brandimarte (1993): Mk01 a Mk10 (10 instancias).
  Dauzere-Peres & Paulli (1997): 01a, 04a, 07a, 10a, 13a, 16a (6 instancias).

En total: 31 instancias x 5 repeticiones por instancia = 155 ejecuciones.

ESTRUCTURA DE CARPETAS

fjsp_ag/
  fjsp_parser.py      Lector de archivos de instancia (formato compartido
                      por los tres benchmarks).
  ag_fjsp.py          Metaheuristica: Algoritmo Genetico + decodificador
                      de schedule activo.
  experimentos.py     Driver del experimento: corre las 31 instancias x 5
                      repeticiones, exporta TXT, Excel y configuracion.
  requirements.txt    Unica dependencia externa (openpyxl).
  instancias/
    hurink/edata/      la01.txt, la06.txt, la11.txt, la16.txt, la21.txt
    hurink/rdata/      la01.txt, la06.txt, la11.txt, la16.txt, la21.txt
    hurink/vdata/      la01.txt, la06.txt, la11.txt, la16.txt, la21.txt
    brandimarte/       Mk01.fjs ... Mk10.fjs
    dauzere/           01a.fjs, 04a.fjs, 07a.fjs, 10a.fjs, 13a.fjs, 16a.fjs
  resultados/         Carpeta de salida (vacia hasta que se ejecute el
                      experimento; se completa al correr experimentos.py).

INSTALACION

Requiere Python 3.8 o superior. Instalar la unica dependencia externa:

    pip install -r requirements.txt

COMO EJECUTAR
Corrida completa (31 instancias x 5 repeticiones x 60 segundos, dura
aproximadamente 2 horas y media):

    cd fjsp_ag
    python experimentos.py

Prueba rapida para verificar que todo funciona antes de la corrida completa
(mismo numero de instancias y repeticiones, pero con presupuesto reducido a
3 segundos por ejecucion, dura unos minutos):

    python experimentos.py --rapido

ARCHIVOS DE SALIDA carpeta resultados
resultados_reporte.txt
    Reporte legible, organizado por benchmark (Hurink, Brandimarte,
    Dauzere), con la tabla de mejor, promedio, desviacion estandar, peor,
    gap% respecto al Upper Bound, iteraciones y tiempo promedio por
    instancia.

resultados.xlsx
    Libro de Excel con las siguientes hojas:
      Resumen_General      Resumen agregado de las 31 instancias.
      Hurink_edata         Resumen agregado del subconjunto edata.
      Hurink_rdata         Resumen agregado del subconjunto rdata.
      Hurink_vdata         Resumen agregado del subconjunto vdata.
      Brandimarte          Resumen agregado de Mk01-Mk10.
      Dauzere              Resumen agregado de 01a-16a.
      Rep_Hurink_edata      Detalle de cada una de las 5 repeticiones, edata.
      Rep_Hurink_rdata      Detalle de cada una de las 5 repeticiones, rdata.
      Rep_Hurink_vdata      Detalle de cada una de las 5 repeticiones, vdata.
      Rep_Brandimarte       Detalle de cada una de las 5 repeticiones, Brandimarte.
      Rep_Dauzere           Detalle de cada una de las 5 repeticiones, Dauzere.

configuracion.txt
  Parametros del experimento (repeticiones, semillas, presupuesto de
  tiempo), lista de benchmarks e instancias incluidas, y entorno de
  ejecucion detectado automaticamente (sistema operativo, arquitectura,
  procesador, nucleos logicos, version de Python).

METODOLOGIA EXPERIMENTAL
5 repeticiones por instancia, con semillas fijas de base 100 (100, 101, 102, 103, 104) para garantizar reproducibilidad.
-Presupuesto temporal uniforme de 60 segundos por ejecucion: todas las
instancias reciben el mismo tiempo de computo real, independientemente
de su tamano, para que la comparacion entre instancias sea justa.
Metricas registradas: mejor makespan, promedio, desviacion estandar
muestral (n-1), peor, gap% respecto al Upper Bound (del mejor y del
promedio), generaciones promedio, evaluaciones promedio y tiempo
promedio de ejecucion.

UPPER BOUNDS DE REFERENCIA
Hurink (edata):   la01=609  la06=800  la11=1071 la16=717  la21=835
Hurink (rdata):   la01=570  la06=799  la11=1071 la16=717  la21=833
Hurink (vdata):   la01=570  la06=799  la11=1071 la16=717  la21=800
Brandimarte:      Mk01=42 Mk02=32 Mk03=211 Mk04=81 Mk05=186
                  Mk06=86 Mk07=157 Mk08=523 Mk09=369 Mk10=296
Dauzere:          01a=2530 04a=2565 07a=2408 10a=2362 13a=2302 16a=2301

Fuente de los Upper Bounds: Mastrolilli, M. y Gambardella, L.M. (2000),
"Effective Neighborhood Functions for the Flexible Job Shop Problem",
y su apendice de resultados computacionales.
