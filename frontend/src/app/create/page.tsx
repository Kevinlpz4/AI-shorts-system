"use client";

import { ManualTopicForm } from "@/components/forms/ManualTopicForm";
import { ArrowLeft, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";

export default function CreateTopicPage() {
  const router = useRouter();

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-2 text-[10px] font-mono text-neon-cyan/50 tracking-[0.2em] uppercase mb-2">
          <Sparkles size={12} className="text-neon-cyan" />
          <span>Content Creation</span>
        </div>
        <h1 className="text-2xl font-display font-bold text-white tracking-wide">
          Create Topic
        </h1>
        <p className="text-sm font-sans text-gray-400 mt-1 font-light">
          Add a topic manually to the discovery queue for review and scoring
        </p>
      </div>

      {/* Back */}
      <div className="mb-6">
        <Button variant="ghost" size="sm" onClick={() => router.push("/")}>
          <ArrowLeft size={16} />
          Back to Dashboard
        </Button>
      </div>

      {/* Form */}
      <ManualTopicForm />
    </motion.div>
  );
}
