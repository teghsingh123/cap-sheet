import { useMemo, useState } from "react";
import type { CliffRecord } from "./types";

interface Props {
  data: CliffRecord[];
}

const fmt = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

function brefUrl(brefId: string) {
  return `https://www.basketball-reference.com/players/${brefId[0]}/${brefId}.html`;
}

export function PlayerSearch({ data }: Props) {
  const [query, setQuery] = useState("");

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (q.length < 2) return [];
    return data
      .filter((d) => d.player.toLowerCase().includes(q))
      .sort((a, b) => a.player.localeCompare(b.player) || a.year - b.year)
      .slice(0, 30);
  }, [data, query]);

  return (
    <div className="player-search">
      <input
        type="text"
        className="player-search-input"
        placeholder="Look up any player in the dataset (e.g. “Iguodala”)..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        aria-label="Search vet-min signings by player name"
      />
      {query.trim().length >= 2 && (
        <div className="player-search-results">
          {results.length === 0 ? (
            <p className="player-search-empty">No vet-min signings matched "{query}".</p>
          ) : (
            <div className="player-search-table-wrap">
            <table className="player-search-table">
              <thead>
                <tr>
                  <th>Player</th>
                  <th>Year</th>
                  <th>Age</th>
                  <th>Salary</th>
                  <th>vs. prior year</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {results.map((d) => (
                  <tr key={`${d.brefId}-${d.year}-${d.team}-${d.salary}`}>
                    <td>{d.player}</td>
                    <td>{d.year}</td>
                    <td>{d.age}</td>
                    <td>{fmt.format(d.salary)}</td>
                    <td>
                      {d.dropPct == null
                        ? "—"
                        : d.dropPct < 0
                          ? `+${Math.abs(d.dropPct)}%`
                          : `-${d.dropPct}%`}
                    </td>
                    <td>
                      <a
                        href={brefUrl(d.brefId)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="player-search-link"
                      >
                        bref &rarr;
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
