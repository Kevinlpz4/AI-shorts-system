import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // ── Cyberpunk Palette ──
        cyber: {
          black: "#0B0F1A",
          dark: "#111827",
          navy: "#0F172A",
          slate: "#1E293B",
          gray: "#334155",
          // Neon accents
          magenta: "#FF00FF",
          cyan: "#00F0FF",
          purple: "#8B5CF6",
          violet: "#7C3AED",
          green: "#00FF88",
          yellow: "#FFD700",
          red: "#FF3355",
          orange: "#FF6B35",
        },
        // ── Glass / Frost ──
        glass: {
          white: "rgba(255, 255, 255, 0.05)",
          light: "rgba(255, 255, 255, 0.08)",
          medium: "rgba(255, 255, 255, 0.12)",
          border: "rgba(255, 255, 255, 0.15)",
        },
      },
      fontFamily: {
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
        display: ["Orbitron", "JetBrains Mono", "monospace"],
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      boxShadow: {
        "neon-magenta": "0 0 15px rgba(255, 0, 255, 0.3), 0 0 30px rgba(255, 0, 255, 0.1)",
        "neon-cyan": "0 0 15px rgba(0, 240, 255, 0.3), 0 0 30px rgba(0, 240, 255, 0.1)",
        "neon-purple": "0 0 15px rgba(139, 92, 246, 0.3), 0 0 30px rgba(139, 92, 246, 0.1)",
        "neon-green": "0 0 15px rgba(0, 255, 136, 0.3), 0 0 30px rgba(0, 255, 136, 0.1)",
        "neon-red": "0 0 15px rgba(255, 51, 85, 0.3), 0 0 30px rgba(255, 51, 85, 0.1)",
        "glass": "0 8px 32px rgba(0, 0, 0, 0.4)",
      },
      animation: {
        "glow-pulse": "glow-pulse 2s ease-in-out infinite",
        "fade-in": "fade-in 0.3s ease-out",
        "slide-up": "slide-up 0.4s ease-out",
        "slide-in-right": "slide-in-right 0.3s ease-out",
        "neon-flicker": "neon-flicker 3s ease-in-out infinite",
        "scan-line": "scan-line 8s linear infinite",
        "pulse-slow": "pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
      keyframes: {
        "glow-pulse": {
          "0%, 100%": { opacity: "1", filter: "brightness(1)" },
          "50%": { opacity: "0.7", filter: "brightness(1.3)" },
        },
        "fade-in": {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "slide-up": {
          "0%": { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "slide-in-right": {
          "0%": { opacity: "0", transform: "translateX(20px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        "neon-flicker": {
          "0%, 100%": { opacity: "1" },
          "41%": { opacity: "1" },
          "42%": { opacity: "0.8" },
          "43%": { opacity: "1" },
          "45%": { opacity: "0.6" },
          "46%": { opacity: "1" },
          "91%": { opacity: "1" },
          "92%": { opacity: "0.4" },
          "93%": { opacity: "1" },
        },
        "scan-line": {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(100vh)" },
        },
      },
      backgroundImage: {
        "cyber-grid":
          "linear-gradient(rgba(0, 240, 255, 0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 240, 255, 0.03) 1px, transparent 1px)",
        "cyber-glow":
          "radial-gradient(ellipse at 50% 0%, rgba(139, 92, 246, 0.15) 0%, transparent 60%)",
      },
      backgroundSize: {
        "grid": "40px 40px",
      },
      backdropBlur: {
        "xs": "2px",
      },
    },
  },
  plugins: [],
};

export default config;
