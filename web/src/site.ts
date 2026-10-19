// Site-wide settings. The name is a placeholder until the blog has a real one.
export const site = {
  name: "Cap Sheet",
  tagline: "Salary cap nerdery, with charts.",
};

export function formatDate(iso: string) {
  return new Date(iso + "T00:00:00").toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}
