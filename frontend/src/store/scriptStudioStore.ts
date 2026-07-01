// ═══════════════════════════════════════════════════
// scriptStudioStore — Zustand store for Script Studio
// ═══════════════════════════════════════════════════
// Estado del Studio: topics aprobados sin script,
// recomendaciones, configuración y generación.
// Desacoplado del dominio: almacena DTOs planos.

import { create } from "zustand";

import { TopicData, ScriptData, ScriptRecommendations, StudioConfig } from "@/types";
import { TopicStatusValue, SourceType } from "@/types";
import { getApiBase, mapScriptFromApi } from "@/lib/utils";

// ── State shape ──

interface ScriptStudioState {
  // ── Data ──
  approvedTopics: TopicData[];
  selectedTopic: TopicData | null;
  recommendations: ScriptRecommendations | null;
  config: StudioConfig;
  script: ScriptData | null;

  // ── UI state ──
  isLoading: boolean;
  isGenerating: boolean;
  error: string | null;

  // ── Actions ──
  loadApprovedTopics: () => Promise<void>;
  selectTopic: (topic: TopicData) => Promise<void>;
  setConfig: (partial: Partial<StudioConfig>) => void;
  generateScript: () => Promise<void>;
  regenerateScript: () => Promise<void>;
  acceptScript: () => void;
  clearSelection: () => void;
  clearError: () => void;
}

// ── Constants ──

const DEFAULT_CONFIG: StudioConfig = {
  duration: 60,
  tone: "educational",
  niche: "tecnología",
};

// ── Helpers ──



// ── Mock generators ──

/** Genera topics mock realistas para desarrollo sin backend */
function generateMockTopics(): TopicData[] {
  return [
    {
      id: "mock-topic-1",
      title: "DeepSeek: La IA China que Desafía a OpenAI",
      description:
        "Análisis del nuevo modelo de lenguaje DeepSeek y su impacto en la industria de la inteligencia artificial.",
      contentPreview:
        "DeepSeek ha emergido como un competidor directo de OpenAI, ofreciendo rendimiento comparable a una fracción del costo...",
      sourceName: "google-news",
      sourceType: SourceType.GOOGLE_NEWS,
      status: TopicStatusValue.APPROVED,
      score: { relevance: 9, popularity: 8, recency: 10, reliability: 7 },
      scoreTotal: 85,
      url: "https://example.com/deepseek-ai",
      author: null,
      createdAt: "2026-06-28T10:00:00Z",
      reviewedAt: "2026-06-29T14:30:00Z",
      duplicateHash: null,
    },
    {
      id: "mock-topic-2",
      title: "Bitcoin Rompe los $150,000: ¿Qué Significa para tu Bolsillo?",
      description:
        "El precio de Bitcoin alcanza un nuevo máximo histórico. Análisis de impacto financiero y perspectivas del mercado cripto.",
      contentPreview:
        "Bitcoin ha superado la barrera de los $150,000 por primera vez en su historia, impulsado por la adopción institucional...",
      sourceName: "twitter",
      sourceType: SourceType.TWITTER,
      status: TopicStatusValue.APPROVED,
      score: { relevance: 8, popularity: 9, recency: 9, reliability: 5 },
      scoreTotal: 77,
      url: "https://example.com/bitcoin-ath",
      author: "@crypto_analyst",
      createdAt: "2026-06-27T08:00:00Z",
      reviewedAt: "2026-06-28T11:00:00Z",
      duplicateHash: null,
    },
    {
      id: "mock-topic-3",
      title:
        "Cómo la IA Está Revolucionando el Diagnóstico Médico",
      description:
        "Los algoritmos de machine learning están detectando enfermedades con una precisión que supera a los especialistas humanos.",
      contentPreview:
        "La inteligencia artificial en medicina está avanzando a pasos agigantados. Estudios recientes muestran que los algoritmos...",
      sourceName: "google-news-rss",
      sourceType: SourceType.GOOGLE_NEWS,
      status: TopicStatusValue.APPROVED,
      score: { relevance: 9, popularity: 7, recency: 8, reliability: 9 },
      scoreTotal: 82,
      url: "https://example.com/ai-medical-diagnosis",
      author: null,
      createdAt: "2026-06-26T09:00:00Z",
      reviewedAt: "2026-06-27T16:00:00Z",
      duplicateHash: null,
    },
    {
      id: "mock-topic-4",
      title:
        "Startups de Tecnología Educativa que Atraerán Inversiones en 2026",
      description:
        "El sector EdTech está en pleno auge. Descubre las startups que están transformando la educación con tecnología.",
      contentPreview:
        "El mercado de tecnología educativa sigue creciendo a doble dígito. Startups innovadoras están atrayendo la atención de los principales fondos de inversión...",
      sourceName: "rss",
      sourceType: SourceType.RSS,
      status: TopicStatusValue.APPROVED,
      score: { relevance: 7, popularity: 6, recency: 7, reliability: 7 },
      scoreTotal: 68,
      url: "https://example.com/edtech-startups",
      author: "María García",
      createdAt: "2026-06-25T12:00:00Z",
      reviewedAt: "2026-06-26T09:00:00Z",
      duplicateHash: null,
    },
    {
      id: "mock-topic-5",
      title:
        "Ejercicio y Salud Mental: La Conexión que la Ciencia Confirma",
      description:
        "Nuevos estudios confirman el impacto del ejercicio físico en la salud mental y la prevención de enfermedades neurodegenerativas.",
      contentPreview:
        "La relación entre el ejercicio físico y la salud mental está cada vez más documentada. Investigaciones recientes...",
      sourceName: "google-news",
      sourceType: SourceType.GOOGLE_NEWS,
      status: TopicStatusValue.APPROVED,
      score: { relevance: 8, popularity: 7, recency: 6, reliability: 8 },
      scoreTotal: 73,
      url: "https://example.com/exercise-mental-health",
      author: null,
      createdAt: "2026-06-24T15:00:00Z",
      reviewedAt: "2026-06-25T10:00:00Z",
      duplicateHash: null,
    },
  ];
}

