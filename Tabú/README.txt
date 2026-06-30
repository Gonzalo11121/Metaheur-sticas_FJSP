================================================================================
 BUSQUEDA TABU PARA EL FLEXIBLE JOB SHOP PROBLEM (FJSP)
================================================================================

Implementacion de la metaheuristica Busqueda Tabu (Tabu Search) para el
Flexible Job Shop Problem, minimizando el makespan (Cmax). El nucleo del
proyecto (parser, metaheuristica y driver de experimentos) esta escrito en
Python puro; openpyxl y matplotlib se usan solo para las salidas y graficos.

Benchmarks cubiertos:
  - Hurink, Jurisch y Thole (1994): edata, rdata, vdata (la01, la06, la11,
    la16, la21).
  - Brandimarte (1993): Mk01 .. Mk10.
  - Dauzere-Peres y Paulli (1997): 01a, 04a, 07a, 10a, 13a, 16a.

--------------------------------------------------------------------------------
 1. ESTRUCTURA DEL PROYECTO
--------------------------------------------------------------------------------

fjsp_taboo/
  fjsp_parser.py          Lector de instancias FJSP (formato de texto antiguo
                          de FJSPLib y archivos .fjs).
  taboo_search.py         Metaheuristica Busqueda Tabu aplicada al FJSP.
  run_experiments.py      Driver: recorre los benchmarks, ejecuta las
                          repeticiones y exporta los resultados.
  validar_instancias.py   Verifica la integridad de las instancias de Hurink.
  graficar.py             Genera graficos de gap%, makespan/std y convergencia.
  requirements.txt        Dependencias opcionales (openpyxl, matplotlib).
  README.txt              Este archivo.
  instancias/
    Hurink_Data/
      edata/  la01.txt la06.txt la11.txt la16.txt la21.txt
      rdata/  la01.txt la06.txt la11.txt la16.txt la21.txt
      vdata/  la01.txt la06.txt la11.txt la16.txt la21.txt
    Brandimarte_Data/
      Text/   Mk01.fjs .. Mk10.fjs
    dauzere/  01a.fjs 04a.fjs 07a.fjs 10a.fjs 13a.fjs 16a.fjs
  resultados/             Carpeta de salida (vacia inicialmente).

--------------------------------------------------------------------------------
 2. INSTALACION
--------------------------------------------------------------------------------

Requisito minimo: Python 3.8 o superior.

Dependencias opcionales (recomendadas) para las salidas y graficos:

    python3 -m pip install -r requirements.txt

Sin openpyxl, el driver omite resultados.xlsx y mantiene el resto de salidas.
matplotlib solo es necesario para graficar.py.

--------------------------------------------------------------------------------
 3. EJECUCION
--------------------------------------------------------------------------------

Corrida completa (5 repeticiones, 60 s por ejecucion):

    python3 run_experiments.py

Prueba rapida para validar el flujo:

    python3 run_experiments.py --tiempo 5 --reps 2

Validacion de las instancias de Hurink:

    python3 validar_instancias.py

Graficos (despues de run_experiments.py):

    python3 graficar.py

Tiempo total estimado de la corrida completa:
  31 instancias x 5 repeticiones x 60 s ~= 155 minutos.
Usa --tiempo y --reps para reducirlo en pruebas.

--------------------------------------------------------------------------------
 4. SALIDAS (carpeta resultados/)
--------------------------------------------------------------------------------

  resultados_reporte.txt   Reporte legible organizado por benchmark, con UB,
                           mejor, promedio, desviacion estandar, peor, gap% y
                           promedios de iteraciones y tiempo.

  resultados.xlsx          Libro con las hojas:
                             Resumen_General
                             Hurink_edata, Hurink_rdata, Hurink_vdata
                             Brandimarte, Dauzere
                             Rep_Hurink_edata, Rep_Hurink_rdata,
                             Rep_Hurink_vdata, Rep_Brandimarte, Rep_Dauzere
                           Las hojas Rep_ contienen el detalle por repeticion
                           (makespan, gap%, iteraciones y tiempo por semilla).

  configuracion.txt        Parametros del experimento, semillas, benchmarks,
                           parametros de la metaheuristica y hardware detectado
                           automaticamente (sistema, procesador, nucleos y RAM).

  graficos/                Imagenes generadas por graficar.py.

--------------------------------------------------------------------------------
 5. LA METAHEURISTICA (RESUMEN)
--------------------------------------------------------------------------------

  Representacion: (asignacion, secuencia).
    asignacion[j][o] = maquina que ejecuta la operacion o del trabajo j (ruteo).
    secuencia        = vector de IDs de trabajo con repeticion (codificacion
                       operation-based); cualquier permutacion es factible.
  Decodificador: horario activo con insercion en huecos.
  Vecindarios basados en la ruta critica:
    N1 - reasignar una operacion critica a otra maquina elegible.
    N2 - intercambiar dos operaciones adyacentes de trabajos distintos.
    N3 - reubicar una operacion critica algunas posiciones antes.
  Lista tabu con tenencia dinamica (~ raiz de n_operaciones) y criterio de
  aspiracion (se acepta un movimiento tabu si mejora el mejor global).
  Solucion inicial por multi-inicio con balanceo de carga, y diversificacion
  re-centrada en la mejor solucion archivada cuando la busqueda se estanca.

  Parametros configurables en taboo_search.resolver(...): limite_tiempo,
  tenencia_min/max, max_vecinos, iter_sin_mejora_diversif.

--------------------------------------------------------------------------------
 6. FORMATO DE ENTRADA
--------------------------------------------------------------------------------

  Primera linea : n_trabajos  n_maquinas  flexibilidad_promedio
  Una linea por trabajo: n_operaciones y, por cada operacion, n_opciones
  seguido de pares (maquina, duracion), con la maquina en base 1.

  El parser procesa el cuerpo como un flujo de enteros autodescriptivo, por lo
  que admite tanto los .txt de Hurink como los .fjs de Brandimarte y Dauzere.
================================================================================
