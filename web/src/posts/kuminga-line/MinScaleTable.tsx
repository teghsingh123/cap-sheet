import { useEffect, useState } from "react";
import { withBase } from "../../lib/base";

interface MinScaleEntry {
  yos: number;
  minSalary: number;
}

interface MinScaleData {
  season: string;
  scale: MinScaleEntry[];
}

const fmt = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

export function MinScaleTable() {
  const [data, setData] = useState<MinScaleData | null>(null);

  useEffect(() => {
    fetch(withBase("/data/min_scale.json"))
      .then((r) => r.json())
      .then(setData);
  }, []);

  if (!data) return null;

  // yos 0 is the rookie minimum, not a veteran minimum -- a real vet min
  // requires at least one year of service, so it's excluded here.
  const rows = data.scale.filter((row) => row.yos >= 1);
  const max = Math.max(...rows.map((row) => row.minSalary));

  return (
    <div className="min-scale-table-wrap">
      <p className="min-scale-caption">
        NBA veteran minimum salary by years of service, {data.season}
      </p>
      <div className="min-scale-bars">
        {rows.map((row) => (
          <div className="min-scale-row" key={row.yos}>
            <div className="min-scale-label">{row.yos === 10 ? "10+ yrs" : `${row.yos} yr${row.yos === 1 ? "" : "s"}`}</div>
            <div className="min-scale-track">
              <div
                className="min-scale-bar"
                style={{ width: `${(row.minSalary / max) * 100}%` }}
              />
            </div>
            <div className="min-scale-value">{fmt.format(row.minSalary)}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
