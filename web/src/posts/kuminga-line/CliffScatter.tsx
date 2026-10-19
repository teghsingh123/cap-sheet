import { useMemo, useRef, useState } from "react";
import { scaleLinear, scaleSqrt } from "d3-scale";
import type { CliffRecord } from "./types";

interface Props {
  /** pre-filtered rows to plot -- rows with a null dropPct are dropped internally */
  data: CliffRecord[];
  /** bref_id of a single point to call out with a distinct color + persistent label */
  highlightBrefId?: string;
  width?: number;
  height?: number;
}

const MARGIN = { top: 24, right: 24, bottom: 48, left: 56 };

function brefUrl(brefId: string) {
  return `https://www.basketball-reference.com/players/${brefId[0]}/${brefId}.html`;
}

export function CliffScatter({ data, highlightBrefId, width = 900, height = 520 }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  // `pinned` = true once a point has been clicked -- it then stays put and
  // ignores hover from other (likely overlapping) points until the user
  // clicks it again or clicks empty space. Without this, a dense cluster of
  // circles makes it nearly impossible to actually reach the "View on
  // Basketball-Reference" link: moving the mouse toward it re-triggers a
  // neighboring point's hover and swaps the tooltip out from under you.
  // Also gives touch devices (no hover at all) a way to open the tooltip.
  const [tip, setTip] = useState<{ d: CliffRecord; x: number; y: number; pinned: boolean } | null>(null);

  const visible = useMemo(
    () => data.filter((d): d is CliffRecord & { dropPct: number } => d.dropPct != null),
    [data]
  );

  const innerW = width - MARGIN.left - MARGIN.right;
  const innerH = height - MARGIN.top - MARGIN.bottom;

  // axes scaled to the visible points (with a little padding), so whatever
  // cluster is passed in fills the plot instead of sitting in a corner.
  const x = useMemo(() => {
    const ages = visible.map((d) => d.age);
    const lo = Math.floor(Math.min(...ages)) - 0.5;
    const hi = Math.ceil(Math.max(...ages)) + 0.5;
    return scaleLinear().domain([lo, hi]).range([0, innerW]);
  }, [visible, innerW]);
  const y = useMemo(() => {
    // clamp to a 5th-95th percentile band rather than the true min/max --
    // a handful of extreme outliers (e.g. a player going from a few
    // thousand dollars to a full vet-min salary, a multi-thousand-percent
    // "raise") would otherwise squash every normal point into a sliver.
    // points beyond the band are drawn pinned to the nearest edge.
    const drops = [...visible.map((d) => d.dropPct)].sort((a, b) => a - b);
    const pct = (p: number) => drops[Math.floor((drops.length - 1) * p)];
    const lo = Math.floor(Math.min(0, pct(0.05)) / 10) * 10 - 5;
    const hi = Math.min(100, Math.ceil(Math.max(0, pct(0.95)) / 5) * 5 + 5);
    return scaleLinear().domain([lo, hi]).range([innerH, 0]);
  }, [visible, innerH]);
  const clampedY = (d: number) => y(Math.max(y.domain()[0], Math.min(y.domain()[1], d)));
  const r = useMemo(() => {
    const picks = data.map((d) => d.draftPick).filter((p): p is number => p != null);
    if (picks.length === 0) return () => 4;
    return scaleSqrt()
      .domain([Math.min(...picks), Math.max(...picks)])
      .range([9, 3]); // lower pick number (better draft slot) -> bigger dot
  }, [data]);

  function posFromEvent(e: React.MouseEvent) {
    const bounds = containerRef.current?.getBoundingClientRect();
    if (!bounds) return { x: 0, y: 0 };
    // position tooltip as a % of container so it stays correctly placed even
    // though the svg itself is scaled by viewBox to an arbitrary rendered size
    return {
      x: ((e.clientX - bounds.left) / bounds.width) * 100,
      y: ((e.clientY - bounds.top) / bounds.height) * 100,
    };
  }

  function handleHover(e: React.MouseEvent, d: CliffRecord) {
    setTip((prev) => (prev?.pinned ? prev : { d, ...posFromEvent(e), pinned: false }));
  }

  function handleClick(e: React.MouseEvent, d: CliffRecord) {
    e.stopPropagation();
    setTip((prev) =>
      prev?.pinned && prev.d === d ? null : { d, ...posFromEvent(e), pinned: true }
    );
  }

  const zeroY = y(0);

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
        aria-label="Veteran minimum salary cliffs by age"
      >
        <g transform={`translate(${MARGIN.left},${MARGIN.top})`}>
          {/* axes */}
          <line x1={0} y1={innerH} x2={innerW} y2={innerH} stroke="currentColor" opacity={0.3} />
          <line x1={0} y1={0} x2={0} y2={innerH} stroke="currentColor" opacity={0.3} />
          {/* 0% reference line, useful when the domain dips negative (raises) */}
          {zeroY > 0 && zeroY < innerH && (
            <line x1={0} y1={zeroY} x2={innerW} y2={zeroY} stroke="currentColor" opacity={0.15} strokeDasharray="3,3" />
          )}
          {x.ticks(6).map((t) => (
            <text key={t} x={x(t)} y={innerH + 20} textAnchor="middle" fontSize={12} opacity={0.7}>
              {t}
            </text>
          ))}
          {y.ticks(5).map((t) => (
            <text key={t} x={-10} y={y(t)} textAnchor="end" dominantBaseline="middle" fontSize={12} opacity={0.7}>
              {t}%
            </text>
          ))}
          <text x={innerW / 2} y={innerH + 40} textAnchor="middle" fontSize={13} opacity={0.85}>
            Age at signing
          </text>
          <text
            x={-innerH / 2}
            y={-40}
            textAnchor="middle"
            fontSize={13}
            opacity={0.85}
            transform={`rotate(-90)`}
          >
            Salary change from prior season (% drop)
          </text>

          {/* points */}
          {visible.map((d) => {
            const isHighlighted = d.brefId === highlightBrefId;
            const isActive = tip?.d === d;
            return (
              <circle
                key={`${d.brefId}-${d.year}-${d.team}-${d.salary}`}
                cx={x(d.age)}
                cy={clampedY(d.dropPct)}
                r={isHighlighted ? 10 : d.draftPick != null ? r(d.draftPick) : 3}
                fill={isHighlighted ? "#facc15" : d.isKumingaComp ? "var(--accent)" : "currentColor"}
                fillOpacity={isHighlighted ? 1 : isActive ? 1 : d.isKumingaComp ? 0.85 : 0.25}
                stroke={isHighlighted ? "#a16207" : isActive ? "var(--accent)" : "none"}
                strokeWidth={2}
                style={{ cursor: "pointer" }}
                onMouseEnter={(e) => handleHover(e, d)}
                onMouseMove={(e) => handleHover(e, d)}
                onClick={(e) => handleClick(e, d)}
              />
            );
          })}

          {/* persistent label for the highlighted point, drawn above so it's never hidden by other dots */}
          {visible
            .filter((d) => d.brefId === highlightBrefId)
            .map((d) => (
              <text
                key={`label-${d.brefId}`}
                x={x(d.age)}
                y={clampedY(d.dropPct) - 16}
                textAnchor="middle"
                fontSize={13}
                fontWeight={700}
                fill="#a16207"
                style={{ pointerEvents: "none" }}
              >
                {d.player}
              </text>
            ))}
        </g>
      </svg>

      {tip && (
        <div
          className={tip.pinned ? "chart-tooltip chart-tooltip-pinned" : "chart-tooltip"}
          style={{ left: `${tip.x}%`, top: `${tip.y}%` }}
          onClick={(e) => e.stopPropagation()}
        >
          {tip.pinned && (
            <button
              type="button"
              className="chart-tooltip-close"
              aria-label="Close"
              onClick={(e) => {
                e.stopPropagation();
                setTip(null);
              }}
            >
              ×
            </button>
          )}
          <strong>{tip.d.player}</strong>
          <span>
            {tip.d.year} · age {tip.d.age} ·{" "}
            {tip.d.dropPct != null && tip.d.dropPct < 0
              ? `${Math.abs(tip.d.dropPct)}% raise`
              : `${tip.d.dropPct}% drop`}
            {tip.d.draftPick ? ` · pick #${tip.d.draftPick}` : ""}
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
    </div>
  );
}
