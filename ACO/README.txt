PROYECTO FJSP - METAHEURISTICA ACO (MAX-MIN ANT SYSTEM)
=======================================================

Optimizacion por Colonia de Hormigas (ACO), variante MAX-MIN Ant System (MMAS),
aplicada al Flexible Job Shop Scheduling Problem (FJSP). El objetivo es minimizar
el makespan (Cmax).

El experimento se ejecuta sobre tres benchmarks:
  - Hurink (edata, rdata, vdata)  -> la01, la06, la11, la16, la21 en cada subset
  - Brandimarte                   -> Mk01 .. Mk10
  - Dauzere-Peres                 -> 01a, 04a, 07a, 10a, 13a, 16a

Cada instancia se resuelve con 5 repeticiones, semillas fijas 100..104 y un
presupuesto de 60 segundos por corrida.


ESTRUCTURA DE CARPETAS
----------------------
  fjsp_aco.py              Codigo principal (algoritmo + experimento + reportes)
  graficos.py              Genera los graficos a partir de los resultados.xlsx
  FJSP_ACO_Colab_v2.ipynb  Notebook para correr todo en Google Colab / Drive
  README.txt               Este archivo
  instancias/              Instancias organizadas por benchmark
      Hurink/edata/        la01.txt ... la21.txt
      Hurink/rdata/        ...
      Hurink/vdata/        ...
      Brandimarte/         Mk01.fjs ... Mk10.fjs
      Dauzere/             01a.fjs ... 16a.fjs
  resultados_hurink/       Salida del experimento sobre Hurink
  resultados_brandimarte/  Salida del experimento sobre Brandimarte
  resultados_dauzere/      Salida del experimento sobre Dauzere
  graficos/                Las 11 figuras generadas por graficos.py


INSTALACION
-----------
  pip install openpyxl psutil matplotlib


EJECUCION DEL EXPERIMENTO
--------------------------
  Experimento completo (los tres benchmarks, una sola carpeta de salida):
      python fjsp_aco.py

  Un benchmark a la vez (recomendado, mas seguro frente a desconexiones):
      python fjsp_aco.py --benchmarks Hurink      --out resultados_hurink
      python fjsp_aco.py --benchmarks Brandimarte --out resultados_brandimarte
      python fjsp_aco.py --benchmarks Dauzere     --out resultados_dauzere

  Parametros opcionales:
      --budget 60     segundos por corrida
      --reps 5        repeticiones por instancia
      --seed-base 100 semilla base (usa base, base+1, ...)
      --ants 30 --alpha 1.0 --beta 2.0 --rho 0.1
      --no-localsearch  desactiva la busqueda local

  Nota: el experimento completo son 31 instancias x 5 repeticiones x 60 s,
  aproximadamente 2.5 a 3 horas de computo.


SALIDAS DEL EXPERIMENTO (en cada carpeta resultados_*)
-------------------------------------------------------
  resultados_reporte.txt   Resumen por benchmark con metricas y gap% por grupo.
  configuracion.txt        Parametros, semillas y hardware detectado.
  resultados.xlsx          Libro con 12 hojas:
                             Resumen_General,
                             Hurink_edata, Hurink_rdata, Hurink_vdata,
                             Brandimarte, Dauzere,
                             Rep_Hurink_edata, Rep_Hurink_rdata,
                             Rep_Hurink_vdata, Rep_Brandimarte, Rep_Dauzere,
                             Convergencia.

  Metricas por instancia: mejor makespan, promedio, desviacion estandar, peor,
  gap% respecto al upper bound, iteraciones promedio y tiempo de ejecucion.
  gap% = (mejor - UB) / UB * 100

  La hoja Convergencia registra, para la repeticion 1 (seed base) de cada
  instancia, cada vez que el mejor makespan mejoro durante la corrida real:
  iteracion, tiempo transcurrido y makespan alcanzado.


UPPER BOUNDS DE REFERENCIA
--------------------------
  Hurink y Brandimarte/Dauzere segun Mastrolilli & Gambardella (2000).


GRAFICOS (paso posterior, una vez generados los resultados.xlsx)
-------------------------------------------------------------------
  python graficos.py --dirs resultados_hurink resultados_brandimarte resultados_dauzere

  (o si corriste todo a una sola carpeta de salida:  python graficos.py --dirs resultados )

  Lee directamente las hojas Resumen_General y Convergencia de cada
  resultados.xlsx; no vuelve a ejecutar el ACO.

  Produce en la carpeta graficos/ (11 figuras en total):
    3 de Gap%               : gap_Hurink.png, gap_Brandimarte.png, gap_Dauzere.png
    3 de Makespan +/- desv  : makespan_std_Hurink.png, makespan_std_Brandimarte.png,
                              makespan_std_Dauzere.png
    5 de convergencia       : convergencia_Hurink_edata.png, convergencia_Hurink_rdata.png,
                              convergencia_Hurink_vdata.png, convergencia_Brandimarte.png,
                              convergencia_Dauzere.png


EJECUCION EN GOOGLE COLAB
--------------------------
  Abrir FJSP_ACO_Colab_v2.ipynb desde Google Drive (carpeta del proyecto) y
  ejecutar las celdas en orden: conectar Drive, entrar a la carpeta, instalar
  dependencias, verificar instancias, prueba rapida, experimento completo y
  generacion de graficos.
