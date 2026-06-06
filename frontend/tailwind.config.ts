import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        surface: "#f7f8fa",
        ink: "#17202a",
        muted: "#697586",
        line: "#d8dee8"
      }
    }
  },
  plugins: []
};

export default config;

