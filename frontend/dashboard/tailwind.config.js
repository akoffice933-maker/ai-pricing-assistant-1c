/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        base: "#14181B",
        panel: "#1B2125",
        panel2: "#20272B",
        line: "#2C3438",
        accent: "#C0622A",
        accentSoft: "#E08A52",
        accentDim: "#3A2A22",
        text: "#EDEFF0",
        muted: "#8B959B",
        good: "#4FAE7C",
        warn: "#E0A83E",
        bad: "#D9634F",
      },
      fontFamily: {
        display: ["Manrope", "sans-serif"],
        body: ["Inter", "sans-serif"],
      },
    },
  },
  plugins: [],
};
