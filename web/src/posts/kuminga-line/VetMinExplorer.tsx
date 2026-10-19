import { useMemo, useState } from "react";
import { CliffScatter } from "./CliffScatter";
import type { CliffRecord } from "./types";

interface Props {
  data: CliffRecord[];
  highlightBrefId?: string;
}

type View = "all" | "cliffs" | "top";

const VIEWS: { key: View; label: string; blurb: string }[] = [
  {
    key: "all",
    label: "Every vet-min signing",
    blurb:
      "Every real veteran-minimum signing with a prior-season salary to compare against. That includes players who actually got a raise (below the 0% line), like someone coming off a two-way contract.",
  },
  {
    key: "cliffs",
    label: "Real pay cuts only",
    blurb:
      "Same data, filtered down to real salary cliffs: players who took an actual pay cut to sign for the minimum. Raises, like going from a two-way deal to the vet minimum, are left out.",
  },
  {
    key: "top",
    label: "Former top-10 picks",
    blurb:
      "Narrowed further to players with real draft pedigree: top-10 picks who still fell to a vet-min pay cut before turning 27. These are the real Kuminga comps.",
  },
];

export function VetMinExplorer({ data, highlightBrefId }: Props) {
  const [view, setView] = useState<View>("top");

  const visible = useMemo(() => {
    switch (view) {
      case "all":
        return data.filter((d) => d.dropPct != null);
      case "cliffs":
        return data.filter((d) => d.dropPct != null && d.dropPct > 0);
      case "top":
        return data.filter(
          (d) =>
            (d.isKumingaComp && d.draftPick != null && d.draftPick <= 10) ||
            d.brefId === highlightBrefId
        );
    }
  }, [data, view, highlightBrefId]);

  const active = VIEWS.find((v) => v.key === view)!;

  return (
    <div className="explorer">
      <div className="explorer-tabs">
        {VIEWS.map((v) => (
          <button
            key={v.key}
            type="button"
            className={v.key === view ? "explorer-tab active" : "explorer-tab"}
            onClick={() => setView(v.key)}
          >
            {v.label}
          </button>
        ))}
      </div>
      <p className="explorer-blurb">{active.blurb}</p>
      <CliffScatter data={visible} highlightBrefId={highlightBrefId} />
    </div>
  );
}
