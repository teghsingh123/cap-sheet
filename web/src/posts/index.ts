import { lazy, type ComponentType, type LazyExoticComponent } from "react";

// Every post on the site, newest first. To publish a new one: make a folder
// under posts/ with a default-exported component, then add an entry here.
// Name the folder the same as the slug -- the GitHub Pages deploy uses the
// folder names to create each post's page (see scripts/prepare-pages.cjs).
// Each post is lazy-loaded, so its charts and data only download when
// someone actually opens it.

export interface PostMeta {
  slug: string; // URL path: /<slug>
  title: string;
  date: string; // YYYY-MM-DD
  dek: string; // one-line summary shown on the home page
  Component: LazyExoticComponent<ComponentType>;
}

export const posts: PostMeta[] = [
  {
    slug: "kuminga-line",
    title: "The Kuminga Line",
    date: "2026-08-24",
    dek: "Has a former lottery pick ever fallen to the veteran's minimum this far, this fast, while still this young? Every vet-min signing since 1991, checked.",
    Component: lazy(() => import("./kuminga-line/KumingaLine")),
  },
];

export function findPost(slug: string) {
  return posts.find((p) => p.slug === slug);
}
