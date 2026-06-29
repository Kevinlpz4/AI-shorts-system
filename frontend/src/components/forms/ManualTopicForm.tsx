"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useTopicStore } from "@/store/topicStore";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { AlertCircle, CheckCircle, Sparkles } from "lucide-react";

/** Errores de validación del formulario */
interface FormErrors {
  title?: string;
  url?: string;
}

/**
 * Formulario de creación manual de topics.
 *
 * Valida campos (title requerido, URL formato), envía al store y
 * muestra feedback visual de resultado (éxito, duplicado o error).
 */
export function ManualTopicForm() {
  const router = useRouter();
  const { createManualTopic, isLoading } = useTopicStore();

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [url, setUrl] = useState("");
  const [errors, setErrors] = useState<FormErrors>({});
  const [result, setResult] = useState<{
    success: boolean;
    isDuplicate: boolean;
  } | null>(null);

  const validate = (): boolean => {
    const newErrors: FormErrors = {};
    if (!title.trim()) {
      newErrors.title = "Title is required";
    } else if (title.trim().length < 3) {
      newErrors.title = "Title must be at least 3 characters";
    }
    if (url && !url.startsWith("http")) {
      newErrors.url = "URL must start with http:// or https://";
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setResult(null);
    const res = await createManualTopic({
      title: title.trim(),
      description: description.trim(),
      url: url.trim() || null,
    });

    setResult(res);

    if (res.success && !res.isDuplicate) {
      setTitle("");
      setDescription("");
      setUrl("");
    }
  };

  return (
    <Card className="p-6 max-w-2xl">
      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Header */}
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 rounded-lg bg-cyber-purple/20 border border-cyber-purple/30">
            <Sparkles size={20} className="text-cyber-purple" />
          </div>
          <div>
            <h2 className="text-base font-display font-bold text-white">
              Create Manual Topic
            </h2>
            <p className="text-[10px] font-mono text-gray-500">
              Add a topic manually for review and scoring
            </p>
          </div>
        </div>

        {/* Title */}
        <Input
          label="Title *"
          placeholder="Enter topic title..."
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          error={errors.title}
          maxLength={200}
        />

        {/* Description */}
        <div>
          <label className="block mb-1.5 text-xs font-mono text-gray-400 uppercase tracking-wider">
            Description
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Brief description or summary..."
            rows={3}
            maxLength={500}
            className="w-full bg-cyber-dark/60 border border-glass-border rounded-lg px-3 py-2.5 text-sm font-mono text-white placeholder-gray-500 backdrop-blur-sm focus:outline-none focus:ring-2 focus:ring-cyber-purple/50 focus:border-cyber-cyan/50 transition-all resize-none"
          />
        </div>

        {/* URL */}
        <Input
          label="URL (optional)"
          type="url"
          placeholder="https://example.com/article..."
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          error={errors.url}
        />

        {/* Submit */}
        <div className="flex items-center gap-3 pt-2">
          <Button
            type="submit"
            variant="primary"
            size="lg"
            isLoading={isLoading}
            glow
          >
            <Sparkles size={16} />
            {isLoading ? "Creating..." : "Create Topic"}
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="lg"
            onClick={() => router.push("/")}
          >
            Cancel
          </Button>
        </div>

        {/* Result feedback */}
        {result && (
          <div
            className={`p-3 rounded-lg border text-sm font-mono flex items-center gap-2 ${
              result.success && !result.isDuplicate
                ? "border-cyber-green/30 bg-cyber-green/10 text-cyber-green"
                : result.isDuplicate
                ? "border-cyber-yellow/30 bg-cyber-yellow/10 text-cyber-yellow"
                : "border-cyber-red/30 bg-cyber-red/10 text-cyber-red"
            }`}
          >
            {result.success && !result.isDuplicate ? (
              <>
                <CheckCircle size={16} />
                Topic created successfully!
              </>
            ) : result.isDuplicate ? (
              <>
                <AlertCircle size={16} />
                This topic already exists (possible duplicate)
              </>
            ) : (
              <>
                <AlertCircle size={16} />
                Failed to create topic
              </>
            )}
          </div>
        )}
      </form>
    </Card>
  );
}
