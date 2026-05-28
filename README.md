# Slotting Optimization Engine

**Motor de análisis y simulación para optimización de slotting en centros de distribución.**

---

## Introducción — ¿Qué es esto y para qué sirve?

Imaginá un centro de distribución con miles de productos (SKUs), cientos de estanterías (ubicaciones) y decenas de zonas. Todos los días, los pickers caminan kilómetros para armar pedidos. Algunos SKUs de alta demanda están lejos del despacho. Otros, que casi no se venden, ocupan espacios privilegiados. Algunas zonas están al límite de capacidad mientras otras tienen espacio de sobra.

**Este proyecto te ayuda a poner orden en ese caos.** No mueve productos automáticamente ni reemplaza a tu equipo operativo. En cambio, **analiza**, **prioriza** y **simula** para que vos — con criterio humano — puedas tomar mejores decisiones sobre dónde ubicar cada SKU.

En concreto, el motor te permite responder preguntas como:

| Pregunta | Lo que el motor te devuelve |
|---------|---------------------------|
| ¿Qué SKUs de alta demanda están mal ubicados? | Una lista ordenada con scores |
| ¿Qué zonas están sobrecargadas? | Diagnóstico de capacidad por zona |
| ¿Conviene priorizar demanda o capacidad primero? | Comparación de escenarios lado a lado |
| ¿Qué SKU debería ir a qué zona? | Asignación candidata SKU→zona |
| ¿Cuánto cambiarían las distancias si muevo estos SKUs? | Simulación de impacto en km y tiempo |
| ¿Mejoraría el balance entre zonas? | Coeficiente Gini antes/después |
| ¿Cuántas órdenes más por turno podría procesar? | Estimación de throughput |

> **⚠️ IMPORTANTE:** Todo lo que produce este motor son **recomendaciones analíticas** sobre datos sintéticos. Los pesos, umbrales y supuestos están marcados como `inferred / pending confirmation` (inferidos / pendientes de confirmación). No son órdenes operativas ni decisiones automáticas.

---

## ¿Para quién es esta herramienta?

| Perfil | Qué puede hacer con esto |
|--------|------------------------|
| **Jefe de depósito / Operaciones** | Entender qué zonas están sobrecargadas, qué SKUs conviene revisar primero, y cuantificar el impacto potencial de cambios |
| **Analista de datos / Supply Chain** | Ejecutar scripts, explorar CSVs de salida, ajustar pesos y umbrales, preparar informes |
| **Estudiante / Aprendiz** | Aprender cómo funciona el slotting y la optimización de depósitos con datos ficticios |
| **Desarrollador** | Extender el código, agregar nuevos escenarios de simulación, conectar datos reales |

No necesitás saber programación para **leer los resultados** (son CSVs que se abren en Excel). Pero sí necesitás usar la terminal (PowerShell / bash) para ejecutar los scripts.

---

## Alcance actual — ¿Qué está implementado?

El proyecto se divide en **6 fases** que se ejecutan en secuencia. Cada fase toma los outputs de la anterior.

| Fase | Nombre | ¿Qué hace? | Estado |
|------|--------|-----------|--------|
| 1 | Datos y features | Genera datos sintéticos, valida contratos y construye señales analíticas | ✅ Completa |
| 1.5 | Interfaz técnica (Streamlit) | UI visual para inspeccionar outputs procesados | ✅ Completa |
| 2 | Diagnósticos descriptivos | Marca problemas por SKU, ubicación, zona y categoría | ✅ Completa |
| 3 | Scoring y priorización | Ordena oportunidades para revisión humana con pesos transparentes | ✅ Completa |
| 4 | Comparación de escenarios | Compara lentes analíticos: demanda primero, capacidad primero o balanceado | ✅ Completa |
| 5 | Asignación matemática | Asigna SKU→zona candidata minimizando costo proxy; no ejecuta movimientos | ✅ Completa |
| 6 | Simulación operativa | Simula distancia, balance de carga y throughput post-optimización | ✅ Completa (3 escenarios) |

### ¿Qué NO está implementado? (alcance futuro)

