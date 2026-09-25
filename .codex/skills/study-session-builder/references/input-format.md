# Formato de entrada

JSON UTF-8 con objeto raíz. No se admiten campos adicionales ni claves duplicadas.

| Campo | Tipo | Regla |
| --- | --- | --- |
| `subject` | string | Texto no vacío, sin caracteres de control |
| `exam_date` | string | Fecha real `AAAA-MM-DD`, posterior a hoy |
| `topics` | lista de strings | No vacía; temas únicos ignorando mayúsculas y espacios exteriores |
| `priority_topics` | lista de strings | Opcional, por defecto `[]`; nombres exactos incluidos en topics, sin duplicados |
| `availability` | objeto fecha: entero | No vacío; fechas desde hoy hasta el día anterior al examen; 1–1440 minutos diarios |
| `max_session_minutes` | entero | Opcional; por defecto 50; entre 20 y 120 con las reglas iniciales |

No se aceptan números decimales ni booleanos como minutos. Los límites de la duración
máxima se leen de `study_rules.json`. Las sesiones concretas pueden durar menos de
20 minutos al repartir tiempos pequeños: 20 es el mínimo de la **configuración del máximo**.
La disponibilidad representa tiempo total, incluidos los descansos sugeridos.
No se requieren horas de inicio; el resultado ordena sesiones, sin inventar horarios.
La fecha actual es `date.today()` del equipo. Configurar correctamente su fecha y zona horaria.

## Ejemplo breve

```json
{
  "subject": "Redes",
  "exam_date": "2026-09-30",
  "topics": ["TLS", "DNS"],
  "availability": {"2026-09-29": 90},
  "max_session_minutes": 50
}
```

Este ejemplo solo es válido antes del 30 de septiembre de 2026 y mientras su
fecha disponible no haya pasado. Para una demostración siempre vigente, ejecutar
`scripts/demo.py`: crea entradas nuevas con fechas relativas a hoy, sin modificar
los ejemplos originales. Para uso real, actualizar el JSON con tus fechas reales.

## Salidas de terminal

- 0: operación correcta.
- 2: entrada, reglas, plantilla o argumentos inválidos; prefijo `[ERROR]`, sin traceback.
- 1: fallo al escribir el resultado, o demostración con un comportamiento inesperado.

Los ejemplos completos y las pruebas están en `examples/` y `tests/` del proyecto.
