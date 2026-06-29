"use client";

import { ManualTopicForm } from "@/components/forms/ManualTopicForm";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { useRouter } from "next/navigation";

/** Página de creación manual de topics con formulario */
export default function CreateTopicPage() {
  const router = useRouter();

  return (
    <div className="animate-fade-in">
      {/* Back */}
      <div className="mb-6">
        <Button variant="ghost" size="sm" onClick={() => router.push("/")}>
          <ArrowLeft size={16} />
          Back to Dashboard
        </Button>
      </div>

      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-2 text-[10px] font-mono text-cyber-cyan/60 tracking-widest uppercase mb-1">
          <span className="w-2 h-2 rounded-full bg-cyber-cyan animate-glow-pulse" />
          <span>Content Creation</span>
        </div>
        <h1 className="text-2xl font-display font-bold text-white tracking-wide">
          Create Topic
        </h1>
        <p className="text-sm font-mono text-gray-400 mt-1">
          Add a topic manually to the discovery queue for review and scoring.
        </p>
      </div>

      {/* Form */}
      <ManualTopicForm />
    </div>
  );
}
