# Skills Spec - AI Shorts Agent

## Overview
Cada skill es un bloque encapsulado. Yo las orchestro, no las implemento.

---

## Skill: get_trends()

**Propósito**: Obtener trends actuales de múltiples fuentes

**Inputs**: 
- `sources`: ["twitter", "youtube", "tiktok", "news"]
- `niche`: string (opcional)
- `limit`: int (default 20)

**Output**: 
```json
{
  "trends": [
    {
      "id": "trend_001",
      "topic": "IA tools 2025",
      "source": "twitter",
      "viral_score": 85,
      "timestamp": "2026-04-10T10:00:00Z"
    }
  ]
}
```

**Cuándo usarla**: Al inicio de cada ciclo, para descubrir qué está trending.

---

## Skill: generate_idea(trends)

**Propósito**: Crear ideas de contenido alineadas con trends

**Inputs**:
- `trends`: lista de trends disponibles
- `niche`: string
- `style`: ["story", "list", "reaction", "tutorial", "fact"]

**Output**:
```json
{
  "ideas": [
    {
      "id": "idea_001",
      "trend_id": "trend_001",
      "hook": "5 IA tools que van a cambiar todo en 2025",
      "format": "list",
      "viral_potential": 78
    }
  ]
}
```

**Cuándo usarla**: Inmediatamente después de get_trends().

---

## Skill: write_script(idea)

**Propósito**: Escribir guion optimizado para short (30-60s)

**Inputs**:
- `idea_id`: string
- `duration`: int (default 45 segundos)
- `tone`: ["educational", "entertaining", "controversial", "inspirational"]

**Output**:
```json
{
  "script": {
    "hook": "3 segundos - atención inmediata",
    "body": "45 segundos - valor principal",
    "cta": "5 segundos - call to action",
    "total_duration": 53,
    "words": 132
  }
}
```

**Regla de estructura**: Hook (3s) + Valor (45s) + CTA (5s)

---

## Skill: generate_hook(script)

**Propósito**: Optimizar el hook para máxima retención

**Inputs**:
- `script`: objeto script
- `variations`: int (cuántas variantes generar)

**Output**:
```json
{
  "hooks": [
    {"text": "¿Sabías esto sobre IA?", "type": "question"},
    {"text": "Esto va a impactar a todos", "type": "statement"}
  ]
}
```

---

## Skill: generate_voice(script)

**Propósito**: Convertir guion a audio TTS

**Inputs**:
- `script_text`: string
- `voice_id`: string
- `speed`: float (0.8 - 1.2)

**Output**: `audio.mp3` path

---

## Skill: generate_video(script, audio)

**Propósito**: Renderizar video final

**Inputs**:
- `script`: objeto script
- `audio_path`: string
- `template`: string (opcional)
- `aspect_ratio`: "9:16" (default para shorts)

**Output**: `video.mp4` path

---

## Skill: generate_subtitles(video)

**Propósito**: Añadir subtitles al video

**Inputs**:
- `video_path`: string
- `language`: string (default "es")
- `style`: ["burned", "srt"]

**Output**: `video_with_subs.mp4`

---

## Skill: publish(video)

**Propósito**: Publicar a la plataforma destino

**Inputs**:
- `video_path`: string
- `platform`: ["youtube", "tiktok", "instagram"]
- `title`: string
- `description`: string
- `tags`: list

**Output**: `{ "url": "https://...", "video_id": "xxx" }`

---

## Skill: analyze_performance(video_id)

**Propósito**: Analizar métricas post-publicación

**Inputs**:
- `video_id`: string
- `platform`: string

**Output**:
```json
{
  "metrics": {
    "views": 15000,
    "retention_avg": 68,
    "likes": 2300,
    "comments": 145,
    "shares": 89,
    "ctr": 4.2
  },
  "recommendations": [
    "Hooks más cortos funcionan mejor en tu nicho",
    "Los tutoriales tienen mayor retention"
  ]
}
```

**CRÍTICO**: Este output debe guardarse en memoria para optimización futura.

---

## Diagrama de Integración

```
┌─────────────────────────────────────────────────────────┐
│                   AGENTE MAESTRO                        │
│  (orchestrator + decision_engine + memory_manager)     │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   get_trends    generate_idea   analyze_performance
        │              │                    │
        ▼              ▼                    ▼
   trends.json     ideas.json        performance_log.json
        │              │                    ▲
        │              ▼                    │
        │         write_script             │
        │              │                    │
        │              ▼                    │
        │         generate_hook             │
        │              │                    │
        │              ▼                    │
        │         generate_voice            │
        │              │                    │
        │              ▼                    │
        │         generate_video             │
        │              │                    │
        │              ▼                    │
        │    generate_subtitles             │
        │              │                    │
        │              ▼                    │
        └────────────►publish()◄────────────┘
```

---

## Notas Importantes

1. **Las skills son inmutables** — yo no las modify, solo las uso
2. **La memoria es bidireccional** — escribo después de analyze_performance, leo antes de generate_idea
3. **El flujo NO es siempre lineal** — puedo saltar pasos si la memoria indica que no funcionan
4. **Cada ciclo debe mejorar** —对比 anterior ciclo, ajustando según métricas