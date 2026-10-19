import { useMemo, useRef, useState } from "react";
import { scaleLinear, scaleLog } from "d3-scale";
import type { YoungFaRecord } from "./types";

interface KumingaMarker {
  label: string;
  age: number;
  /** where to actually plot it on the x axis -- separate from `age` so two
   * markers at the same real age (rejected offer vs. signed deal, both 22)
   * don't render as fully overlapping, unclickable circles */
  plotAge: number;
  salary: number;
  note: string;
  /** which side of the dot the label sits on -- the two Warriors markers are
   * only a few pixels apart, so their labels go out to opposite sides */
  labelSide: "above" | "left" | "right";
}

// The real/rumored numbers behind Kuminga's own free agency, for direct
// comparison against a decade of actual 21-25-year-old contract signings.
// Sourced from reporting on his 2025 RFA negotiation and 2026 UFA situation
// (see content.ts intro for the same figures with citations in context).
const KUMINGA_MARKERS: KumingaMarker[] = [
  { label: "Rejected Warriors offer", age: 22, plotAge: 21.82, salary: 25_066_667, note: "3yr/$75.2M offer, turned down", labelSide: "left" },
  { label: "Signed Warriors deal", age: 22, plotAge: 22.18, salary: 24_250_000, note: "2yr/$48.5M, what he actually got", labelSide: "right" },
  { label: "Rumored vet-min outcome", age: 23, plotAge: 23, salary: 2_845_883, note: "5-YOS veteran minimum for 2026-27", labelSide: "above" },
];

interface Props {
  data: YoungFaRecord[];
  width?: number;
  height?: number;
}

const MARGIN = { top: 24, right: 24, bottom: 48, left: 64 };

const fmtCompact = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 1,
  notation: "compact",
});
const fmtFull = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

function brefUrl(brefId: string) {
  return `https://www.basketball-reference.com/players/${brefId[0]}/${brefId}.html`;
}

type Tip =
  | { kind: "player"; d: YoungFaRecord; x: number; y: number; pinned: boolean }
  | { kind: "kuminga"; d: KumingaMarker; x: number; y: number; pinned: boolean };

