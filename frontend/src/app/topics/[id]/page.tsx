"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect } from "react";
import { useTopicStore } from "@/store/topicStore";
import { TopicDetailPanel } from "@/components/topic/TopicDetailPanel";
import { Button } from "@/components/ui/Button";
import { ArrowLeft, Loader2, AlertCircle } from "lucide-react";

/** Página de detalle individual de un topic con loading/error states */
export default function TopicDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const { selectedTopic, isLoading, loadTopicById } = useTopicStore();

  useEffect(() => {
    if (id) {
      loadTopicById(id);
    }
  }, [id, loadTopicById]);

  return (
    <div className="max-w-4xl mx-auto animate-fade-in">
      {/* Back button */}
      <div className="mb-6">
        <Button variant="ghost" size="sm" onClick={() => router.push("/")}>
          <ArrowLeft size={16} />
          Back to Dashboard
        </Button>
      </div>

      {/* Header */}
      <div className="flex items-center gap-2 text-[10px] font-mono text-cyber-cyan/60 tracking-widest uppercase mb-1">
        <span className="w-2 h-2 rounded-full bg-cyber-cyan animate-glow-pulse" />
        <span>Topic Detail • ID: {id?.slice(0, 8)}</span>
      </div>

      {/* Loading */}
      {isLoading && !selectedTopic && (
        <div className="flex items-center justify-center py-20">
          <Loader2 size={32} className="animate-spin text-cyber-cyan" />
        </div>
      )}

      {/* Error */}
      {!isLoading && !selectedTopic && (
        <div className="flex flex-col items-center justify-center py-20">
          <AlertCircle size={32} className="text-cyber-red mb-4" />
          <p className="text-sm font-mono text-gray-400">Topic not found</p>
          <p className="text-xs font-mono text-gray-500 mt-1">
            The topic with ID &quot;{id}&quot; does not exist.
          </p>
          <Button
            variant="ghost"
            size="sm"
            className="mt-4"
            onClick={() => router.push("/")}
          >
            Return to Dashboard
          </Button>
        </div>
      )}

      {/* Detail panel */}
      {selectedTopic && (
        <div className="mt-4">
          <TopicDetailPanel topicId={id} />
        </div>
      )}
    </div>
  );
}
