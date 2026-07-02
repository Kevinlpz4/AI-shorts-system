---
adr: "ADR-021"
title: "Foundation Stability Policy"
status: "APPROVED"
date: "2026-07-02"
---

# ADR-021: Foundation Stability Policy

## Contexto

El Foundation Layer es la base técnica de TODO el sistema. Su estabilidad
determina la estabilidad del sistema completo.

Sin una política explícita, Foundation tiende a convertirse en un "cajón
de sastre" donde termina cualquier cosa que "podría ser útil en el futuro".
Esto lleva a:

- Foundation con 50 módulos, de los cuales 40 solo los usa un BC.
- Dependencias ocultas entre BCs a través de foundation.
- Foundation que ya no es "base" sino "todo".
- Incertidumbre sobre qué va y qué no va en foundation.

## Decisión

Se establece la siguiente **Foundation Stability Policy**, que rige
qué se puede agregar al Foundation Layer y bajo qué condiciones.

### Criterios de inclusión

Un componente PUEDE ser agregado a Foundation SOLO si cumple **todos**
los siguientes criterios:

```
1. MULTI-BC: Será utilizado por al menos DOS (2) Bounded Contexts
   diferentes en los próximos 2 Epics planificados.

2. NO BUSINESS RULES: No contiene reglas de negocio de ningún BC.
   Si usa una palabra del lenguaje ubicuo de un BC, no está en
   foundation.

3. ZERO DEPENDENCIES: No introduce dependencias externas nuevas.
   Foundation sigue siendo stdlib-only.

4. NO COUPLING: No incrementa el acoplamiento entre Bounded Contexts.
   Los BCs no deben necesitar conocer la existencia de otros BCs
   a través de foundation.

5. MECHANISM, NOT POLICY: Resuelve un problema técnico transversal
   (identidad, errores, eventos, clock), NO un problema de negocio.
```

### Lo que queda FUERA de Foundation

| Componente | Motivo de exclusión |
|-----------|-------------------|
| Category entity | Es dominio compartido, no base técnica → `shared/domain/` |
| AI ports | Solo usado por BCs que usan AI → `ai/` |
| ResearchSourcePort | Solo Research BC → `research/domain/` |
| URL utilities | Si solo los usa ingestion → `ingestion/` |
| HTTP client wrappers | Si solo los usa ingestion → `ingestion/infrastructure/` |
| Algo "por si acaso" | YAGNI. Se agrega cuando haya DOS BCs que lo necesiten. |

### Proceso de inclusión

```
Propuesta de nuevo componente para Foundation
  │
  ├── 1. Verificar contra los 5 criterios
  │       └── ¿Cumple TODOS?
  │              │
  │              Sí → 2. ADR que documenta la decisión
  │              │      3. Implementación
  │              │
  │              No → 4. El componente NO va en foundation
  │                    5. Va en el BC que lo necesita
  │                       o en shared/ si es dominio compartido
  │
  └── Si después 2 BCs lo necesitan → se extrae a foundation
       (refactor controlado con ADR)
```

### Consecuencias

#### Positivas ✅
- Foundation se mantiene pequeño, estable y enfocado.
- No hay acoplamiento oculto entre BCs vía foundation.
- Cualquier desarrollador puede determinar rápidamente si algo pertenece a foundation.
- La política es clara y aplicable desde el día 1.

#### Negativas ⚠️
- Hay que ser disciplinado. Es tentador poner algo "útil" en foundation.
- Extraer algo de un BC a foundation después requiere refactor.
- Puede haber pequeñas duplicaciones temporales hasta que dos BCs requieran lo mismo.

### Alternativas Consideradas

#### Alternativa 1: Sin política (dejar crecer orgánicamente)
- **Descartada por**: Foundation se convierte en `utils/` gigante e inmantenible.
  Experiencia comprobada en cientos de proyectos.

#### Alternativa 2: Política relajada ("si es útil, va")
- **Descartada por**: No previene el crecimiento descontrolado. "Útil" es subjetivo.

#### Alternativa 3: Prohibir completamente nuevas incorporaciones
- **Descartada por**: Demasiado restrictiva. Hay casos legítimos (ClockPort,
  UUIDProvider) que justifican estar en foundation desde el inicio.

### Compliance

- **Principios**: F1 (zero dependencies), F6 (no business logic)
- **Baseline**: v1.0 Foundation Design (no rompe)
