"use client";

import { useState } from "react";
import { useTopicStore } from "@/store/topicStore";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Compass, Loader2 } from "lucide-react";

/** Página de descubrimiento automático de topics desde fuentes externas */
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
    <div className="animate-fade-in max-w-3xl mx-auto">
      <div className="flex items-center gap-2 text-[10px] font-mono text-cyber-cyan/60 tracking-widest uppercase mb-1">
        <span className="w-2 h-2 rounded-full bg-cyber-cyan animate-glow-pulse" />
        <span>Discovery Module</span>
      </div>
      <h1 className="text-2xl font-display font-bold text-white tracking-wide mb-6">
        Discover Topics
      </h1>

      <Card className="p-6 mb-6">
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <Input
              placeholder="Search query (leave empty for trending)..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleDiscover()}
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
            <Compass size={18} />
            {isDiscovering ? "Scanning..." : "Discover"}
          </Button>
        </div>
      </Card>

      {isDiscovering && (
        <Card className="p-8 flex items-center justify-center gap-3">
          <Loader2 size={20} className="animate-spin text-cyber-cyan" />
          <span className="text-sm font-mono text-gray-400">
            Scanning external sources...
          </span>
        </Card>
      )}

      {result && !isDiscovering && (
        <Card glow="cyan" className="p-6 space-y-3">
          <h3 className="text-sm font-display font-semibold text-white">
            Discovery Complete
          </h3>
          <div className="grid grid-cols-3 gap-4">
            <div className="p-4 rounded-lg bg-cyber-green/10 border border-cyber-green/20 text-center">
              <p className="text-2xl font-display font-bold text-cyber-green">
                {result.discovered}
              </p>
              <p className="text-[10px] font-mono text-gray-400 uppercase mt-1">
                New Topics
              </p>
            </div>
            <div className="p-4 rounded-lg bg-cyber-yellow/10 border border-cyber-yellow/20 text-center">
              <p className="text-2xl font-display font-bold text-cyber-yellow">
                {result.duplicates}
              </p>
              <p className="text-[10px] font-mono text-gray-400 uppercase mt-1">
                Duplicates
              </p>
            </div>
            <div className="p-4 rounded-lg bg-cyber-red/10 border border-cyber-red/20 text-center">
              <p className="text-2xl font-display font-bold text-cyber-red">
                {result.errors}
              </p>
              <p className="text-[10px] font-mono text-gray-400 uppercase mt-1">
                Errors
              </p>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
