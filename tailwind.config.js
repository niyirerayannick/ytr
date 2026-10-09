/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./apps/**/templates/**/*.html",
    "./apps/**/*.py",
    "./static/js/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        night: "var(--night)",
        "night-2": "var(--night-2)",
        ember: "var(--ember)",
        "ember-dim": "var(--ember-dim)",
        dawn: "var(--dawn)",
        paper: "var(--paper)",
        "paper-2": "var(--paper-2)",
        river: "var(--river)",
        ink: "var(--ink)",
        "ink-soft": "var(--ink-soft)",
        "cream-ink": "var(--cream-ink)",
        line: "var(--line)",
        "line-night": "var(--line-night)",
      },
      fontFamily: {
        serif: ["Fraunces", "ui-serif", "Georgia", "serif"],
        sans: ["Work Sans", "ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "Roboto", "sans-serif"],
      },
      maxWidth: {
        site: "1180px",
      },
      keyframes: {
        fadein: { from: { opacity: 0 }, to: { opacity: 1 } },
        rise: {
          "0%": { transform: "translateY(0) scale(1)", opacity: 0 },
          "8%": { opacity: 0.9 },
          "90%": { opacity: 0 },
          "100%": { transform: "translateY(-320px) scale(0.3)", opacity: 0 },
        },
        sunrise: {
          from: { transform: "translateY(60px)", opacity: 0 },
          to: { transform: "translateY(0)", opacity: 1 },
        },
        scrollfaq: {
          from: { transform: "translateX(0)" },
          to: { transform: "translateX(-50%)" },
        },
      },
      animation: {
        fadein: "fadein 0.35s ease",
        rise: "rise 7s linear infinite",
        sunrise: "sunrise 2.4s cubic-bezier(.2,.7,.3,1) both",
        scrollfaq: "scrollfaq 42s linear infinite",
      },
    },
  },
  plugins: [],
};
