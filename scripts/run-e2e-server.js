/*
 * Starts the Django dev server for the Playwright PWA smoke suite.
 *
 * Reuses the project's normal SQLite dev database and runs the existing
 * `seed_demo_content` management command first (it is idempotent — plain
 * update_or_create/get_or_create — so running it again is harmless) rather
 * than standing up a separate throwaway database. That keeps this a small
 * smoke suite instead of a parallel test-infrastructure project, per the
 * Phase A closure instructions.
 */
const { spawnSync, spawn } = require("child_process");
const path = require("path");

const root = path.resolve(__dirname, "..");
const python = process.platform === "win32"
  ? path.join(root, "venv", "Scripts", "python.exe")
  : path.join(root, "venv", "bin", "python");

const port = process.env.YTR_E2E_PORT || "8799";

function run(args) {
  const result = spawnSync(python, ["manage.py", ...args], { cwd: root, stdio: "inherit" });
  if (result.status !== 0) {
    process.exit(result.status || 1);
  }
}

run(["migrate", "--noinput"]);
run(["seed_demo_content"]);

const server = spawn(python, ["manage.py", "runserver", `127.0.0.1:${port}`, "--noreload"], {
  cwd: root,
  stdio: "inherit",
});

server.on("exit", (code) => process.exit(code || 0));
process.on("SIGTERM", () => server.kill());
process.on("SIGINT", () => server.kill());
