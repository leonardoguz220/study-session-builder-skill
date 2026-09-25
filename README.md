# Study Session Builder

Skill para organizar el tiempo de estudio antes de un examen. Recibe una materia,
una fecha, temas y disponibilidad diaria; genera un **plan Markdown con sesiones,
repaso y descansos incluidos en el presupuesto**. Las prioridades son opcionales y
solo proceden de lo que indique explícitamente el estudiante.

Proyecto académico con Python 3.10+, biblioteca estándar, 25 pruebas automáticas y
una demo que ejecuta un caso exitoso y un caso inválido.

## Problema que resuelve

Tener una lista de temas y varios días libres no basta para saber cuánto estudiar
cada día. Esta skill convierte esos datos en una distribución concreta y advierte
si algún tema recibe muy poco tiempo.

## Funcionamiento y flujo completo

1. La persona indica datos reales; el agente consulta la skill y prepara el JSON.
2. Se validan los campos, fechas, límites y prioridades.
3. Se carga `references/study_rules.json` y se reservan los descansos diarios.
4. Del tiempo neto de estudio se reserva el 20 % para repaso (configurable).
5. Se reparte el contenido: peso 2 para prioridades explícitas y 1 para otros temas.
   Sin prioridades, el reparto es equilibrado, con diferencia máxima de un minuto.
6. Se organizan sesiones sin superar el máximo ni programar el día del examen.
7. Se abre `assets/study-plan-template.md` y se genera `output/study-plan.md`.
8. Se revisa y entrega el resultado con sus advertencias.

La suma de contenido, repaso y descansos coincide exactamente con la disponibilidad.
Los minutos se reparten mediante restos mayores. El repaso se coloca al final del
plan. Una sesión puede contener varias actividades, sin pausas adicionales entre
esas actividades. No se inventan horas de inicio.

## Estructura

```text
.codex/skills/study-session-builder/
├── SKILL.md
├── agents/openai.yaml
├── scripts/
│   ├── build_schedule.py
│   ├── validate_input.py
│   └── demo.py
├── assets/study-plan-template.md
└── references/
    ├── input-format.md
    ├── study-method.md
    └── study_rules.json
examples/
├── valid_input.json
├── invalid_input.json
└── expected-study-plan.md
tests/test_skill.py
evidence/
├── README.md
└── verification.txt
output/.gitkeep
README.md
.gitignore
```

## Requisitos

- Python **3.10 o posterior**, con acceso de escritura a la carpeta de salida.
- Git, si se utiliza la instalación por clonación.
- Terminal: PowerShell, CMD, Bash o equivalente.
- No requiere `pip install`, servicios externos, claves ni conexión a internet para ejecutar.

En Linux/macOS puede ser necesario usar `python3`; en Windows también se puede usar
`py -3`. Los comandos siguientes usan `python` por brevedad.

## Instalación

Clona **este repositorio** usando la URL de su botón **Code → HTTPS** y entra en la
carpeta descargada. También puedes usar **Code → Download ZIP** y extraerlo.

```bash
git clone https://github.com/leonardoguz220/study-session-builder-skill.git
cd study-session-builder-skill
python --version
```

Para llevar la skill a otro proyecto, copia la carpeta completa
`.codex/skills/study-session-builder/` a `.codex/skills/` de ese proyecto. Conserva
juntos `SKILL.md`, `scripts`, `assets`, `references` y `agents`.

En un agente compatible con esa ubicación de skills, abre el proyecto y solicita:

> Usa study-session-builder para planificar mi examen de Redes. Mis temas son TLS
> y DNS. Te proporcionaré la fecha del examen y los minutos disponibles cada día.

El agente debe pedir los datos faltantes y ejecutar los scripts siguiendo `SKILL.md`.
La ejecución directa de Python funciona aunque no tengas un agente compatible.

## Inicio rápido: demostración siempre vigente

Desde la raíz del proyecto:

```bash
python .codex/skills/study-session-builder/scripts/demo.py
```

La demo crea `output/demo-valid.json` y `output/demo-invalid.json` con fechas desde
el día local actual. Valida la entrada, genera `output/study-plan.md` y verifica
que una prioridad inexistente falle con código 2 y sin traceback.

