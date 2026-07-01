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
        // ── Base — deep space ──
        base: {
          900: "#020617",
          800: "#07111F",
          700: "#08131F",
          600: "#0A1A2E",
          500: "#0D2240",
        },
        // ── Glass surfaces ──
        glass: {
          base: "rgba(255, 255, 255, 0.04)",
          light: "rgba(255, 255, 255, 0.06)",
          medium: "rgba(255, 255, 255, 0.08)",
          strong: "rgba(255, 255, 255, 0.12)",
          border: "rgba(255, 255, 255, 0.08)",
          "border-hover": "rgba(255, 255, 255, 0.15)",
          "border-active": "rgba(255, 255, 255, 0.2)",
        },
        // ── Neon accents — premium cyberpunk ──
        neon: {
          cyan: "#00E5FF",
          "blue-light": "#6EE7FF",
          violet: "#7C3AED",
          purple: "#A855F7",
          magenta: "#EC4899",
          fuchsia: "#D946EF",
          turquoise: "#14EAD4",
          green: "#34D399",
          yellow: "#FBBF24",
          red: "#FB7185",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        display: ["Space Grotesk", "Inter", "system-ui", "sans-serif"],
        mono: ["IBM Plex Mono", "JetBrains Mono", "monospace"],
      },
      boxShadow: {
        glass: "0 8px 32px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(255, 255, 255, 0.05)",
        "glass-lg":
          "0 16px 48px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.06)",
        "glass-xl":
          "0 24px 64px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(255, 255, 255, 0.08)",
        "neon-cyan": "0 0 20px rgba(0, 229, 255, 0.15), 0 0 40px rgba(0, 229, 255, 0.05)",
        "neon-violet":
          "0 0 20px rgba(124, 58, 237, 0.15), 0 0 40px rgba(124, 58, 237, 0.05)",
        "neon-magenta":
          "0 0 20px rgba(236, 72, 153, 0.15), 0 0 40px rgba(236, 72, 153, 0.05)",
        "neon-turquoise":
          "0 0 20px rgba(20, 234, 212, 0.15), 0 0 40px rgba(20, 234, 212, 0.05)",
        "neon-green":
          "0 0 20px rgba(52, 211, 153, 0.15), 0 0 40px rgba(52, 211, 153, 0.05)",
        "neon-red":
          "0 0 20px rgba(251, 113, 133, 0.15), 0 0 40px rgba(251, 113, 133, 0.05)",
        "inner-glow":
          "inset 0 1px 0 rgba(255, 255, 255, 0.1), inset 0 -1px 0 rgba(0, 0, 0, 0.3)",
      },
      animation: {
        "fade-in": "fade-in 0.5s ease-out",
        "fade-in-up": "fade-in-up 0.5s ease-out",
        "fade-in-down": "fade-in-down 0.4s ease-out",
        "slide-up": "slide-up 0.4s ease-out",
        "slide-in-right": "slide-in-right 0.3s ease-out",
        "scale-in": "scale-in 0.2s ease-out",
        "glow-pulse": "glow-pulse 3s ease-in-out infinite",
        "glow-soft": "glow-soft 4s ease-in-out infinite",
        "orb-float": "orb-float 20s ease-in-out infinite",
        "orb-float-2": "orb-float-2 25s ease-in-out infinite",
        "orb-float-3": "orb-float-3 30s ease-in-out infinite",
        "grid-scroll": "grid-scroll 60s linear infinite",
      },
      keyframes: {
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        "fade-in-up": {
          "0%": { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in-down": {
          "0%": { opacity: "0", transform: "translateY(-10px)" },
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
        "scale-in": {
          "0%": { opacity: "0", transform: "scale(0.95)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        "glow-pulse": {
          "0%, 100%": { opacity: "1", filter: "brightness(1)" },
          "50%": { opacity: "0.7", filter: "brightness(1.4)" },
        },
        "glow-soft": {
          "0%, 100%": { opacity: "0.6", filter: "brightness(1)" },
          "50%": { opacity: "1", filter: "brightness(1.2)" },
        },
        "orb-float": {
          "0%, 100%": { transform: "translate(0, 0) scale(1)" },
          "25%": { transform: "translate(50px, -80px) scale(1.1)" },
          "50%": { transform: "translate(-30px, -40px) scale(0.9)" },
          "75%": { transform: "translate(80px, 30px) scale(1.05)" },
        },
        "orb-float-2": {
          "0%, 100%": { transform: "translate(0, 0) scale(1)" },
          "33%": { transform: "translate(-60px, 50px) scale(1.15)" },
          "66%": { transform: "translate(40px, -60px) scale(0.85)" },
        },
        "orb-float-3": {
          "0%, 100%": { transform: "translate(0, 0) scale(1)" },
          "50%": { transform: "translate(70px, 40px) scale(1.1)" },
        },
        "grid-scroll": {
          "0%": { transform: "translateY(0)" },
          "100%": { transform: "translateY(-50%)" },
        },
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "glass-gradient":
          "linear-gradient(180deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.02) 100%)",
        "glass-shine":
          "linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.08) 50%, transparent 100%)",
        "neon-gradient-cyan":
          "linear-gradient(135deg, rgba(0,229,255,0.2), rgba(110,239,255,0.1))",
        "neon-gradient-violet":
          "linear-gradient(135deg, rgba(124,58,237,0.2), rgba(168,85,247,0.1))",
        "neon-gradient-magenta":
          "linear-gradient(135deg, rgba(236,72,153,0.2), rgba(217,70,239,0.1))",
        "noise":
          "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.05'/%3E%3C/svg%3E\")",
      },
      backgroundSize: {
        grid: "60px 60px",
      },
      transitionDuration: {
        "400": "400ms",
      },
    },
  },
  plugins: [],
};

export default config;
