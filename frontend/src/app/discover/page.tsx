"use client";

import { useState } from "react";
import { useTopicStore } from "@/store/topicStore";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { motion } from "framer-motion";
import { Compass, Loader2, Sparkles, CheckCircle2, XCircle, Copy } from "lucide-react";

export default function DiscoverPage() {
  const { discoverTopics, isDiscovering } = useTopicStore();
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<{
    discovered: number;
    duplicates: number;
    errors: number;
  } | null>(null);

  const handleDiscover = async () => {
    const res = await discoverTopics(query || undefined);
    setResult({
      discovered: res.discovered.length,
      duplicates: res.duplicates.length,
      errors: res.errors.length,
    });
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="max-w-3xl mx-auto"
    >
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-2 text-[10px] font-mono text-neon-cyan/50 tracking-[0.2em] uppercase mb-2">
          <Sparkles size={12} className="text-neon-cyan" />
          <span>Discovery Module</span>
        </div>
        <h1 className="text-2xl font-display font-bold text-white tracking-wide">
          Discover Topics
        </h1>
        <p className="text-sm font-sans text-gray-400 mt-1 font-light">
          Scan external sources for trending topics and ideas
        </p>
      </div>

      {/* Search card */}
      <Card glow="cyan" className="p-6 mb-6">
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <Input
              placeholder="Search query (leave empty for trending)..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleDiscover()}
              icon={<Compass size={16} />}
            />
          </div>
          <Button
            variant="primary"
            size="lg"
            onClick={handleDiscover}
            isLoading={isDiscovering}
            disabled={isDiscovering}
            glow
          >
            {isDiscovering ? "Scanning..." : "Discover"}
          </Button>
        </div>
      </Card>

      {/* Loading state */}
      {isDiscovering && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Card className="p-8 flex flex-col items-center justify-center gap-4">
            <div className="relative">
              <Loader2 size={28} className="animate-spin text-neon-cyan" />
              <span className="absolute inset-0 animate-ping rounded-full bg-neon-cyan/20" />
            </div>
            <div className="text-center">
              <p className="text-sm font-mono text-gray-400">
                Scanning external sources...
              </p>
              <p className="text-xs font-mono text-gray-600 mt-1">
                Fetching topics from RSS feeds and research sources
              </p>
            </div>
          </Card>
        </motion.div>
      )}

      {/* Results */}
      {result && !isDiscovering && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ type: "spring", stiffness: 100, damping: 20 }}
        >
          <Card glow="cyan" className="p-6">
            <div className="flex items-center gap-2 mb-4">
              <CheckCircle2 size={18} className="text-neon-green" />
              <h3 className="text-sm font-display font-semibold text-white">
                Discovery Complete
              </h3>
            </div>

            <div className="grid grid-cols-3 gap-4">
              {/* New topics */}
              <div className="relative glass rounded-xl p-4 text-center overflow-hidden">
                <span className="absolute inset-0 bg-glass-shine" />
                <div className="relative">
                  <p className="text-2xl font-display font-bold text-neon-green">
                    {result.discovered}
                  </p>
                  <p className="text-[10px] font-mono text-gray-400 uppercase tracking-[0.15em] mt-1">
                    New Topics
                  </p>
                </div>
              </div>

              {/* Duplicates */}
              <div className="relative glass rounded-xl p-4 text-center overflow-hidden">
                <span className="absolute inset-0 bg-glass-shine" />
                <div className="relative">
                  <p className="text-2xl font-display font-bold text-neon-yellow">
                    {result.duplicates}
                  </p>
                  <p className="text-[10px] font-mono text-gray-400 uppercase tracking-[0.15em] mt-1">
                    Duplicates
                  </p>
                </div>
              </div>

              {/* Errors */}
              <div className="relative glass rounded-xl p-4 text-center overflow-hidden">
                <span className="absolute inset-0 bg-glass-shine" />
                <div className="relative">
                  <p className="text-2xl font-display font-bold text-neon-red">
                    {result.errors}
                  </p>
                  <p className="text-[10px] font-mono text-gray-400 uppercase tracking-[0.15em] mt-1">
                    Errors
                  </p>
                </div>
              </div>
            </div>
          </Card>
        </motion.div>
      )}
    </motion.div>
  );
}