- Conexión con WMS o ERP real
- Autenticación de usuarios
- Interfaz de negocio completa (solo hay un Streamlit técnico)
- Ejecución automática de movimientos de SKU
- Garantía de factibilidad física a nivel de ubicación exacta
- Despliegue en producción (CI/CD, server, etc.)

---

## Requisitos técnicos

| Requisito | Detalle |
|-----------|---------|
| **Python** | 3.11 o superior (probado en 3.13.5) |
| **Sistema** | Windows, macOS o Linux |
| **Terminal** | PowerShell (Windows) o bash (Mac/Linux) |
| **Git** | Opcional, para clonar el repositorio |
| **Memoria RAM** | Mínimo 4 GB (8 GB recomendado) |
| **Disco** | ~100 MB para el proyecto y datos |

No necesitás instalar nada más que Python. Las dependencias se instalan automáticamente con `pip`.

---

## Guía completa paso a paso

Esta guía está pensada para **cualquier persona**, aunque nunca haya usado Python o una terminal. Cada paso explica qué hace, por qué es necesario y cómo verificar que funcionó.

### Paso 1 — Obtener el código

Si ya tenés la carpeta del proyecto, abrí una terminal en esa carpeta y saltá al Paso 2.

Si no, abrí una terminal y ejecutá:

```bash
git clone https://github.com/harrysxavio/optimizacion.git
cd optimizacion
```

> **¿No tenés Git?** También podés descargar el código como ZIP desde GitHub y extraerlo en una carpeta.

### Paso 2 — Crear el entorno virtual (recomendado)

El entorno virtual aísla las dependencias de este proyecto del resto de tu sistema.

**En Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**En Mac / Linux (bash):**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

> Vas a ver `(.venv)` al inicio de la línea en tu terminal. Eso indica que el entorno está activo.

### Paso 3 — Instalar el paquete

```powershell
pip install -e ".[dev]"
```

Esto instala todo lo necesario: pandas (tablas), numpy (números), ruff (calidad de código), pytest (tests), etc.

**Verificá que funcionó:**

```powershell
python -c "import slotting_optimization_engine; print('OK')"
```

Si ves `OK`, todo está listo.

### Paso 4 — Generar datos sintéticos

El proyecto usa **datos ficticios** para que puedas probar sin riesgo. No necesitás datos reales de tu depósito.

```powershell
python scripts/generate_sample_data.py
```

Esto crea ~13,000 filas de datos en `data/synthetic/`:

| Archivo | Qué contiene | Cantidad |
|---------|-------------|----------|
| `skus.csv` | Catálogo de SKUs con categoría, peso, volumen | 500 SKUs |
| `zones.csv` | Zonas del depósito con distancia a despacho | 10 zonas |
| `locations.csv` | Ubicaciones (estantes) con zona y capacidad | 200 ubicaciones |
| `inventory.csv` | Stock actual por SKU y ubicación | ~700 registros |
| `orders.csv` | Encabezados de pedidos | 2,000 órdenes |
| `order_lines.csv` | Líneas de detalle de cada pedido | ~10,000 líneas |

### Paso 5 — Validar los datos

Revisa que todos los IDs, tipos de datos y reglas estén correctos.

```powershell
python scripts/run_data_validation.py
```

> Si ves `All validations passed`, los datos están listos.

### Paso 6 — Construir features analíticas

Calcula señales como: ¿cuánto se pide cada SKU?, ¿qué tan llenas están las zonas?, ¿qué SKUs están lejos del despacho?

```powershell
python scripts/build_features.py
```

**Outputs:** `data/processed/slotting_features.parquet`, `location_utilization.csv`, `zone_utilization.csv`

### Paso 7 — Diagnosticar problemas del depósito

Marca qué SKUs, ubicaciones y zonas tienen problemas detectables por reglas simples.

```powershell
python scripts/run_diagnostics.py
```

**Qué produjo:** 5 CSVs con flags como:
- SKUs de alta demanda que están lejos del despacho
- SKUs de movimiento lento que ocupan zonas premium
- Zonas con capacidad al límite
- Categorías dispersas entre muchas zonas