/**
 * Genera recomendaciones mock según las mismas reglas de recommendations.py:
 * - source → tone (mapping por nombre de fuente)
 * - score → duration (≥80 → 90s, ≥60 → 60s, <60 → 30s)
 * - keywords en título/descripción → niche
 */
function generateMockRecommendations(
  topic: TopicData,
): ScriptRecommendations {
  // Tone from source name
  const toneMap: Record<string, [string, string]> = {
    "google-news": [
      "educational",
      "Fuente noticiosa → tono educativo y objetivo",
    ],
    rss: [
      "educational",
      "Contenido RSS → tono educativo y estructurado",
    ],
    "google-news-rss": [
      "educational",
      "Feed de noticias → tono educativo",
    ],
    twitter: [
      "controversial",
      "Twitter → contenido opinativo y controversial",
    ],
  };
  const defaultTone: [string, string] = [
    "educational",
    "Fuente estándar → tono educativo por defecto",
  ];
  const [tone, toneReason] = topic.sourceName.startsWith("manual")
    ? (["informative", "Entrada manual → tono informativo general"] as [string, string])
    : (toneMap[topic.sourceName] || defaultTone);

  // Duration from score
  const [duration, durationReason] =
    topic.scoreTotal >= 80
      ? ([90, "Score alto (≥80): contenido con alto valor → 90s"] as const)
      : topic.scoreTotal >= 60
        ? ([60, "Score medio (60-79): contenido valioso → 60s"] as const)
        : ([30, "Score bajo (<60): contenido simple → 30s"] as const);

  // Niche from keywords in title + description
  const text = (topic.title + " " + topic.description).toLowerCase();
  const keywordsMap: Record<string, [string, string[]]> = {
    tecnologia: [
      "tecnología",
      [
        "ia",
        "inteligencia artificial",
        "tecnología",
        "software",
        "programación",
        "digital",
        "robot",
        "algoritmo",
        "datos",
        "blockchain",
        "deepseek",
        "openai",
        "gpt",
      ],
    ],
    negocios: [
      "negocios",
      [
        "negocio",
        "empresa",
        "startup",
        "mercado",
        "inversión",
        "start-up",
        "corporativo",
        "ceo",
        "emprendedor",
      ],
    ],
    salud: [
      "salud",
      [
        "salud",
        "médico",
        "enfermedad",
        "tratamiento",
        "bienestar",
        "nutrición",
        "ejercicio",
        "mental",
        "covid",
      ],
    ],
    educacion: [
      "educación",
      [
        "educación",
        "aprendizaje",
        "curso",
        "formación",
        "universidad",
        "estudiante",
        "clase",
        "enseñanza",
      ],
    ],
    finanzas: [
      "finanzas",
      [
        "finanza",
        "economía",
        "cripto",
        "bitcoin",
        "bolsa",
        "inversión",
        "ahorro",
        "pesos",
        "dólar",
        "inflación",
      ],
    ],
  };

  let niche = "tecnología";
  let nicheReason =
    "Nicho por defecto: tecnología (no se encontraron keywords específicas)";
  for (const [, [n, keywords]] of Object.entries(keywordsMap)) {
    if (keywords.some((kw) => text.includes(kw))) {
      niche = n;
      nicheReason = `Keywords detectadas → nicho: ${n}`;
      break;
    }
  }

  return {
    tone,
    duration,
    niche,
    reasoning: {
      tone: toneReason,
      duration: durationReason,
      niche: nicheReason,
    },
  };
}

