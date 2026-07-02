# Foundation Stability Policy

> **Documento oficial de política del proyecto**
> Versión: 1.0 | Estado: **RATIFIED** | Fecha: 2026-07-02
> ARB Resolution: ARB-2026-07-02-001

---

## 1. Declaración

El **Foundation Layer v1.0** queda oficialmente **CONGELADO** a partir de la fecha de este documento. No se agregan funcionalidades por comodidad, conveniencia, o "por si acaso". Todo cambiopropuesta debe pasar por el proceso definido en esta política.

Esta política fue ratificada por el Architecture Review Board (ARB) y es de cumplimiento obligatorio para todo el proyecto.

---

## 2. ¿Qué significa "Foundation está congelado"?

| Implica | No implica |
|---------|-----------|
| La API pública (`foundation/__init__.py`) es estable y no cambia sin ADR | Que Foundation esté "terminado" para siempre |
| No se agregan nuevos componentes sin cumplir los 5 criterios | Que no puedan haber bug fixes |
| Todo cambio es evaluado contra esta política | Que Foundation no pueda evolucionar si hay necesidad legítima |
| Los BCs pueden depender de Foundation sin fear of breaking changes | Que no puedan hacerse refactors internos (mientras la API pública no cambie) |

---

## 3. Criterios de Inclusión (los 5 mandamientos)

Un componente **PUEDE** ser agregado a Foundation SOLO si cumple **TODOS** los siguientes criterios:

```
┌─────────────────────────────────────────────────────────────────┐
│  1. MULTI-BC                                                     │
│     Es utilizado por al menos DOS (2) Bounded Contexts           │
│     diferentes. Si solo un BC lo necesita, vive en ese BC.      │
├─────────────────────────────────────────────────────────────────┤
│  2. NO BUSINESS RULES                                            │
│     No contiene reglas de negocio de ningún BC.                  │
│     Si usa una palabra del lenguaje ubicuo, no está en           │
│     Foundation.                                                  │
├─────────────────────────────────────────────────────────────────┤
│  3. ZERO DEPENDENCIES                                            │
│     No introduce dependencias externas nuevas.                   │
│     Foundation sigue siendo stdlib-only.                         │
├─────────────────────────────────────────────────────────────────┤
│  4. NO COUPLING                                                  │
│     No incrementa el acoplamiento entre Bounded Contexts.        │
│     Los BCs no deben necesitar conocer la existencia de          │
│     otros BCs a través de Foundation.                            │
├─────────────────────────────────────────────────────────────────┤
│  5. MECHANISM, NOT POLICY                                        │
│     Resuelve un problema técnico transversal (identidad,         │
│     errores, eventos, clock), NO un problema de negocio.         │
└─────────────────────────────────────────────────────────────────┘
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

---

## 4. Proceso de Cambio

```
┌─────────────────────────────────────────────────────────────────┐
│                    PROCESO DE CAMBIO                             │
│                                                                  │
│  1. Identificar necesidad de cambio                              │
│     └── ¿Es un bug? → Saltar a paso 5                           │
│     └── ¿Es una vulnerabilidad? → Saltar a paso 5               │
│     └── ¿Es una nueva funcionalidad? → Continuar                 │
│                                                                  │
│  2. Verificar contra los 5 criterios                             │
│     └── ¿Cumple TODOS? → Continuar                              │
│     └── ¿NO cumple alguno? → NO va en Foundation.               │
│         Va en el BC que lo necesita.                             │
│                                                                  │
│  3. ¿Lo solicitan al menos DOS BCs distintos?                    │
│     └── Sí → Continuar                                           │
│     └── No → Rechazar. NO se agrega por comodidad.              │
│                                                                  │
│  4. Redactar ADR                                                 │
│     └── Documentar: problema, solución, alternativas             │
│     └── ARB revisa y vota                                       │
│     └── ADR APPROVED → se implementa                            │
│                                                                  │
│  5. Implementación                                               │
│     └── Mantener Backward Compatibility                          │
│     └── Sin Breaking Changes                                     │
│     └── Tests completos                                          │
│     └── Documentación actualizada                                │
│                                                                  │
│  6. Release                                                      │
│     └── Foundation v1.x (minor) si es aditivo                    │
│     └── Foundation v2.0 (major) si es breaking (excepcional)    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Tipos de Cambio

