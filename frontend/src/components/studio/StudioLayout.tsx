"use client";

import { TopicQueue } from "./TopicQueue";
import { ConfigPanel } from "./ConfigPanel";
import { OutputPanel } from "./OutputPanel";

/**
 * 3-column layout for the Script Studio.
 *
 * - Left:   Topic queue (approved topics waiting for scripts)
 * - Center: Configuration panel (duration, tone, niche + generate)
 * - Right:  Output panel (generated script display + actions)
 */
export function StudioLayout() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-12rem)]">
      {/* Left column — Topic queue */}
      <div className="lg:col-span-1 min-h-0 overflow-hidden">
        <TopicQueue />
      </div>

      {/* Center column — Config */}
      <div className="lg:col-span-1 min-h-0 overflow-y-auto">
        <ConfigPanel />
      </div>

      {/* Right column — Output */}
      <div className="lg:col-span-1 min-h-0 overflow-y-auto">
        <OutputPanel />
      </div>
    </div>
  );
}
