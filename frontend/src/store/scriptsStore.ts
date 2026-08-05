"use client";

import { create } from "zustand";
import type { ScriptWithTopic } from "@/types";
import { getApiBase, mapScriptFromApi } from "@/lib/utils";

/** Genera scripts mock para desarrollo offline */
function generateMockScripts(): ScriptWithTopic[] {
  return [
    {
      id: "mock-1",
      topicId: "topic-mock-1",
      topic_title: "DeepSeek: La IA China que Revoluciona el Mercado",
      topic_score: 92,
      topic_status: "approved",
      hook: "¿Sabías que una inteligencia artificial china está cambiando las reglas del juego?",
      body: "DeepSeek no es solo otro modelo de lenguaje. Con su enfoque en eficiencia computacional, está logrando resultados comparables a GPT-4 con una fracción de los recursos. Lo más impresionante es que es open source, permitiendo a desarrolladores de todo el mundo experimentar y mejorar sobre su base. Empresas tecnológicas ya están integrando DeepSeek en sus productos, desde asistentes virtuales hasta herramientas de análisis de datos.",
      cta: "Seguinos para más novedades sobre IA que están transformando el mundo.",
      duration: 60,
      tone: "educational",
      format: "story",
      wordCount: 98,
      isValid: true,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    },
    {
      id: "mock-2",
      topicId: "topic-mock-2",
      topic_title: "Bitcoin Supera los $100K: Análisis del Mercado",
      topic_score: 88,
      topic_status: "approved",
      hook: "Bitcoin acaba de romper una barrera histórica y esto es solo el comienzo.",
      body: "La criptomoneda más famosa del mundo alcanzó un nuevo máximo histórico, superando expectativas de analistas. Los principales factores incluyen la adopción institucional masiva, la reducción a la mitad de la minería que redujo la oferta, y un entorno regulatorio cada vez más favorable en países clave. Expertos predicen que este rally podría continuar durante los próximos meses, aunque advierten sobre la volatilidad característica del mercado.",
      cta: "No te pierdas nuestro análisis completo — suscribite al canal.",
      duration: 90,
      tone: "informative",
      format: "list",
      wordCount: 85,
      isValid: true,
      createdAt: new Date(Date.now() - 86400000).toISOString(),
      updatedAt: new Date(Date.now() - 86400000).toISOString(),
    },
    {
      id: "mock-3",
      topicId: "topic-mock-3",
      topic_title: "Nuevo Tratamiento para la Diabetes Tipo 2",
      topic_score: 75,
      topic_status: "approved",
      hook: "Científicos acaban de anunciar un avance que podría cambiar la vida de millones.",
      body: "Un equipo de investigadores ha desarrollado una nueva terapia que combina un fármaco innovador con cambios en el estilo de vida, logrando remisión de la diabetes tipo 2 en el 70% de los pacientes del estudio. El tratamiento se enfoca en regenerar las células beta del páncreas, responsables de producir insulina. Los resultados preliminares son prometedores y la FDA ya aprobó la fase 3 de ensayos clínicos.",
      cta: "Dale like y compartí esta noticia que podría salvar vidas.",
      duration: 60,
      tone: "educational",
      format: "fact",
      wordCount: 92,
      isValid: true,
      createdAt: new Date(Date.now() - 172800000).toISOString(),
      updatedAt: new Date(Date.now() - 172800000).toISOString(),
    },
  ];
}

/** Estado del store de scripts */
interface ScriptsState {
  scripts: ScriptWithTopic[];
  selectedScript: ScriptWithTopic | null;
  isLoading: boolean;
  error: string | null;
  total: number;

  loadScripts: () => Promise<void>;
  selectScript: (script: ScriptWithTopic) => void;
  clearSelection: () => void;
  clearError: () => void;
}

export const useScriptsStore = create<ScriptsState>((set, get) => ({
  scripts: [],
  selectedScript: null,
  isLoading: false,
  error: null,
  total: 0,

  loadScripts: async () => {
    set({ isLoading: true, error: null });
    try {
      const base = getApiBase();
      if (!base) {
        const mocks = generateMockScripts();
        set({ scripts: mocks, total: mocks.length, isLoading: false });
        return;
      }

      const res = await fetch(`${base}/api/v1/scripts`);
      if (!res.ok) throw new Error("Failed to load scripts");
      const data = await res.json();
      // Bug #13 (P0): el backend sirve snake_case (word_count, is_valid,
      // created_at) → reutilizar mapScriptFromApi (lib/utils.ts) y
      // enriquecer con topic_title/topic_score/topic_status tal como las
      // sirve script_list.py (ScriptWithTopic las declara snake_case).
      const scripts = (data.scripts as Record<string, unknown>[]).map((s) => ({
        ...mapScriptFromApi(s),
        topic_title: s.topic_title as string,
        topic_score: s.topic_score as number,
        topic_status: s.topic_status as string,
      }));
      set({
        scripts,
        total: data.total,
        isLoading: false,
      });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : "Failed to load scripts",
        isLoading: false,
      });
    }
  },

  selectScript: (script) => {
    set({ selectedScript: script });
  },

  clearSelection: () => {
    set({ selectedScript: null });
  },

  clearError: () => {
    set({ error: null });
  },
}));