### Paso 8 — Priorizar oportunidades

Ordena los problemas detectados por importancia para que sepas por dónde empezar a revisar.

```powershell
python scripts/run_scoring.py
```

**Output principal:** `priority_recommendation_queue.csv` — una cola ordenada de "revisá esto primero".

### Paso 9 — Comparar escenarios

Mirá el mismo depósito desde 4 ángulos distintos:

- **Baseline:** prioridad sin cambios
- **Demanda primero:** ¿qué pasa si priorizo SKUs de alta demanda?
- **Capacidad primero:** ¿qué pasa si primero libero espacio?
- **Revisión balanceada:** ¿qué pasa si balanceo ambos?

```powershell
python scripts/run_scenarios.py
```

### Paso 10 — Optimizar asignación de SKUs

Este es el paso más avanzado: asigna SKUs prioritarios a zonas candidatas usando un modelo matemático que minimiza un costo calculado (demanda × distancia × capacidad × oportunidad).

```powershell
python scripts/run_optimization.py
```

> ⚠️ **Esto es un prototipo.** No ejecuta movimientos ni garantiza factibilidad física. Es una recomendación analítica.

### Paso 11 — Simular el impacto operativo

Una vez que tenés la asignación del paso anterior, simulá cuánto cambiarían:

- **Distancias** recorridas por los pickers (km por día)
- **Balance de carga** entre zonas (coeficiente Gini)
- **Throughput** estimado (órdenes por turno)

```powershell
# Todos los escenarios juntos
python scripts/run_simulation.py

# Solo distancia (más rápido)
python scripts/run_simulation.py --scenario-a
```

**Resultado típico (con datos sintéticos):**
- 12 SKUs optimizados
- ~89% de reducción en distancia de viaje
- Mejora en el balance Gini (0.19 → 0.16)
- ~53× más throughput estimado

### Paso 12 — Próximos pasos

Una vez que entiendas el flujo completo, podés:

1. Reemplazar los datos sintéticos por datos reales de tu depósito
2. Ajustar los pesos y umbrales a tu operación (están marcados como `inferred`)
3. Usar los CSVs como insumo para decisiones con tu equipo operativo
4. Explorar el código fuente para entender cada módulo

---

## Las 6 fases en detalle

### Fase 1 — Datos sintéticos y features analíticas

```
┌────────────────────────────────────────────────────────────┐
│                  FASE 1: DATOS Y FEATURES                   │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  Generador → Validador → Cargador → Constructor Features   │
│  (numpy)    (pandera)   (pandas)   (demanda, utilización,  │
│                                      scores de alineación)  │
│                                                             │
│  Outputs: slotting_features.parquet                         │
│           location_utilization.csv                          │
│           zone_utilization.csv                              │
│                                                             │
│  $ python scripts/generate_sample_data.py                   │
│  $ python scripts/run_data_validation.py                    │
│  $ python scripts/build_features.py                         │
└────────────────────────────────────────────────────────────┘
```

**Qué aprendés:** Este paso crea un "mundo ficticio" de datos para practicar sin tocar información real. Los features son señales básicas como "¿cuánto se pide este SKU?" o "¿qué tan llenas están las zonas?".

---

### Fase 1.5 — Interfaz técnica (Streamlit)

