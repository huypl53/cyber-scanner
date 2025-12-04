import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        // SOC Dark Theme Colors
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        // Cybersecurity Semantic Colors
        threat: {
          low: "#06b6d4", // Cyan - Low/Normal traffic
          medium: "#f59e0b", // Amber - Medium threats
          high: "#ef4444", // Red - High threats
          critical: "#dc2626", // Dark red - Critical attacks
        },
        status: {
          safe: "#10b981", // Green - Safe/Normal
          warning: "#f59e0b", // Amber - Warning
          danger: "#ef4444", // Red - Danger
          info: "#3b82f6", // Blue - Info
        },
        // Terminal/Technical Colors
        terminal: {
          bg: "#0a0f1e",
          text: "#e2e8f0",
          accent: "#06b6d4",
          error: "#ef4444",
          success: "#10b981",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "Inter", "system-ui", "sans-serif"],
        mono: ["var(--font-roboto-mono)", "Roboto Mono", "Courier New", "monospace"],
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
        pulse: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.5" },
        },
        "pulse-glow": {
          "0%, 100%": {
            opacity: "1",
            boxShadow: "0 0 8px rgba(6, 182, 212, 0.5)",
          },
          "50%": {
            opacity: "0.8",
            boxShadow: "0 0 16px rgba(6, 182, 212, 0.8)",
          },
        },
        "fade-in": {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
        "slide-in-right": {
          from: { transform: "translateX(100%)", opacity: "0" },
          to: { transform: "translateX(0)", opacity: "1" },
        },
        "slide-in-left": {
          from: { transform: "translateX(-100%)", opacity: "0" },
          to: { transform: "translateX(0)", opacity: "1" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        pulse: "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "pulse-glow": "pulse-glow 2s ease-in-out infinite",
        "fade-in": "fade-in 0.3s ease-in-out",
        "slide-in-right": "slide-in-right 0.3s ease-out",
        "slide-in-left": "slide-in-left 0.3s ease-out",
      },
      boxShadow: {
        glow: "0 0 8px rgba(6, 182, 212, 0.5)",
        "glow-lg": "0 0 16px rgba(6, 182, 212, 0.6)",
        "glow-red": "0 0 8px rgba(239, 68, 68, 0.5)",
        "glow-red-lg": "0 0 16px rgba(239, 68, 68, 0.6)",
        "glow-green": "0 0 8px rgba(16, 185, 129, 0.5)",
        "glow-green-lg": "0 0 16px rgba(16, 185, 129, 0.6)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
export default config;
