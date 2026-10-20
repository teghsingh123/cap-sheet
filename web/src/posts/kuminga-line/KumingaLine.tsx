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
                credit={{ by: "Position Sports, Inc.", license: "CC BY-SA 4.0" }}
              />
            ),
            3: (
              <FloatImg
                src="https://upload.wikimedia.org/wikipedia/commons/thumb/f/fd/Malik_Monk_-_51960020214_%28cropped2%29.jpg/500px-Malik_Monk_-_51960020214_%28cropped2%29.jpg"
                alt="Malik Monk with the Los Angeles Lakers"
                caption="Malik Monk on his one-year minimum with the Lakers, 2022"
                side="left"
                credit={{ by: "Erik Drost", license: "CC BY 2.0" }}
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
        <Paragraphs
          paragraphs={story.methodology.paragraphs.slice(1)}
          figures={{
            0: (
              <FloatImg
                src="https://upload.wikimedia.org/wikipedia/commons/thumb/1/1f/Ryan_Rollins%2C_Toledo_Rockets_MBB%2C_February_2022.jpg/500px-Ryan_Rollins%2C_Toledo_Rockets_MBB%2C_February_2022.jpg"
                alt="Ryan Rollins playing for Toledo"
                caption="Ryan Rollins at Toledo. His move to Washington was a trade, not a signing"
                side="right"
                credit={{ by: "MrJacon000", license: "CC BY-SA 4.0" }}
              />
            ),
          }}
        />
      </section>

      <div className="chart-pin">
        <h2>{story.chart.heading}</h2>
        {data ? <VetMinExplorer data={data.signings} highlightBrefId="bendedr01" /> : loading}
      </div>

      <section className="story-section">
        <h2>{story.whoDoesntCount.heading}</h2>
        <Paragraphs
          paragraphs={story.whoDoesntCount.paragraphs}
          figures={{
            0: (
              <FloatImg
                src="https://upload.wikimedia.org/wikipedia/commons/thumb/7/75/Dragan_Bender.JPG/500px-Dragan_Bender.JPG"
                alt="Dragan Bender playing for Maccabi Tel Aviv"
                caption="Dragan Bender, the youngest real comp, a year before the draft"
                side="right"
                credit={{ by: "Botend", license: "CC BY-SA 4.0" }}
              />
            ),
            2: (
              <FloatImg
                src="https://upload.wikimedia.org/wikipedia/commons/thumb/b/be/Anthony_Bennett_by_Jeremy_Rincon.jpg/500px-Anthony_Bennett_by_Jeremy_Rincon.jpg"
                alt="Anthony Bennett"
                caption="Anthony Bennett, #1 pick turned repeat vet-min signee"
                side="left"
                credit={{ by: "Jeremy Rincon", license: "CC BY 2.0" }}
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
                credit={{ by: "inboundpass", license: "CC BY 2.0" }}
              />
            ),
            1: (
              <FloatImg
                src="https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/Joe_Johnson_%2851902632002%29.jpg/500px-Joe_Johnson_%2851902632002%29.jpg"
                alt="Joe Johnson"
                caption="Joe Johnson: bought out, $414K with Miami, $11M with Utah"
                side="right"
                credit={{ by: "All-Pro Reels", license: "CC BY-SA 2.0" }}
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
                credit={{ by: "Erik Drost", license: "CC BY 2.0" }}
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
                credit={{ by: "Verse Photography", license: "CC BY-SA 2.0" }}
              />
            ),
          }}
        />
      </section>

      <section className="story-section">
        <h2>{story.missingSeasonsFix.heading}</h2>
        <Paragraphs
          paragraphs={story.missingSeasonsFix.paragraphs}
          figures={{
            0: (
              <FloatImg
                src="https://upload.wikimedia.org/wikipedia/commons/8/8b/NikolozTskitishvili2010.jpg"
                alt="Nikoloz Tskitishvili"
                caption="Nikoloz Tskitishvili, the first version's answer"
                side="right"
                credit={{ by: "Zorro2212", license: "CC BY 3.0" }}
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
        <Paragraphs
          paragraphs={story.closing.paragraphs}
          figures={{
            0: (
              <FloatImg
                src="https://upload.wikimedia.org/wikipedia/commons/thumb/5/58/Marquese_Chriss_%28cropped%29.jpg/500px-Marquese_Chriss_%28cropped%29.jpg"
                alt="Marquese Chriss with the Cleveland Cavaliers"
                caption="Marquese Chriss in 2019, months before his minimum deal at 22.2"
                side="left"
                credit={{ by: "Erik Drost", license: "CC BY 2.0" }}
              />
            ),
            2: (
              <FloatImg
                src="https://upload.wikimedia.org/wikipedia/commons/thumb/f/f0/Mo_Bamba_rebound_%28cropped%29.jpg/500px-Mo_Bamba_rebound_%28cropped%29.jpg"
                alt="Mo Bamba grabbing a rebound for the Orlando Magic"
                caption="Mo Bamba: $10.3 million to the minimum at 25.2"
                side="left"
                credit={{ by: "All-Pro Reels", license: "CC BY-SA 2.0" }}
              />
            ),
            4: (
              <FloatImg
                src="https://upload.wikimedia.org/wikipedia/commons/thumb/2/2a/Shaun_Livingston_with_Warriors_%28cropped%29.jpg/500px-Shaun_Livingston_with_Warriors_%28cropped%29.jpg"
                alt="Shaun Livingston with the Warriors"
                caption="Shaun Livingston: knee injury, minimum deals, three titles"
                side="right"
                credit={{ by: "Keith Allison", license: "CC BY-SA 2.0" }}
              />
            ),
          }}
        />
      </section>
    </article>
  );
}
