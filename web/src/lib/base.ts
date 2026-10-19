// The site can be served from a subfolder (GitHub Pages serves it at
// /cap-sheet/), so every absolute path to a page or a public/ file goes
// through here. BASE is "" when the site is served from the domain root.
export const BASE = import.meta.env.BASE_URL.replace(/\/$/, "");

export function withBase(path: string) {
  return BASE + path;
}
