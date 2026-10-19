import { useEffect, useState } from "react";
import { BASE } from "./base";

// A tiny path-based router -- the site only has two kinds of pages (home and
// a post), so it doesn't need a routing library. <Link> lives in Link.tsx.

// The current path with the site's base folder stripped off, e.g. "/kuminga-line".
function currentPath() {
  const path = window.location.pathname;
  return path.startsWith(BASE) ? path.slice(BASE.length) || "/" : path;
}

export function usePath() {
  const [path, setPath] = useState(currentPath);
  useEffect(() => {
    const onPop = () => setPath(currentPath());
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);
  return path;
}

export function navigate(to: string) {
  window.history.pushState(null, "", BASE + to);
  window.dispatchEvent(new PopStateEvent("popstate"));
  window.scrollTo(0, 0);
}
