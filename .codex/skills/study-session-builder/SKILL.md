---
name: study-session-builder
description: >
  Crea un plan de estudio distribuido por días a partir de una materia,
  fecha de examen, lista de temas, disponibilidad diaria y duración máxima
  de sesión. Usar cuando una persona necesite organizar su tiempo de
  estudio antes de un examen, con repasos, descansos y prioridades opcionales.
---

# Study Session Builder

## Cuándo utilizarla

Utilizar para transformar disponibilidad y temas de un examen en un plan Markdown
verificable. Admitir prioridades solo si la persona las señala explícitamente.

## Cuándo no utilizarla

No utilizar para responder el examen, generar contenido académico, administrar
calendarios ni garantizar resultados académicos. Si falta una fecha o disponibilidad,
solicitar ese dato antes de generar el plan.

## Datos necesarios

Recoger `subject`, `exam_date`, `topics` y `availability`. Recoger opcionalmente
`priority_topics` y `max_session_minutes` (50 por defecto). Utilizar Python 3.10+.

## Flujo de ejecución

1. Leer [input-format.md](references/input-format.md) para construir el JSON.
2. Consultar [study-method.md](references/study-method.md) para explicar el reparto
   y [study_rules.json](references/study_rules.json) para conocer los parámetros.
3. Guardar los datos confirmados en un archivo JSON. No inventar temas ni prioridades.
   Confirmar la fecha local del sistema si el usuario está en otra zona horaria.
4. Ejecutar `python <SKILL_DIR>/scripts/validate_input.py <entrada.json>`.
5. Si la validación falla, presentar el error y corregir únicamente los datos
   indicados por la persona. No alterar fechas para eludir la validación.
6. Ejecutar `python <SKILL_DIR>/scripts/build_schedule.py <entrada.json> --output output/study-plan.md`.
   Sustituir `<SKILL_DIR>` por la ruta real de esta carpeta, conservando comillas
   si la ruta contiene espacios.
7. Leer el Markdown generado y comprobar el total de contenido, repaso y descansos;
   las fechas deben ser anteriores al examen. Comunicar las advertencias.
8. Entregar el archivo generado y un resumen breve. Indicar que el repaso está al
   final y que una sesión puede contener varias actividades.

## Recursos ejecutados

- `scripts/validate_input.py`: validar JSON, fechas, temas, prioridades y reglas;
  devolver código 2 con un mensaje claro ante entrada inválida.
- `scripts/build_schedule.py`: cargar reglas, distribuir minutos enteros y abrir
  realmente `assets/study-plan-template.md` para producir el resultado.
- `scripts/demo.py`: ejecutar un caso válido y otro inválido con fechas futuras
  calculadas desde el día local actual. Ejecutar desde cualquier carpeta; genera
  `output/study-plan.md` en el directorio de trabajo.

La disponibilidad incluye descansos. Reservar el porcentaje configurado del tiempo
neto de estudio para repaso. Dar mayor peso únicamente a las prioridades explícitas;
sin prioridades, distribuir de forma equilibrada. Usar siempre los scripts para
calcular, sin reconstruir manualmente el algoritmo.
