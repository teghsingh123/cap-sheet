import { Fragment, type ReactNode } from "react";
import { useChartData, useProveItData, useYoungFaData } from "./useChartData";
import { VetMinExplorer } from "./VetMinExplorer";
import { ProveItChart } from "./ProveItChart";
import { YoungFaScatter } from "./YoungFaScatter";
import { MinScaleTable } from "./MinScaleTable";
import { FloatImg } from "../../components/FloatImg";
import { PlayerSearch } from "./PlayerSearch";
import { story } from "./content";

// Renders a section's paragraphs, dropping each photo in right before the
// paragraph that talks about that player so the text wraps around it there.
function Paragraphs({
  paragraphs,
  figures = {},
}: {
  paragraphs: string[];
  figures?: Record<number, ReactNode>;
}) {
  return paragraphs.map((p, i) => (
    <Fragment key={i}>
      {figures[i]}
      <p>{p}</p>
    </Fragment>
  ));
}

const loading = <p>Loading chart data…</p>;

export default function KumingaLine() {
  const data = useChartData();
  const proveIt = useProveItData();
  const youngFa = useYoungFaData();

  return (
    <article>
      <section className="story-section">
        <h1>{story.intro.heading}</h1>
        <Paragraphs
          paragraphs={story.intro.paragraphs}
          figures={{
            0: (
              <FloatImg
                src="https://upload.wikimedia.org/wikipedia/commons/thumb/d/d0/Jonathan_Kuminga_2_%28cropped%29.jpg/500px-Jonathan_Kuminga_2_%28cropped%29.jpg"
                alt="Jonathan Kuminga shooting in a high school game"
                caption="Kuminga as a high school prospect"
                side="right"
              />
            ),
          }}
        />
      </section>

      <section className="story-section">
        <h2>{story.methodology.heading}</h2>
        <p>{story.methodology.paragraphs[0]}</p>
        <MinScaleTable />
        <p>{story.snags.intro}</p>
        <ul className="story-list">
          {story.snags.items.map((item) => (
            <li key={item.label}>
              <strong>{item.label}</strong> {item.text}
            </li>
          ))}
        </ul>
        <Paragraphs paragraphs={story.methodology.paragraphs.slice(1)} />
      </section>

      <div className="chart-pin">
        <h2>{story.chart.heading}</h2>
        {data ? <VetMinExplorer data={data.signings} highlightBrefId="tskitni01" /> : loading}
      </div>

      <section className="story-section">
        <h2>{story.whoDoesntCount.heading}</h2>
        <Paragraphs
          paragraphs={story.whoDoesntCount.paragraphs}
          figures={{
            0: (
              <FloatImg
                src="https://upload.wikimedia.org/wikipedia/commons/8/8b/NikolozTskitishvili2010.jpg"
                alt="Nikoloz Tskitishvili"
                caption="Nikoloz Tskitishvili, the youngest real comp"
                side="right"
              />
            ),
            2: (
              <FloatImg
                src="https://upload.wikimedia.org/wikipedia/commons/thumb/b/be/Anthony_Bennett_by_Jeremy_Rincon.jpg/500px-Anthony_Bennett_by_Jeremy_Rincon.jpg"
                alt="Anthony Bennett"
                caption="Anthony Bennett, #1 pick turned repeat vet-min signee"
                side="left"
              />
            ),
          }}
        />
      </section>

      <div className="chart-pin">
        <h2>{story.youngFa.heading}</h2>
        <p>{story.youngFa.intro}</p>
        {youngFa ? <YoungFaScatter data={youngFa.signings} /> : loading}
      </div>

      <div className="chart-pin">
        <h2>{story.proveIt.heading}</h2>
        {proveIt ? <ProveItChart data={proveIt.signings} /> : loading}
      </div>

      <section className="story-section">
        <h2>{story.buyoutCaveat.heading}</h2>
        <Paragraphs
          paragraphs={story.buyoutCaveat.paragraphs}
          figures={{
            0: (
              <FloatImg
                src="https://upload.wikimedia.org/wikipedia/commons/thumb/6/60/Chris_Webber_NBA_Asia_Challenge_2010.jpg/500px-Chris_Webber_NBA_Asia_Challenge_2010.jpg"
                alt="Chris Webber"
                caption="Chris Webber: bought out, then $661K with Detroit"
                side="right"
              />
            ),
            1: (
              <FloatImg
                src="https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/Joe_Johnson_%2851902632002%29.jpg/500px-Joe_Johnson_%2851902632002%29.jpg"
                alt="Joe Johnson"
                caption="Joe Johnson: bought out, $414K with Miami, $11M with Utah"
                side="right"
              />
            ),
          }}
        />
      </section>

      <section className="story-section">
        <h2>{story.prorationCaveat.heading}</h2>
        <Paragraphs
          paragraphs={story.prorationCaveat.paragraphs}
          figures={{
            1: (
              <FloatImg
                src="https://upload.wikimedia.org/wikipedia/commons/thumb/f/f4/Danny_Green_2023_Cleveland_Cavaliers_vs._New_York_Knicks.jpg/500px-Danny_Green_2023_Cleveland_Cavaliers_vs._New_York_Knicks.jpg"
                alt="Danny Green"
                caption="Danny Green: 2 games, then waived"
                side="right"
              />
            ),
          }}
        />
      </section>

      <section className="story-section">
        <h2>{story.deadMoneyFix.heading}</h2>
        <Paragraphs
          paragraphs={story.deadMoneyFix.paragraphs}
          figures={{
            0: (
              <FloatImg
                src="https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/DeAndre_Jordan_warmup_20131118_Clippers_v_Grizzles.jpg/500px-DeAndre_Jordan_warmup_20131118_Clippers_v_Grizzles.jpg"
                alt="DeAndre Jordan"
                caption="DeAndre Jordan: real trade, fake bounce-back"
                side="left"
              />
            ),
          }}
        />
      </section>

      <section className="story-section">
        <h2>{story.lookup.heading}</h2>
        <p>{story.lookup.intro}</p>
        {data ? <PlayerSearch data={data.signings} /> : loading}
      </section>

      <section className="story-section">
        <h2>{story.closing.heading}</h2>
        <Paragraphs paragraphs={story.closing.paragraphs} />
      </section>
    </article>
  );
}
