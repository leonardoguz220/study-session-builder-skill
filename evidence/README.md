# Evidencias de ejecución

`verification.txt` contiene una ejecución real: fecha, versión de Python, comandos,
salidas de terminal y códigos de salida. `examples/expected-study-plan.md` es una
copia del Markdown generado con el ejemplo original.

## Capturas recomendadas para entregar

| Archivo sugerido | Qué mostrar |
| --- | --- |
| `01-caso-exitoso.png` | Validación y generación correctas de la entrada de la demo |
| `02-plan-generado.png` | Vista previa Markdown, totales y al menos una jornada |
| `03-entrada-invalida.png` | Mensaje de prioridad inexistente y código 2 |
| `04-pruebas-automaticas.png` | Salida de unittest: 25 tests, OK |

No se han creado capturas ficticias. Para obtenerlas, ejecutar desde la raíz:

```bash
python .codex/skills/study-session-builder/scripts/demo.py
python .codex/skills/study-session-builder/scripts/validate_input.py output/demo-valid.json
python .codex/skills/study-session-builder/scripts/build_schedule.py output/demo-valid.json
python .codex/skills/study-session-builder/scripts/build_schedule.py output/demo-invalid.json
python -m unittest discover -s tests -v
```

Tras el caso inválido, consultar `echo $?` en Bash, `$LASTEXITCODE` en PowerShell,
o `echo %ERRORLEVEL%` en CMD: el resultado esperado es 2. Hacerlo inmediatamente
después de ese comando.

Capturar la ventana de terminal o del editor con las herramientas del sistema.
Revisar que la captura no muestre datos privados antes de incorporarla al repositorio.
Las fechas de la demo se adaptan al día de ejecución; no tienen que coincidir con
las del ejemplo histórico de septiembre de 2026.