Resultado final esperado:

```text
DEMO COMPLETA: ambos casos se comportaron como se esperaba.
```

Los ejemplos originales no se modifican. `output/` se mantiene fuera del historial,
excepto `.gitkeep`, para no publicar datos personales de planes futuros.

## Ejecución con tus propios datos

1. Copia `examples/valid_input.json` y actualiza fechas, temas y disponibilidad.
2. Valida la entrada:

```bash
python .codex/skills/study-session-builder/scripts/validate_input.py examples/valid_input.json
```

3. Genera el resultado:

```bash
python .codex/skills/study-session-builder/scripts/build_schedule.py examples/valid_input.json --output output/study-plan.md
```

4. Abre `output/study-plan.md` con la vista previa Markdown de VS Code o tu editor.

**Fechas del ejemplo:** el JSON incluido es el caso histórico del 25 al 29 de
septiembre de 2026, con examen el 30. Si esas fechas ya pasaron, el rechazo es
correcto. Actualízalas con datos reales o utiliza `demo.py`. El reloj y la zona
horaria del equipo determinan la fecha actual; no hay opción CLI para omitirla.

La salida predeterminada es relativa al directorio desde el que ejecutas el comando.
La plantilla y las reglas se localizan mediante la ruta del script, así que también
funciona desde otra carpeta. Una entrada inválida no escribe ni reemplaza la salida;
si ya había un plan anterior, ese archivo permanece y no corresponde a la entrada
rechazada. Una ejecución exitosa reemplaza el archivo de salida indicado.

## Ejemplo de entrada

```json
{
  "subject": "Aplicaciones con Redes",
  "exam_date": "2026-09-30",
  "topics": ["TLS 1.3", "DNS y DHCP", "HTTP/2 y HTTP/3", "Balanceo de carga"],
  "priority_topics": ["TLS 1.3", "Balanceo de carga"],
  "availability": {
    "2026-09-25": 120,
    "2026-09-26": 90,
    "2026-09-27": 180,
    "2026-09-28": 120,
    "2026-09-29": 120
  },
  "max_session_minutes": 50
}
```

Puedes omitir `priority_topics` o usar `[]`. Puedes omitir `max_session_minutes`
para usar el valor de las reglas (50). El contrato completo está en
[input-format.md](.codex/skills/study-session-builder/references/input-format.md).

## Ejemplo de resultado

Con la entrada anterior se generan 15 sesiones y la siguiente distribución:

| Uso | Minutos |
| --- | ---: |
| TLS 1.3, prioridad explícita | 141 |
| DNS y DHCP | 71 |
| HTTP/2 y HTTP/3 | 71 |
| Balanceo de carga, prioridad explícita | 141 |
| Repaso general | 106 |
| Descansos | 100 |
| **Total** | **630** |

El 25 de septiembre contiene tres sesiones de 34, 33 y 33 minutos, separadas por
dos descansos de 10 minutos: **120 minutos exactos**. Consulta el
[plan completo generado](examples/expected-study-plan.md).

El límite de 20 minutos se aplica al valor configurable de la duración máxima,
no a cada sesión: se permiten sesiones más cortas. Si hay muy pocos minutos, se
advierten temas con asignación insuficiente o cero. Los pesos pueden empatar por
redondeo cuando el presupuesto es diminuto. El plan no garantiza aprobar el examen.

## Manejo de errores

```bash
python .codex/skills/study-session-builder/scripts/build_schedule.py examples/invalid_input.json
```

Mientras las fechas del ejemplo estén vigentes, se obtiene:

```text
[ERROR] Cada prioridad debe existir exactamente en topics.
```

Para demostrar ese mismo error después, usa `output/demo-invalid.json`, creado por
la demo. Los ejemplos con fechas pasadas se rechazan primero por fecha.

