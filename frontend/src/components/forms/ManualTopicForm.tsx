"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useTopicStore } from "@/store/topicStore";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { motion } from "framer-motion";
import { AlertCircle, CheckCircle, Sparkles } from "lucide-react";

interface FormErrors {
  title?: string;
  url?: string;
}

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
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: "spring", stiffness: 100, damping: 20 }}
    >
      <Card glow="violet" className="p-6 max-w-2xl">
        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Header */}
          <div className="flex items-center gap-3 mb-2">
            <div className="relative p-2.5 rounded-xl bg-gradient-to-br from-neon-violet/20 to-neon-magenta/10 border border-neon-violet/30">
              <Sparkles size={20} className="text-neon-violet" />
            </div>
            <div>
              <h2 className="text-base font-display font-semibold text-white">
                Create Manual Topic
              </h2>
              <p className="text-[10px] font-mono text-gray-500">
                Add a topic for review and scoring
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
            <label className="block mb-1.5 text-[10px] font-mono text-gray-400 uppercase tracking-[0.15em]">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief description or summary..."
              rows={3}
              maxLength={500}
              className="w-full px-4 py-3 text-sm font-mono rounded-xl transition-all duration-300
                bg-glass-base backdrop-blur-xl border border-glass-border
                text-white placeholder-gray-500 resize-none
                focus:outline-none focus:border-neon-cyan/40 focus:bg-glass-light
                focus:shadow-[0_0_20px_rgba(0,229,255,0.08)]"
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
            <Button type="submit" variant="primary" size="lg" isLoading={isLoading} glow>
              <Sparkles size={16} />
              {isLoading ? "Creating..." : "Create Topic"}
            </Button>
            <Button type="button" variant="ghost" size="lg" onClick={() => router.push("/")}>
              Cancel
            </Button>
          </div>

          {/* Result feedback */}
          {result && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`p-3 rounded-xl border text-sm font-mono flex items-center gap-2 ${
                result.success && !result.isDuplicate
                  ? "border-neon-green/30 bg-neon-green/10 text-neon-green"
                  : result.isDuplicate
                    ? "border-neon-yellow/30 bg-neon-yellow/10 text-neon-yellow"
                    : "border-neon-red/30 bg-neon-red/10 text-neon-red"
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
            </motion.div>
          )}
        </form>
      </Card>
    </motion.div>
  );
}