/** Genera un script mock realista basado en el topic y la configuración */
function generateMockScript(
  topic: TopicData,
  config: StudioConfig,
): ScriptData {
  const hookMap: Record<string, string> = {
    tecnología: "🤯 ¿Sabías que la tecnología está avanzando más rápido que nunca?",
    salud: "🩺 Esto es lo que la ciencia dice sobre tu salud y no sabías",
    finanzas: "💰 La verdad sobre el dinero que nadie te cuenta",
    educación: "📚 El método de aprendizaje que está cambiando la educación",
    negocios: "💼 El secreto de las startups más exitosas del momento",
  };

  const hook =
    hookMap[config.niche] ||
    "🔥 Esto va a cambiar tu forma de ver las cosas";

  const body =
    `Hoy vamos a hablar de ${topic.title.toLowerCase()}. ${topic.description}\n\n` +
    `Esto es importante porque está transformando la industria. Los expertos coinciden en que estamos frente a un cambio de paradigma.\n\n` +
    `¿La mejor parte? Tú puedes ser parte de este cambio. Solo necesitas estar informado y tomar acción.`;

  const ctaMap: Record<string, string> = {
    tecnología:
      "🔥 Si te gusta la tecnología, dale like y suscribite para más contenido.",
    salud:
      "💪 Cuidá tu salud, compartí este video con alguien que lo necesita.",
    finanzas:
      "💰 Invertí en tu conocimiento financiero. Seguime para más tips.",
    educación:
      "📚 Nunca pares de aprender. Compartí esto con un estudiante.",
    negocios:
      "🚀 Emprendé con inteligencia. Suscribite para más contenido de negocios.",
  };

  const cta = ctaMap[config.niche] ||
    "🔥 Dale like y suscribite para más contenido.";

  return {
    id: `mock-script-${topic.id}-${Date.now()}`,
    topicId: topic.id,
    hook,
    body,
    cta,
    duration: config.duration,
    tone: config.tone,
    format: "youtube-shorts",
    wordCount: hook.length + body.length + cta.length,
    isValid: true,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };
}

// ── Store ──