export function YoungFaScatter({ data, width = 900, height = 520 }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  // see CliffScatter.tsx for why pinning-on-click exists -- overlapping
  // points otherwise make the bref link unreachable, and touch devices have
  // no hover at all.
  const [tip, setTip] = useState<Tip | null>(null);

  const innerW = width - MARGIN.left - MARGIN.right;
  const innerH = height - MARGIN.top - MARGIN.bottom;

  const x = useMemo(() => scaleLinear().domain([20.5, 25.5]).range([0, innerW]), [innerW]);
  const y = useMemo(() => {
    const salaries = data.map((d) => d.salary).filter((s) => s > 0);
    const kumingaMax = Math.max(...KUMINGA_MARKERS.map((m) => m.salary));
    const lo = Math.min(...salaries, KUMINGA_MARKERS[2].salary) * 0.8;
    const hi = Math.max(...salaries, kumingaMax) * 1.15;
    return scaleLog().domain([lo, hi]).range([innerH, 0]);
  }, [data, innerH]);

  const yTicks = [1_000_000, 3_000_000, 10_000_000, 30_000_000, 60_000_000].filter(
    (t) => t >= y.domain()[0] && t <= y.domain()[1]
  );

  function posFromEvent(e: React.MouseEvent) {
    const bounds = containerRef.current?.getBoundingClientRect();
    if (!bounds) return { x: 0, y: 0 };
    return {
      x: ((e.clientX - bounds.left) / bounds.width) * 100,
      y: ((e.clientY - bounds.top) / bounds.height) * 100,
    };
  }
  function handleHoverPlayer(e: React.MouseEvent, d: YoungFaRecord) {
    setTip((prev) => (prev?.pinned ? prev : { kind: "player", d, ...posFromEvent(e), pinned: false }));
  }
  function handleHoverKuminga(e: React.MouseEvent, d: KumingaMarker) {
    setTip((prev) => (prev?.pinned ? prev : { kind: "kuminga", d, ...posFromEvent(e), pinned: false }));
  }
  function handleClickPlayer(e: React.MouseEvent, d: YoungFaRecord) {
    e.stopPropagation();
    setTip((prev) =>
      prev?.pinned && prev.kind === "player" && prev.d === d
        ? null
        : { kind: "player", d, ...posFromEvent(e), pinned: true }
    );
  }
  function handleClickKuminga(e: React.MouseEvent, d: KumingaMarker) {
    e.stopPropagation();
    setTip((prev) =>
      prev?.pinned && prev.kind === "kuminga" && prev.d === d
        ? null
        : { kind: "kuminga", d, ...posFromEvent(e), pinned: true }
    );
  }

  return (
    <div
      className="chart-container"
      ref={containerRef}
      onMouseLeave={() => setTip((prev) => (prev?.pinned ? prev : null))}
      onClick={() => setTip((prev) => (prev?.pinned ? null : prev))}
    >
      <svg
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="xMidYMid meet"
        role="img"
        aria-label="Contract value by age for players 21-25, last decade, with Kuminga's numbers marked"
      >
        <g transform={`translate(${MARGIN.left},${MARGIN.top})`}>
          <line x1={0} y1={innerH} x2={innerW} y2={innerH} stroke="currentColor" opacity={0.3} />
          <line x1={0} y1={0} x2={0} y2={innerH} stroke="currentColor" opacity={0.3} />
          {[21, 22, 23, 24, 25].map((t) => (
            <text key={t} x={x(t)} y={innerH + 20} textAnchor="middle" fontSize={12} opacity={0.7}>
              {t}
            </text>
          ))}
          {yTicks.map((t) => (
            <text key={t} x={-10} y={y(t)} textAnchor="end" dominantBaseline="middle" fontSize={12} opacity={0.7}>
              {fmtCompact.format(t)}
            </text>
          ))}
          <text x={innerW / 2} y={innerH + 40} textAnchor="middle" fontSize={13} opacity={0.85}>
            Age at signing
          </text>
          <text
            x={-innerH / 2}
            y={-48}
            textAnchor="middle"
            fontSize={13}
            opacity={0.85}
            transform="rotate(-90)"
          >
            New contract salary (log scale)
          </text>

          {/* the decade of comps */}
          {data.map((d) => (
            <circle
              key={`${d.brefId}-${d.year}`}
              cx={x(d.age)}
              cy={y(Math.max(d.salary, y.domain()[0]))}
              r={3}
              fill="currentColor"
              fillOpacity={tip?.kind === "player" && tip.d === d ? 0.9 : 0.2}
              style={{ cursor: "pointer" }}
              onMouseEnter={(e) => handleHoverPlayer(e, d)}
              onMouseMove={(e) => handleHoverPlayer(e, d)}
              onClick={(e) => handleClickPlayer(e, d)}
            />
          ))}

          {/* Kuminga's real/rumored numbers, called out distinctly */}
          {KUMINGA_MARKERS.map((m) => (
            <g key={m.label}>
              <circle
                cx={x(m.plotAge)}
                cy={y(m.salary)}
                r={9}
                fill="#facc15"
                stroke="#a16207"
                strokeWidth={2}
                style={{ cursor: "pointer" }}
                onMouseEnter={(e) => handleHoverKuminga(e, m)}
                onMouseMove={(e) => handleHoverKuminga(e, m)}
                onClick={(e) => handleClickKuminga(e, m)}
              />
              <text
                x={x(m.plotAge) + (m.labelSide === "left" ? -14 : m.labelSide === "right" ? 14 : 0)}
                y={m.labelSide === "above" ? y(m.salary) - 14 : y(m.salary)}
                textAnchor={m.labelSide === "left" ? "end" : m.labelSide === "right" ? "start" : "middle"}
                dominantBaseline={m.labelSide === "above" ? "auto" : "middle"}
                fontSize={11}
                fontWeight={700}
                fill="#a16207"
                style={{ pointerEvents: "none" }}
              >
                {m.label}
              </text>
            </g>
          ))}
        </g>
      </svg>

      {tip?.kind === "player" && (
        <div
          className={tip.pinned ? "chart-tooltip chart-tooltip-pinned" : "chart-tooltip"}
          style={{ left: `${tip.x}%`, top: `${tip.y}%` }}
          onClick={(e) => e.stopPropagation()}
        >
          {tip.pinned && (
            <button type="button" className="chart-tooltip-close" aria-label="Close" onClick={() => setTip(null)}>
              ×
            </button>
          )}
          <strong>{tip.d.player}</strong>
          <span>
            {tip.d.year} · age {tip.d.age} · {fmtFull.format(tip.d.salary)}
          </span>
          <a
            className="chart-tooltip-link"
            href={brefUrl(tip.d.brefId)}
            target="_blank"
            rel="noopener noreferrer"
          >
            View on Basketball-Reference →
          </a>
        </div>
      )}
      {tip?.kind === "kuminga" && (
        <div
          className={tip.pinned ? "chart-tooltip chart-tooltip-pinned" : "chart-tooltip"}
          style={{ left: `${tip.x}%`, top: `${tip.y}%` }}
          onClick={(e) => e.stopPropagation()}
        >
          {tip.pinned && (
            <button type="button" className="chart-tooltip-close" aria-label="Close" onClick={() => setTip(null)}>
              ×
            </button>
          )}
          <strong>Jonathan Kuminga</strong>
          <span>{tip.d.note}</span>
          <span>{fmtFull.format(tip.d.salary)}</span>
        </div>
      )}
    </div>
  );
}
