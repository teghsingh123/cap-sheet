// Run after `vite build` when deploying to GitHub Pages. GitHub Pages only
// serves real files, so each post folder under src/posts/ gets its own copy
// of index.html (dist/<slug>/index.html) and loads with a normal 200 status.
// 404.html catches any other address so the app can show its own
// "Not found" page.
const fs = require("fs");
const path = require("path");

const dist = path.join(__dirname, "..", "dist");
const postsDir = path.join(__dirname, "..", "src", "posts");
const index = path.join(dist, "index.html");

for (const entry of fs.readdirSync(postsDir, { withFileTypes: true })) {
  if (!entry.isDirectory()) continue;
  fs.mkdirSync(path.join(dist, entry.name), { recursive: true });
  fs.copyFileSync(index, path.join(dist, entry.name, "index.html"));
}
fs.copyFileSync(index, path.join(dist, "404.html"));