Además de los scripts de terminal, el proyecto incluye una **interfaz visual técnica** construida con [Streamlit](https://streamlit.io). Te permite explorar los outputs procesados sin tener que leer CSVs a cada rato.

**Cómo ejecutarla:**

```powershell
pip install -e ".[streamlit]"
streamlit run src/slotting_optimization_engine/app/streamlit_app.py
```

**Qué podés ver:**
- Tablas de SKUs con features analíticas
- Utilización de ubicaciones y zonas
- Visualizaciones básicas (barras, heatmaps)

> ⚠️ **Importante:** Esta UI es técnica y descriptiva. No es una aplicación de negocio final. Muestra los datos procesados para inspección, no para tomar decisiones operativas automáticas.

**Prerequisitos:** Haber ejecutado los scripts de Fase 1 (generar, validar y construir features).

---

### Fase 2 — Diagnósticos descriptivos

```
┌────────────────────────────────────────────────────────────┐
│                FASE 2: DIAGNÓSTICOS                         │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  Entradas: slotting_features.parquet                        │
│            location_utilization.csv                         │
│            zone_utilization.csv                             │
│                                                             │
│  Reglas: ¿SKU de alta demanda lejos de zona prioritaria?    │
│          ¿Slow mover en zona premium?                       │
│          ¿Zona con capacidad al límite?                      │
│          ¿Categoría muy dispersa?                           │
│                                                             │
│  Outputs: slotting_diagnostics.csv (1 fila por SKU)         │
│           location_diagnostics.csv (1 fila por ubicación)   │
│           zone_diagnostics.csv (1 fila por zona)            │
│           category_diagnostics.csv (1 fila por categoría)   │
│           diagnostic_summary.csv (conteo de problemas)      │
│                                                             │
│  $ python scripts/run_diagnostics.py                        │
└────────────────────────────────────────────────────────────┘
```

**Qué aprendés:** Es como un "check-up" del depósito. No dice qué mover, solo marca qué se ve raro o merece atención. Los pesos están marcados como `inferred / pending confirmation` porque son supuestos, no reglas confirmadas.

---

### Fase 3 — Scoring y priorización

```
┌────────────────────────────────────────────────────────────┐
│              FASE 3: SCORING Y COLA DE REVISIÓN             │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  Entradas: slotting_diagnostics.csv                         │
│            zone_diagnostics.csv                             │
│            category_diagnostics.csv                         │
│                                                             │
│  Pesos transparentes:                                       │
│  • Demanda: 30%    • Distancia: 25%                         │
│  • Capacidad: 25%   • Oportunidad: 20%                     │
│  (pesos inferidos, pendientes de confirmación)             │
│                                                             │
│  Ordena de mayor a menor score → cola de revisión humana    │
│                                                             │
│  Outputs: slotting_opportunity_scores.csv                   │
│           priority_recommendation_queue.csv (top-N)         │
│           scoring_summary.csv (métricas y configuración)    │
│                                                             │
│  $ python scripts/run_scoring.py                            │
└────────────────────────────────────────────────────────────┘
```

**Qué aprendés:** Arma una "lista de tareas ordenada" para que un humano sepa por dónde empezar a revisar. **No optimiza**, solo prioriza. Los pesos son supuestos a confirmar con expertos del negocio.

---

### Fase 4 — Comparación de escenarios

```
┌────────────────────────────────────────────────────────────┐
│            FASE 4: ESCENARIOS WHAT-IF                       │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  Entradas: slotting_opportunity_scores.csv                  │
│            priority_recommendation_queue.csv                │
│                                                             │
│  Escenarios:                                                │
│  • Baseline:       "si no cambiamos nada"                   │
│  • Demanda 1°:     "priorizar SKUs de alta demanda"        │
│  • Capacidad 1°:   "primero liberar espacio"               │
│  • Balanceado:     "mezcla de ambos"                        │
│                                                             │
│  Outputs: scenario_comparison.csv (top-N por escenario)     │
│           scenario_action_mix.csv (mezcla de acciones)      │
│           scenario_summary.csv (métricas comparables)       │
│                                                             │
│  $ python scripts/run_scenarios.py                          │
└────────────────────────────────────────────────────────────┘
```

**Qué aprendés:** Es como mirar el mismo depósito desde 4 ángulos diferentes. No dice cuál es "el mejor", solo muestra qué cambia cuando cambian las prioridades. Útil para debates con el equipo operativo.

---

### Fase 5 — Asignación matemática controlada

```
┌────────────────────────────────────────────────────────────┐
│            FASE 5: ASIGNACIÓN SKU → ZONA                    │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  Entradas: priority_recommendation_queue.csv (Phase 3)     │
│            slotting_diagnostics.csv (Phase 2)               │
│            scenario_comparison.csv (Phase 4)                │
│            skus.csv / zones.csv (Phase 1)                   │
│                                                             │
│  Proceso:                                                   │
│  1. Toma top-N SKUs de la cola de priorización             │
│  2. Expande zonas en slots lógicos (A → A.1, A.2, A.3)     │
│  3. Calcula costo SKU×zona (demanda + distancia + cap.)    │
│  4. Resuelve asignación de menor costo total                │
│     (usa SciPy si está instalado, o fallback greedy)        │
│                                                             │
│  Outputs: optimization_assignments.csv (1 assign por SKU)   │
│           optimization_summary.csv (método, costo, cant.)   │
│           optimization_cost_matrix.csv (costo transparente) │
│                                                             │
│  ⚠️ PROTOTIPO: No ejecuta movimientos, no valida           │
│     factibilidad física, no conecta WMS/ERP.               │
│                                                             │
│  $ python scripts/run_optimization.py                       │
└────────────────────────────────────────────────────────────┘
```

**Qué aprendés:** Es la primera vez que el motor "decide" algo, pero es una decisión **analítica**, no operativa. Asigna SKUs a zonas candidatas minimizando un costo matemático. **No es una orden de mover productos.** Si SciPy no está instalado, usa un fallback greedy determinístico (siempre da el mismo resultado).

---

### Fase 6 — Simulación de impacto operativo

```
┌────────────────────────────────────────────────────────────┐
│         FASE 6: SIMULACIÓN DE IMPACTO OPERACIONAL           │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  Entradas: orders.csv / order_lines.csv  (Phase 1)         │
│            zones.csv / locations.csv / inventory.csv        │
│            optimization_assignments.csv (Phase 5)           │
│                                                             │
│  Sub-simulaciones:                                          │
│  • Travel:   distancia antes/después por orden             │
│  • Workload: picks por zona + Gini coefficient             │
│  • Throughput: órdenes/turno (optimista/balanceado/cons.)   │
│                                                             │
│  Outputs: simulation_summary.csv (métricas clave)           │
│           travel_aggregate.csv (dist/tiempo)                │
│           zone_impact.csv (picks + Gini)                    │
│           throughput_scenarios.csv (órdenes/turno)         │
│           order_detail.csv (detalle por orden)              │
│                                                             │
│  ⚠️ PROTOTIPO: No es modelo de ingeniería certificado,     │
│     no sustituye estudios de tiempos y movimientos.         │
│                                                             │
│  $ python scripts/run_simulation.py                         │
│  $ python scripts/run_simulation.py --scenario-a            │
└────────────────────────────────────────────────────────────┘
```

**Qué aprendés:** Es la primera vez que el motor "estima" el efecto de los cambios. No dice qué mover — ya lo decidió Fase 5 — sino **cuánto cambiarían** las caminatas diarias, el balance entre zonas y las órdenes procesadas por turno si esos movimientos se ejecutaran. **Es una estimación ilustrativa, no una predicción certificada.**

---

## Comandos de un vistazo

| Comando | Qué hace | Fase |
|---------|----------|------|
| `python scripts/generate_sample_data.py` | Crea datos sintéticos | 1 |
| `python scripts/run_data_validation.py` | Valida contratos y reglas | 1 |
| `python scripts/build_features.py` | Calcula features analíticas | 1 |
| `streamlit run src/.../streamlit_app.py` | Abre UI visual técnica | 1.5 |
| `python scripts/run_diagnostics.py` | Diagnostica problemas | 2 |
| `python scripts/run_scoring.py` | Prioriza oportunidades | 3 |
| `python scripts/run_scenarios.py` | Compara escenarios | 4 |
| `python scripts/run_optimization.py` | Asigna SKUs a zonas | 5 |
| `python scripts/run_simulation.py` | Simula impacto operativo | 6 |
| `python scripts/run_simulation.py --scenario-a` | Solo simula distancias | 6 |
| `python -m pytest -v` | Ejecuta tests (~257) | — |
| `python -m ruff check src tests scripts` | Revisa calidad de código | — |

### Ejecutar todo de una

```powershell
python scripts/generate_sample_data.py
python scripts/run_data_validation.py
python scripts/build_features.py
python scripts/run_diagnostics.py
python scripts/run_scoring.py
python scripts/run_scenarios.py
python scripts/run_optimization.py
python scripts/run_simulation.py

# Verificar
python -m pytest -v
python -m ruff check src tests scripts
```

---

## Outputs — qué produce cada fase

Después de ejecutar las 6 fases, la carpeta `data/processed/` contiene:

| Archivo | Fase | Qué contiene |
|---------|------|-------------|
| `slotting_features.parquet` | 1 | Tabla ancha con features por SKU |
| `location_utilization.csv` | 1 | % de utilización por ubicación |
| `zone_utilization.csv` | 1 | Resumen de utilización por zona |
| `slotting_diagnostics.csv` | 2 | Flags descriptivos por SKU |
| `location_diagnostics.csv` | 2 | Diagnóstico de ubicaciones |
| `zone_diagnostics.csv` | 2 | Diagnóstico de zonas |
| `category_diagnostics.csv` | 2 | Indicadores de categorías |
| `diagnostic_summary.csv` | 2 | Conteo de problemas detectados |
| `slotting_opportunity_scores.csv` | 3 | Scores de oportunidad por acción |
| `priority_recommendation_queue.csv` | 3 | **Cola ordenada de revisión** |
| `scoring_summary.csv` | 3 | Métricas y configuración del scoring |
| `scenario_comparison.csv` | 4 | Top-N recalculado por escenario |
| `scenario_action_mix.csv` | 4 | Mezcla de acciones por escenario |
| `scenario_summary.csv` | 4 | Métricas comparables entre escenarios |
| `optimization_assignments.csv` | 5 | **Asignación SKU→zona candidata** |
| `optimization_summary.csv` | 5 | Método usado y costo total |
| `optimization_cost_matrix.csv` | 5 | Matriz de costos transparente |
| `simulation_summary.csv` | 6 | Métricas resumen de simulación |
| `simulation_travel_aggregate.csv` | 6 | Distancia/tiempo agregados |
| `simulation_zone_impact.csv` | 6 | Picks por zona + Gini |
| `simulation_throughput_scenarios.csv` | 6 | Órdenes/turno estimadas |
| `simulation_order_detail.csv` | 6 | Desglose por orden individual |

---

## Frontend (Streamlit) — Cómo probar las herramientas visualmente

**Sí, el proyecto tiene un frontend técnico.** Está construido con Streamlit y te permite explorar los outputs sin leer CSVs crudos.

**Para ejecutarlo:**

```powershell
# 1. Instalar dependencia opcional
pip install -e ".[streamlit]"

# 2. Ejecutar (requiere outputs de Fase 1)
streamlit run src/slotting_optimization_engine/app/streamlit_app.py
```

**Qué vas a ver:**
- Tablas interactivas de SKUs con features
- Utilización por ubicación y zona
- Visualizaciones básicas (barras, heatmaps de zonas)
- Filtros para explorar los datos

**Prerequisito:** Haber ejecutado los scripts de Fase 1 (generar datos, validar, construir features).

> ⚠️ **Nota importante:** Esta UI es técnica, no una aplicación de negocio final. Está pensada para que analistas y desarrolladores inspeccionen los datos procesados. No incluye autenticación, permisos ni workflows de aprobación.

---

## Limitaciones importantes — Qué NO hacer con esto

- ❌ **No muevas SKUs automáticamente** basándote en los CSVs de salida
- ❌ **No trates un score alto como una orden operativa** — es una recomendación, no una instrucción
- ❌ **No interpretes la asignación de Fase 5 como solución óptima real** — es un prototipo matemático acotado
- ❌ **No cambies layout, dotación o capacidad** sin validar con operación real
- ❌ **No uses estos pesos como política de negocio** hasta confirmarlos con expertos del depósito
- ❌ **No asumas que la simulación de Fase 6 es un estudio certificado** — no reemplaza un estudio de tiempos y movimientos
- ❌ **No ejecutes movimientos de SKU automáticamente** usando `optimization_assignments.csv`

Los datos actuales son **sintéticos** y los umbrales/pesos están marcados como `inferred / pending confirmation`. Eso es **deliberado**: sirve para aprender y auditar la lógica antes de convertirla en decisión de negocio.

---

## Conceptos clave (glosario)

| Término | Significado |
|---------|-------------|
| **SKU** | Stock Keeping Unit — producto individual que se almacena y se vende |
| **Slotting** | Disciplina de decidir dónde ubicar cada SKU dentro del depósito |
| **Zona** | Área del depósito (ej: picking, reserve, cross-dock, devoluciones) |
| **Ubicación** | Estante, rack o posición específica dentro de una zona |
| **Peso inferido (`inferred`)** | Valor estimado, no confirmado con operación real |
| **Pendiente de confirmación (`pending confirmation`)** | Requiere validación con datos o expertos reales |
| **Gini coefficient** | Medida de qué tan balanceada está la carga entre zonas (0 = equilibrio perfecto, 1 = concentración total) |
| **Throughput** | Cantidad de órdenes que se pueden procesar por unidad de tiempo (ej: por turno) |
| **Feature** | Señal analítica calculada a partir de datos crudos (ej: demanda diaria promedio por SKU) |
| **Fallback greedy** | Algoritmo simple que asigna SKUs uno por uno al mejor slot disponible sin mirar el quadro completo |
| **Parquet** | Formato de archivo columnar, más eficiente que CSV para datos tabulares grandes |

---

## Estructura del proyecto

```
slotting-optimization-engine/
├── README.md                      # Este archivo
├── pyproject.toml                 # Definición del paquete y dependencias
├── data/
│   ├── synthetic/                 # Datos generados (Phase 1)
│   └── processed/                 # Outputs de todas las fases
├── docs/
│   ├── master_plan.md             # Plan maestro y trazabilidad
│   ├── architecture_sdd.md        # Arquitectura técnica
│   ├── data_contract.md           # Contratos de datos y validación
│   ├── roadmap.md                 # Roadmap por fase
│   ├── phase_notes/               # Documentación detallada por fase
│   └── phase_logs/                # Logs de terminal de ejecución
├── scripts/                       # Scripts CLI de cada fase
├── src/
│   └── slotting_optimization_engine/
│       ├── config/                # Configuración central
│       ├── data/                  # Generación, carga, validación
│       ├── domain/                # Conceptos del dominio (SKU, zona, etc.)
│       ├── features/              # Construcción de features analíticas
│       ├── diagnostics/           # Diagnósticos descriptivos (Fase 2)
│       ├── scoring/               # Scoring y priorización (Fase 3)
│       ├── scenarios/             # Comparación de escenarios (Fase 4)
│       ├── optimization/          # Asignación matemática (Fase 5)
│       ├── simulation/            # Simulación operativa (Fase 6)
│       ├── reporting/             # Reportes y resúmenes
│       └── app/                   # Streamlit UI técnica (Fase 1.5)
├── tests/
│   ├── unit/                      # Tests unitarios
│   └── integration/               # Tests de integración (futuro)
└── notebooks/                     # Notebooks exploratorios
```

---

## Documentación relacionada

| Documento | Propósito |
|-----------|----------|
| `docs/master_plan.md` | Plan maestro del proyecto, alcance, decisiones y trazabilidad |
| `docs/architecture_sdd.md` | Arquitectura técnica, responsabilidades de módulos, flujo de datos |
| `docs/data_contract.md` | Entidades, campos, reglas de validación |
| `docs/roadmap.md` | Roadmap fases 0–7 con estado de implementación |
| `docs/phase_notes/phase_*` | Notas detalladas de cada fase (decisiones, outputs, evidencia) |
| `docs/phase_logs/phase_*` | Logs de terminal con comandos ejecutados y resultados |

---

## Verificación y calidad de código

```powershell
# Ejecutar todos los tests (~257)
python -m pytest -v

# Revisar calidad de código
python -m ruff check src tests scripts

# Verificar tipos (opcional, requiere mypy)
python -m mypy src --ignore-missing-imports
```

Todos los tests deben pasar antes de considerar los outputs como válidos para análisis.
