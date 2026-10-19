import { useMemo, useState } from "react";
import type { ProveItRecord } from "./types";

interface Props {
  data: ProveItRecord[];
}

const fmt = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
  notation: "compact",
});

type Tab = "bounced" | "stuck" | "flamed";

export function ProveItChart({ data }: Props) {
  const [tab, setTab] = useState<Tab>("bounced");

  const { bounced, stuck, flamed, counts } = useMemo(() => {
    const bouncedBack = data.filter((d) => d.outcome === "bounced_back").sort((a, b) => (b.multiple ?? 0) - (a.multiple ?? 0));
    const stuckAtMin = data.filter((d) => d.outcome === "stuck").sort((a, b) => (a.multiple ?? 0) - (b.multiple ?? 0));
    const flamedOut = data.filter((d) => d.outcome === "flamed_out").sort((a, b) => b.vetMinSalary - a.vetMinSalary);
    return {
      bounced: bouncedBack.slice(0, 12),
      stuck: stuckAtMin.slice(0, 12),
      flamed: flamedOut.slice(0, 12),
      counts: { bounced: bouncedBack.length, stuck: stuckAtMin.length, flamed: flamedOut.length },
    };
  }, [data]);

  const rows = tab === "bounced" ? bounced : tab === "stuck" ? stuck : flamed;
  const maxMultiple = Math.max(1, ...rows.map((r) => r.multiple ?? 1));

  return (
    <div className="prove-it">
      <p className="explorer-blurb">
        Of the {data.length} real vet-min cliffs in this dataset, {counts.bounced} players earned a real
        contract the very next season (at least 1.5x the vet-min rate), {counts.stuck} signed another
        genuine minimum deal, and {counts.flamed} were out of the league within a year, or their next
        season was too prorated to read reliably.
      </p>
      <div className="explorer-tabs">
        <button
          type="button"
          className={tab === "bounced" ? "explorer-tab active" : "explorer-tab"}
          onClick={() => setTab("bounced")}
        >
          Bounced back
        </button>
        <button
          type="button"
          className={tab === "stuck" ? "explorer-tab active" : "explorer-tab"}
          onClick={() => setTab("stuck")}
        >
          Stuck at the minimum
        </button>
        <button
          type="button"
          className={tab === "flamed" ? "explorer-tab active" : "explorer-tab"}
          onClick={() => setTab("flamed")}
        >
          Flamed out
        </button>
      </div>
      <div className="prove-it-bars">
        {rows.map((r) => (
          <div className="prove-it-row" key={`${r.brefId}-${r.year}`}>
            <div className="prove-it-label">
              {r.player} <span className="prove-it-year">'{String(r.year).slice(2)}</span>
            </div>
            <div className="prove-it-track">
              {r.multiple != null && (
                <div
                  className="prove-it-bar"
                  style={{ width: `${(r.multiple / maxMultiple) * 100}%` }}
                />
              )}
            </div>
            <div className="prove-it-value">
              {r.multiple != null && r.nextYearSalary != null
                ? `${fmt.format(r.vetMinSalary)} → ${fmt.format(r.nextYearSalary)} (${r.multiple}x)`
                : `${fmt.format(r.vetMinSalary)} → gone within a year`}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
