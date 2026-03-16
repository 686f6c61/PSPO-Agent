---
description: "Modo carpeta-autopilot: lee instrucciones y cualquier CSV de equipo compatible de una carpeta y ejecuta el flujo completo hasta la gate final"
argument-hint: "Ruta de la carpeta de entrada (opcional). Por defecto: .pspo-agent/inbox"
---

Invoca el skill `pspo-agent:autopilot`.

Si `$ARGUMENTS` esta vacio, usa directamente `.pspo-agent/inbox` como carpeta
de entrada.

Si `$ARGUMENTS` tiene valor, usa esa ruta literalmente.

No preguntes por la ruta ni leas `.claude/settings.local.json` para deducirla.
Antes de reabrir la inbox, comprueba si ya existe runtime de reentrada. Cuenta
como runtime valido cualquiera de estas senales:
- `.pspo-agent/runtime/autopilot-context.md`
- `.pspo-agent/runtime/product-phase.status`
- `.pspo-agent/runtime/final-gate.status`
- `.pspo-agent/runtime/autopilot-branch-skill.status`
Si NO existe ninguna de esas senales, la primera accion valida es
`Glob(".pspo-agent/inbox/*")`.
Si YA existe cualquiera de esas senales de runtime, no reabras la inbox:
- con `product-phase.status=done` y gate pendiente, ve a la gate final
- con rama ya elegida, invoca directamente esa `Skill(...)`
- si solo existe runtime sin producto listo, usa `Skill("pspo-agent:product-phase")`
NO leas directamente `brief.md`, `vision.md`, `contexto.md`, `config*` ni el
CSV de equipo desde este comando.