### Bug Fix (✅ Permitido sin ADR)

- Corrección de comportamiento incorrecto
- No cambia la API pública
- No agrega nuevas funcionalidades
- Requiere test que reproduzca el bug
- Se revisa en code review normal

### Vulnerabilidad (✅ Permitido sin ADR)

- Corrección de seguridad
- Puede cambiar comportamiento interno
- No cambia la API pública a menos que sea estrictamente necesario
- Se documenta en el commit

### Mejora Interna (Refactor) (✅ Permitido sin ADR)

- No cambia la API pública
- Mejora rendimiento, legibilidad, mantenibilidad
- Tests existentes deben seguir pasando

### Nueva Funcionalidad (❌ Requiere ADR + 5 criterios + 2 BCs)

- Cualquier adición a la API pública
- Cualquier nuevo componente
- Debe cumplir los 5 criterios
- Debe ser solicitada por al menos 2 BCs distintos

### Breaking Change (❌ Excepcional, requiere ADR + ARB)

- Cambio en la API pública que rompe BCs existentes
- Requiere justificación extensa
- Requiere plan de migración
- Requiere versión major (v2.0, v3.0, etc.)

---

## 6. Backward Compatibility

Foundation v1.x garantiza:

1. **Binary compatibility**: Código compilado contra v1.0 funciona con v1.x
2. **Source compatibility**: Código fuente escrito contra v1.0 compila con v1.x sin cambios
3. **Behavioral compatibility**: El comportamiento documentado no cambia

**No constituye breaking change:**
- Agregar nuevos exports a `foundation/__init__.py` (aditivo)
- Agregar nuevos métodos a clases existentes (si tienen default)
- Agregar nuevos parámetros opcionales a constructores/funciones
- Cambios internos de implementación que no afectan la API

**Constraint**: Ningún breaking change está permitido sin un ADR explícito que documente:
- Justificación del breaking change
- Impacto en cada BC
- Plan de migración
- Timeline de deprecación (mínimo 1 sprint de aviso)

---

## 7. ADRs Asociados

| ADR | Título | Relación |
|-----|--------|----------|
| ADR-016 | Foundation Layer como Base Técnica Compartida | Define qué es Foundation |
| ADR-017 | EntityId como Value Object con Type Safety | Implementa identidad |
| ADR-018 | Result Pattern para Flujos Esperados | Implementa Result |
| ADR-019 | ClockPort y UUIDProvider como Puertos | Implementa puertos |
| ADR-020 | Tres Capas de Error (Domain, Application, Infrastructure) | Implementa errores |
| ADR-021 | Foundation Stability Policy | **Este documento** |
| ADR-022 | ErrorCode Enum Inheritance Policy | Política de enums |

---

## 8. Vigencia y Revisión

- **Esta política entra en vigencia**: Inmediatamente, con la declaración de Foundation v1.0 STABLE.
- **Próxima revisión**: Al completar el EPIC 3 (Ingestion Domain Core) o si un ADRpropuesta modifica Foundation.
- **Excepciones**: Cualquier desarrollador puede solicitar una excepción mediante ADRpropuesta. La excepción debe justificar por qué el cambio es necesario y por qué no se puede lograr respetando esta política.

---

## 9. Firmas

| Rol | Fecha |
|-----|-------|
| Architecture Review Board | 2026-07-02 |
| Principal Software Architect | 2026-07-02 |

---

*Documento generado durante el cierre oficial de Foundation v1.0 STABLE.*
*Ratifica y expande ADR-021 como política oficial del proyecto.*