| Condición | Comportamiento |
| --- | --- |
| Archivo inexistente, ilegible o JSON inválido | Error claro, código 2 |
| Materia vacía, temas vacíos o duplicados | Rechazo, código 2 |
| Prioridad inexistente o repetida | Rechazo, código 2 |
| Examen pasado, hoy o fecha imposible | Rechazo, código 2 |
| Disponibilidad pasada, vacía o desde el examen | Rechazo, código 2 |
| Minutos no enteros, cero, negativos o mayores que 1440 por día | Rechazo, código 2 |
| Máximo de sesión fuera de 20–120 o de tipo incorrecto | Rechazo, código 2 |
| Campos extra, claves JSON duplicadas, reglas incoherentes | Rechazo, código 2 |
| Plantilla faltante o variables incorrectas | Rechazo, código 2 |
| Imposibilidad de escribir el plan | Error claro, código 1 |
| Tiempo escaso pero entrada válida | Plan con avisos, código 0 |

## Pruebas

```bash
python -m unittest discover -s tests -v
```

Se incluyen **25 tests**: entrada válida, prioridades, fechas y tipos inválidos,
conservación de tiempo diaria y global, uso real de plantilla y reglas, repaso,
reparto equilibrado, ejecución desde otra carpeta y demo de extremo a extremo.
La comprobación de límites recorre los presupuestos de 1 a 1440 minutos para máximos
20, 50 y 120. Las pruebas usan fechas relativas y no caducan con el ejemplo.

## Uso real de scripts, assets y references

| Recurso | Cómo se utiliza |
| --- | --- |
| `SKILL.md` | Instruye al agente sobre cuándo usarla, qué pedir y qué ejecutar |
| `scripts/validate_input.py` | CLI e importación compartida para validar |
| `scripts/build_schedule.py` | Reparto de minutos y generación del Markdown |
| `scripts/demo.py` | Ejecuta los dos casos y verifica códigos y mensajes |
| `assets/study-plan-template.md` | Se abre con Python y se sustituyen sus variables |
| `references/study_rules.json` | Se carga con Python; sus nueve parámetros afectan la ejecución |
| `references/input-format.md` | El agente lo consulta antes de construir la entrada |
| `references/study-method.md` | El agente lo consulta para explicar el cálculo y sus límites |

La descripción detallada del algoritmo y de los parámetros está en
[study-method.md](.codex/skills/study-session-builder/references/study-method.md).

## Presentación individual: guía de 5–7 minutos

1. **Problema, 45 s:** «Esta skill transforma mis temas y mi disponibilidad en un
   plan antes del examen, con sesiones, descansos y repaso».
2. **Estructura, 60 s:** muestra `SKILL.md`, su descripción, los scripts, la plantilla
   y las referencias. Explica que una skill guía al agente y que los scripts hacen
   el cálculo reproducible.
3. **Entrada, 45 s:** muestra el JSON; explica las prioridades opcionales.
4. **Caso exitoso, 90 s:** ejecuta la demo y abre `output/study-plan.md`. Explica la
   igualdad `424 + 106 + 100 = 630` y una jornada concreta.
5. **Error controlado, 45 s:** ejecuta el generador con `output/demo-invalid.json`.
   Explica que el código 2 señala una entrada inválida sin un traceback técnico.
6. **Pruebas, 45 s:** ejecuta unittest y muestra las 25 pruebas correctas.
7. **Cierre, 30 s:** muestra cómo cambiar la plantilla o el porcentaje de repaso
   permite adaptar el resultado; señala que los temas solo se priorizan a petición.

Antes de exponer, ensaya los comandos y verifica que Python esté disponible.
El proyecto cubre los componentes de la rúbrica; la nota también depende de la
explicación individual y de la evaluación docente.

| Criterio de la rúbrica | Evidencia preparada |
| --- | --- |
| Funcionalidad, 35 puntos | Generador, demo y plan real |
| Estructura, 20 puntos | Skill y las tres carpetas con uso documentado |
| Documentación, 15 puntos | Instalación, contrato, algoritmo y ejemplos |
| Pruebas y errores, 15 puntos | 25 tests y caso inválido controlado |
| Presentación individual, 15 puntos | Guía y comandos reproducibles para ensayar |

## Evidencias y capturas

Consulta [evidence/README.md](evidence/README.md). El archivo
[evidence/verification.txt](evidence/verification.txt) contiene la salida real de
la validación, generación, caso inválido, demo y unittest. Las capturas sugeridas
se deben obtener ejecutando los comandos; no se incluyen imágenes simuladas.
