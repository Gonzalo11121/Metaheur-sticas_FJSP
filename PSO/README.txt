# FJSP con PSO — Job Shop Flexible resuelto con Enjambre de Partículas

Resolución del **Flexible Job Shop Scheduling Problem (FJSP)** minimizando el
**makespan (Cmax)** sobre el benchmark de **Hurink (1994)** (subconjuntos
`edata`, `rdata`, `vdata`), usando una metaheurística de **Optimización por
Enjambre de Partículas (PSO)**.

Implementación en **Python puro** (solo librería estándar: `random`, `time`,
`math`, `csv`, `statistics`, `datetime`, `os`). Sin numpy ni dependencias
externas.

---

## Archivos

| Archivo | Contenido |
|---|---|
| `fjsp_pso.py` | Núcleo: parser de instancias Hurink + decodificador + PSO. |
| `run_experiments.py` | Script de experimentos (15 instancias × 5 semillas) + exportación CSV/TXT. |
| `instancias/` | Las 15 instancias (`edata/`, `rdata/`, `vdata/` × `la01,la06,la11,la16,la21`). |
| `resultados/` | Salidas de ejemplo (generadas con presupuesto corto a modo de demostración). |

---

## Cómo ejecutar

Corrida completa del experimento (15 instancias × 5 repeticiones):

```bash
python3 run_experiments.py
```

Genera en `resultados/` tres archivos con *timestamp*:

* `fjsp_pso_detalle_<fecha>.csv` — una fila por ejecución (instancia, semilla,
  makespan, iteraciones, tiempo, gap%).
* `fjsp_pso_resumen_<fecha>.csv` — una fila por instancia (best, mean, std,
  worst, gap_best%, gap_mean%, iteraciones medias, tiempo medio).
* `fjsp_pso_reporte_<fecha>.txt` — reporte legible con configuración y tablas.

Probar una sola instancia rápidamente:

```bash
python3 fjsp_pso.py instancias/edata/la01.txt
```

### Presupuesto temporal (importante)

El enunciado pide *"60 segundos por instancia"*. En `run_experiments.py` se
interpreta como **60 s por ejecución** (cada una de las 5 repeticiones), que es
la práctica estándar al evaluar metaheurísticas. La corrida completa tarda por
tanto ≈ 15 × 5 × 60 s ≈ **75 minutos**.

Si tu enunciado exige 60 s repartidos entre las 5 repeticiones, cambia en
`run_experiments.py`:

```python
TIME_BUDGET = 12.0   # 60 s / 5 repeticiones
```

Las semillas son fijas (`100, 101, 102, 103, 104`), así que los resultados son
**totalmente reproducibles**.

---

## Diseño de la metaheurística

**Representación de la partícula** (vector continuo de dimensión `2N`, con `N` =
número total de operaciones):

* **Mitad MS (Machine Selection)** — una clave por operación en `[0,1)`. Para
  una operación con `L` máquinas alternativas, se elige la alternativa
  `floor(clave · L)`. Resuelve el subproblema de **ruteo**.
* **Mitad OS (Operation Sequence)** — claves aleatorias (*random keys*). Al
  ordenar los "slots" por su clave se obtiene una secuencia de jobs;
  la k-ésima aparición del job *j* es su k-ésima operación. Esta codificación
  basada en operaciones **garantiza la factibilidad de precedencia**. Resuelve
  el subproblema de **secuenciación**.

**Decodificador** — construye una planificación *activa* insertando cada
operación en el hueco factible más temprano de su máquina (*left-shifting*).

**PSO** — actualización estándar de velocidad/posición con inercia `w`
decreciente linealmente y coeficientes cognitivo/social `c1`, `c2`; *clamping*
de velocidad.

**Componente memético** (clave para la calidad) — cada vez que mejora el mejor
global se refina con búsqueda local:

* **Búsqueda local de grafo / bloque crítico** — calcula cabezas y colas sobre
  el grafo disyuntivo, identifica las operaciones críticas (`head+tail=Cmax`) y
  prueba *swaps* dentro de los bloques críticos (vecindario N5 clásico) y
  reasignación de máquina de operaciones críticas.
* **Búsqueda local de ruteo** (solo en instancias flexibles) — reasigna cada
  operación flexible a sus máquinas alternativas para descongestionar.

Cuando el enjambre se estanca, se **reinyecta diversidad** re-aleatorizando las
peores partículas sin perder el mejor global.

---

## Sobre los resultados esperados (lectura honesta)

* Instancias de **baja flexibilidad fáciles** (p. ej. `edata/la01`): el método
  alcanza el óptimo conocido o se queda a ~2 %.
* Instancias **flexibles** (`rdata`, `vdata`): típicamente dentro de ~2–10 %.
* Instancias **10×10 difíciles** (`la16`, `la21`, sobre todo en `edata`): el gap
  es mayor (puede rondar 15–30 %). Esto es esperable: por ejemplo, en
  `edata/la16` la cota inferior por job ya **iguala** al UB (717), de modo que
  alcanzar ese valor exige una secuenciación casi óptima del job más largo,
  algo muy difícil para una metaheurística de propósito general en 60 s. La
  métrica **gap%** existe precisamente para cuantificar esta distancia.

Para el informe individual conviene analizar: convergencia, efecto de la
flexibilidad (edata < rdata < vdata) sobre la calidad, sensibilidad a los
hiperparámetros del PSO y dónde la búsqueda local aporta más.