export const useScriptStudioStore = create<ScriptStudioState>((set, get) => ({
  // ── Estado inicial ──
  approvedTopics: [],
  selectedTopic: null,
  recommendations: null,
  config: DEFAULT_CONFIG,
  script: null,
  isLoading: false,
  isGenerating: false,
  error: null,

  // ── Cargar topics aprobados sin script ──
  /**
   * Obtiene la cola de topics aprobados que aún no tienen script.
   * En modo mock genera datos simulados.
   */
  loadApprovedTopics: async () => {
    set({ isLoading: true, error: null });
    try {
      const base = getApiBase();

      if (!base) {
        // Mock mode
        set({ approvedTopics: generateMockTopics(), isLoading: false });
        return;
      }

      const res = await fetch(`${base}/api/v1/studio/approved-topics`);

      if (!res.ok) {
        const errData = await res.json().catch(() => null);
        throw new Error(
          errData?.detail || `API error: ${res.status} ${res.statusText}`,
        );
      }

      const data = await res.json();
      set({ approvedTopics: data.topics, isLoading: false });
    } catch (err) {
      set({
        isLoading: false,
        error:
          err instanceof Error ? err.message : "Failed to load approved topics",
      });
    }
  },

  // ── Seleccionar topic ──
  /**
   * Selecciona un topic de la cola, carga sus recomendaciones
   * y establece la configuración inicial.
   */
  selectTopic: async (topic: TopicData) => {
    set({
      selectedTopic: topic,
      script: null,
      recommendations: null,
      config: { duration: 60, tone: "educational", niche: "tecnología" },
    });

    try {
      const base = getApiBase();

      if (!base) {
        // Mock mode
        const recs = generateMockRecommendations(topic);
        set({
          recommendations: recs,
          config: {
            duration: recs.duration,
            tone: recs.tone,
            niche: recs.niche,
          },
        });
        return;
      }

      const res = await fetch(
        `${base}/api/v1/studio/recommendations/${topic.id}`,
      );

      if (!res.ok) {
        const errData = await res.json().catch(() => null);
        throw new Error(
          errData?.detail || `API error: ${res.status} ${res.statusText}`,
        );
      }

      const recs = await res.json();
      set({
        recommendations: recs,
        config: { duration: recs.duration, tone: recs.tone, niche: recs.niche },
      });
    } catch (err) {
      set({
        error:
          err instanceof Error
            ? err.message
            : "Failed to load recommendations",
      });
    }
  },

  // ── Configuración ──
  /** Actualiza parcialmente la configuración del script */
  setConfig: (partial) => {
    set((state) => ({ config: { ...state.config, ...partial } }));
  },

  // ── Generar script ──
  /**
   * Genera un script para el topic seleccionado.
   * Usa la configuración actual (duración, tono, nicho).
   */
  generateScript: async () => {
    const { selectedTopic, config } = get();
    if (!selectedTopic) return;

    set({ isGenerating: true, error: null });
    try {
      const base = getApiBase();

      if (!base) {
        // Mock mode
        await new Promise((r) => setTimeout(r, 800));
        const script = generateMockScript(selectedTopic, config);
        set({ script, isGenerating: false });
        return;
      }

      const res = await fetch(
        `${base}/api/v1/topics/${selectedTopic.id}/script/generate`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(config),
        },
      );

      if (!res.ok) {
        const errData = await res.json().catch(() => null);
        throw new Error(
          errData?.detail || `API error: ${res.status} ${res.statusText}`,
        );
      }

      const data = await res.json();
      set({ script: mapScriptFromApi(data), isGenerating: false });
    } catch (err) {
      set({
        isGenerating: false,
        error:
          err instanceof Error ? err.message : "Failed to generate script",
      });
    }
  },

  // ── Regenerar script ──
  /** Regenera el script — la API maneja la regeneración internamente */
  regenerateScript: async () => {
    await get().generateScript();
  },

  // ── Aceptar script ──
  /**
   * Acepta el script generado.
   * El script ya está guardado por el endpoint de generación,
   * solo lo removemos de la cola local.
   */
  acceptScript: () => {
    const { selectedTopic, approvedTopics } = get();
    if (!selectedTopic) return;

    set({
      selectedTopic: null,
      script: null,
      recommendations: null,
      approvedTopics: approvedTopics.filter(
        (t) => t.id !== selectedTopic.id,
      ),
    });
  },

  // ── Limpiar estado ──
  /** Limpia la selección actual y el script generado */
  clearSelection: () => {
    set({ selectedTopic: null, script: null, recommendations: null });
  },

  /** Limpia el mensaje de error actual */
  clearError: () => {
    set({ error: null });
  },
}));
