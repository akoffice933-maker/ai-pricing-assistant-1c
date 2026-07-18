/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#07080a",
        panel: "#0c0e11",
        panel2: "#101318",
        line: "#1c2129",
        line2: "#2a313c",
        lime: "#d7ff3f",
        limedim: "#aacc2e",
        mist: "#98a2ae",
        fog: "#5c6672",
        danger: "#ff5d5d",
        warn: "#ffb02e",
        sky: "#6fd3ff",
        // алиасы, чтобы не переписывать всю разметку компонентов
        base: "#07080a",
        text: "#e8ecf1",
        muted: "#98a2ae",
        good: "#d7ff3f",
        bad: "#ff5d5d",
      },
      fontFamily: {
        display: ["Unbounded", "sans-serif"],
        body: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};
