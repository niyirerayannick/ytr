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
        night: "#1A1230",
        "night-2": "#241A3D",
        ember: "#E4572E",
        "ember-dim": "#C24A24",
        dawn: "#F6B93B",
        paper: "#FBF7F0",
        "paper-2": "#F1E9D8",
        river: "#1E6E71",
        ink: "#241A3D",
        "ink-soft": "#544A6C",
        "cream-ink": "#F6EFE0",
        line: "rgba(36,26,61,0.15)",
        "line-night": "rgba(246,239,224,0.16)",
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
