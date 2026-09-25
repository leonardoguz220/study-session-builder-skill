# Método de distribución

El método es una regla de organización configurable, no una garantía académica.

1. Validar datos y cargar `study_rules.json`.
2. Ordenar los días. Para cada presupuesto D, máximo M y descanso B, calcular
   `n = ceil((D + B) / (M + B))`. Es el mínimo número de sesiones que permite
   conservar el presupuesto con `n - 1` descansos. Reservar `B * (n - 1)` minutos.
3. Repartir el tiempo neto del día por igual entre n sesiones, con diferencias
   máximas de un minuto. Cada sesión es positiva y no supera M.
4. Sumar el tiempo neto de todos los días (S). Reservar `floor(S * review_ratio)`
   para repaso, con un mínimo de un minuto cuando S >= 2 y dejando al menos
   un minuto para contenido. Con S = 1, advertir que no hay repaso posible.
5. Repartir contenido usando peso 2 para prioridades explícitas y 1 para el resto
   (valores configurables). Usar restos mayores: tomar las partes enteras y dar
   los minutos sobrantes a los residuos más grandes, desempatando por orden de temas.
6. Colocar contenido en el orden de la lista y repaso general al final. Las sesiones
   pueden contener varios temas para evitar añadir descansos que excedan el presupuesto.
   El último bloque puede repartir el repaso entre varias sesiones y días.
7. Advertir sobre cualquier tema con menos de 40 minutos de contenido y sobre temas
   sin asignación. Con muy poco tiempo, los pesos pueden empatar por redondeo; no
   prometer más minutos estrictos para cada prioridad en esos casos.
8. Renderizar con la plantilla real. Mostrar contenido, repaso, descansos y total.

## Ejemplo verificable

Con el ejemplo de 630 minutos, máximo de 50 y descansos de 10, se crean 15 sesiones.
Los descansos suman 100 minutos; quedan 530 para estudio. Se reservan 106 para repaso
(20 %) y 424 para contenido. TLS recibe 141, DNS 71, HTTP 71 y Balanceo 141 minutos.
La igualdad final es `424 + 106 + 100 = 630`. Sin prioridades, los temas reciben
cantidades que difieren como máximo en un minuto.

## Parámetros utilizados en ejecución

| Parámetro | Uso real |
| --- | --- |
| `review_ratio` | Fracción del estudio neto dedicada al repaso |
| `priority_weight` | Peso de cada prioridad explícita |
| `normal_weight` | Peso de cada tema restante |
| `default_max_session_minutes` | Máximo cuando falta en la entrada |
| `min_allowed_session_minutes` | Límite inferior para configurar el máximo |
| `max_allowed_session_minutes` | Límite superior para configurar el máximo |
| `recommended_min_content_minutes_per_topic` | Umbral de advertencia por tema |
| `break_minutes` | Pausa entre sesiones del mismo día |

Todos los parámetros deben ser positivos y finitos. Los minutos deben ser enteros;
el porcentaje debe estar entre 0 y 1; el peso prioritario debe superar al normal;
`break_minutes < min_allowed_session_minutes <= default_max_session_minutes <= max_allowed_session_minutes`.

## Plantilla

`assets/study-plan-template.md` debe conservar estas variables (pueden repetirse):
`SUBJECT`, `EXAM_DATE`, `TOTAL_TIME`, `MAX_SESSION`, `STATUS`, `WARNINGS`, `DAILY_PLAN`,
`TOPIC_SUMMARY`, `CONTENT_TIME`, `REVIEW_TIME`, `BREAK_TIME`, cada una entre `{{` y `}}`.
Cambiar los títulos o el texto de la plantilla cambia el archivo generado.
Los textos del usuario se escapan para no romper las tablas Markdown.
