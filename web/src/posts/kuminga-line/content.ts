// All narrative copy for the story, in one place. KumingaLine.tsx reads from
// this file instead of having text hardcoded inline in JSX.

export const story = {
  intro: {
    heading: "The Kuminga Line",
    paragraphs: [
      "Jonathan Kuminga is 23 years old, and both of his last two contract negotiations have gone sideways. In 2025, he was a restricted free agent with Golden State, and he reportedly turned down a lucrative offer of up to 3 years, $75 million. The contract dispute lingered throughout the summer and partway into training camp, until Kuminga's agent, Aaron Turner, agreed to a 2-year, $48.5 million contract with a team option for the second year.",
      "Then, at the February trade deadline, Golden State dealt him and veteran shooting guard Buddy Hield to Atlanta for big man Kristaps Porzingis. At the end of the season, the Hawks declined his $24.3 million team option for 2026-27, making him an unrestricted free agent.",
      "Although Kuminga is an unrestricted free agent, the Hawks retained his Bird rights, which transferred from the Warriors in the trade. This means the Hawks cannot match offers other teams give him, but they can exceed the salary cap to keep him on the roster. Other interested teams, like the Lakers and Cavaliers, cannot exceed their salary cap to sign him, except through smaller exceptions like the mid-level, unless Atlanta agrees to a sign-and-trade.",
      "Despite being young and freakishly athletic, Kuminga has seen the money fall off a cliff. At one point a max extension looked possible, but now the number being floated around is the veteran's minimum, a chance to prove himself and get a better contract the next year. Other former lottery picks have taken that route before, like Malik Monk, Al-Farouq Aminu and Ed Davis.",
      "Monk, Aminu, and Davis all took the minimum in their early-to-mid twenties, after a few years in the league. But they were falling from rookie-scale money, between $3 million and $5 million a year. Kuminga would be falling from a salary of more than $24 million, and he's only 23. Which raises a wild question: has a former top-10 pick ever fallen to the veteran's minimum this fast and this young? If so, who was it, and how young were they?",
    ],
  },
  methodology: {
    heading: "How I found this",
    paragraphs: [
      "The veteran's minimum isn't a fixed number for everyone. The minimum salary goes up with how many years a player has been in the league (a.k.a. his \"years of service\"). For the 2025-26 season, it ran from about $2 million for a player with one year to about $3.6 million for a player with 10+ years. The bar chart below has the number for each year of service. To compare players against it, I took the salary of every NBA player for every season since 1991 and wrote Python scripts to check each one against the minimum that player was eligible for that year.",
      "After all the collecting and filtering, I had a list of every real veteran-minimum signing since 1991. Each signing records the player's age when he signed, how much his salary dropped from the previous season, and where he was drafted. The chart below shows them all, with three separate tabs: every signing, real pay cuts only, and former top-10 picks.",
    ],
  },
  snags: {
    intro: "Matching salaries to the minimum wasn't as simple as it sounds. There were three main problems:",
    items: [
      {
        label: "Years of service:",
        text: "The salary data doesn't always go back to a player's first season, so I had to find each player's real NBA debut to know which minimum he was eligible for.",
      },
      {
        label: "Mid-season signings:",
        text: "A player who signs in January only gets paid for the games that are left, so his salary looks smaller than the minimum. I counted those, but left out players on short emergency contracts, like two-day deals.",
      },
      {
        label: "Repeat seasons:",
        text: "The second year of the same minimum deal isn't a new signing, so I only counted it if the player changed teams or sat out a year in between. But changing teams isn't always a new deal either. When a young player on a minimum contract gets traded or claimed off waivers, his contract comes with him. So if a player in his first two years was paid exactly the minimum the season before too, I treated the move as the same contract. Khris Middleton is an example: Detroit traded him to Milwaukee in 2013, and he was still on the deal he signed as the 39th pick.",
      },
    ],
  },
  chart: {
    heading: "Under 27, and it happened fast",
  },
  whoDoesntCount: {
    heading: "Why the younger names on the chart don't count",
    paragraphs: [
      "If you switch the chart to the \"Real pay cuts only\" tab, you will see 11 players younger than Dragan Bender, who is the youngest of the top-10-pick group, at 21.9. At first glance, that seems to answer the \"youngest ever\" question. But none of them are really in the same situation as Kuminga.",
      "All of them signed for only part of the full-season minimum, some for as little as 22% of it. That's what a mid-season pickup looks like: one team cuts a player, and another signs him partway through the season, so he only gets paid for the games that are left. They were all just 1-3 years into their careers, so the salary they dropped from was their rookie contract, and they never went through second-contract free agency. A couple also had unusual situations, like Josh Primo's off-court issues and Tyrell Terry stepping away for personal reasons.",
      "The real comparisons for Kuminga are the top-10 picks who signed the minimum in the offseason, meaning they went into free agency and the market decided what they were worth. Bender, the #4 pick in 2016, is the youngest. Phoenix let him go after three years, and he signed a minimum deal with Milwaukee at 21.9. Marquese Chriss (#8 in 2016) is next at 22.3, on a non-guaranteed minimum deal with Golden State. Eddie Griffin (#7 in 2001) also signed at 22.3, a one-year minimum deal with Minnesota after Houston waived him over off-court problems. Then come Nikoloz Tskitishvili (#5 in 2002) at 22.5 and Anthony Bennett (#1 in 2013) at 22.6. Even outside the top 10, nobody signed a full-season minimum deal younger than Bender. The closest was Daniel Orton, the 29th pick, at 22.1. What makes Kuminga stand out is the combination of being drafted high and the open market pricing him at the minimum.",
    ],
  },
  youngFa: {
    heading: "How much do young free agents actually get paid?",
    intro:
      "Ten years of new contracts signed by 21-to-25-year-olds, plotted against what Kuminga was offered, what he actually signed for, and what he's now rumored to settle for.",
  },
  proveIt: {
    heading: "Does the vet minimum stick?",
  },
  buyoutCaveat: {
    heading: "A known blind spot: buyouts",
    paragraphs: [
      "One thing my data can't see clearly is a buyout. When a team buys out a player, he gets released, but he also gets a settlement from his old team on top of whatever his new team pays him. My salary data only shows what the new team pays, so the buyout money is missing. Chris Webber is a good example. In January 2007, Philadelphia bought him out in the middle of the season and he signed with Detroit for the minimum. His real income that year was way higher than the $661,024 Detroit paid him, but the data only sees the Detroit number, so his drop looks bigger than it really was.",
      "Joe Johnson is the more famous case. In 2016, Brooklyn bought him out of the last part of his max contract and he signed with Miami for the rest of the season at $414,481, which looks like a 98% pay cut. He played well in Miami and got an $11 million contract from Utah the next season. The comeback is real, but the drop is exaggerated because the data doesn't include the money Brooklyn still paid him.",
      "I tried to fix this by adding the buyout money back in, but I couldn't get the numbers. The one site that tracks buyout amounts blocks scraping, and Basketball-Reference only says a buyout happened, not how much it was worth. So for any player who was bought out, take the drop on the chart with a grain of salt, especially in the \"Bounced back\" tab.",
    ],
  },
  prorationCaveat: {
    heading: "Another blind spot: short stints and waivers",
    paragraphs: [
      "A similar problem happens without a buyout. A player signs a normal contract, plays a few games, gets hurt or falls out of the rotation, and gets waived. The data only shows what he was paid for those few games, not what the full contract was worth, so on paper it can look like a minimum deal even though it wasn't.",
      "Danny Green is the example that showed me this. In 2023-24 he signed with Philadelphia, played 2 games, and got waived, leaving about $202,000 on the books. My filter already throws out anything under 22% of the full-season minimum, so that number never showed up as a vet-min signing. But it was causing a different problem. The season before, Green had signed a real minimum deal, and my pipeline was reading the $202,000 as his next contract, so it looked like he was still hanging on at the minimum. Really, his career was just ending. Now the \"prove it\" chart puts cases like his in the \"Flamed out\" tab, along with players who have no salary at all the next season.",
    ],
  },
  deadMoneyFix: {
    heading: "One I fixed: old money showing up as a new contract",
    paragraphs: [
      "DeAndre Jordan's case was a third version of this problem, and this one I was able to fix. In 2021-22, Brooklyn traded him to Detroit as a salary dump, and Detroit released him right away. The roughly $7.9 million on Detroit's books was money left over from his old contract, not a new deal. He then signed for the minimum with the Lakers, and later with Denver.",
      "The bug was that the same $7.9 million showed up on Detroit's books again the next season, because the payments were stretched out over multiple years. It was only 0.6% different from the first year, so it was clearly the same money. But my pipeline was reading it as his next contract, which made it look like he jumped from the minimum to $7.9 million. In reality, he had signed another minimum deal with Denver.",
      "To fix it, I now remove a salary if it's within 15% of one the same team already paid him in an earlier season, but only if he was also on a different team that earlier season, and only if the number is clearly above the minimum. That last rule mattered. My first version didn't have it, and it wrongly flagged Jordan's normal re-signing with Denver in 2023-24, which was just a 10% raise on the minimum. With both rules in place, Jordan comes out right: another minimum deal with Denver, not a fake bounce-back.",
      "The same check caught one more issue. My salary data ends with the 2023-24 season, so players who signed a minimum deal that season have no next season to look at. 51 of them were getting put in \"Flamed out\" by default. Now they're left out of that chart, since I don't know what happened to them yet.",
    ],
  },
  missingSeasonsFix: {
    heading: "The one that changed my answer: missing seasons",
    paragraphs: [
      "The first version of this article said Nikoloz Tskitishvili was the youngest. Later, when I double-checked my answer against other sources, one pointed to Dragan Bender instead. He was the #4 pick in 2016, Phoenix let him go after three years, and he signed a minimum deal with Milwaukee in the summer of 2019 at 21. That's younger than Tskitishvili, so why wasn't he on my chart?",
      "The problem wasn't my filters, it was my salary data. The file I started with didn't have Bender's Milwaukee season at all, probably because the Bucks waived him in February. All it had was the roughly $190,000 Golden State paid him on 10-day contracts after that, which is under my 22% floor, so he got thrown out.",
      "To fix it, I scraped the salary table from the Basketball-Reference page of every player since 1991. Those pages list every team that paid a player in a season, including teams that waived him. Then I added back every team-season my original file was missing. There were 1,422 of them, about 9% of the original file, mostly players who got waived, stretched, or hurt. That's how Bender, Marquese Chriss and Eddie Griffin all ended up ahead of Tskitishvili.",
    ],
  },
  lookup: {
    heading: "Look up any player",
    intro:
      "Every real veteran-minimum signing in this dataset, from 1991 to now. Search a name to see that player's drop, not just the ones featured above.",
  },
  closing: {
    heading: "Where it goes from here",
    paragraphs: [
      "So, back to the question: has a former top-10 pick ever fallen to the veteran's minimum this young? Yes. Since 1991, it's happened 45 times to former top-10 picks under 27. Dragan Bender (21.9) is the youngest, followed by Marquese Chriss and Eddie Griffin (both 22.3), Tskitishvili (22.5) and Bennett (22.6, and again at 23.6).",
      "But Kuminga wouldn't be the youngest. He's 23 now, and if his free agency drags into the 2026-27 season, he'd be closer to 24 by the time a minimum deal actually started. That would put him in the younger third of the group, but not at the front.",
      "Where he would really stand out is the money. 40 of those 45 cases dropped from a salary under $10 million. A couple look bigger, like Enes Freedom falling from $20.6 million and Andrew Bynum from $16.9 million, but both were waived in the middle of a season, so the team that waived them was still paying them (the same blind spot as the buyouts above). Among top-10 picks who actually went through free agency, the biggest drop was Mo Bamba, from $10.3 million to $2.3 million at 25.4. Going beyond top-10 picks, only one player under 27 has ever gone through free agency and dropped to the minimum from $15 million or more: Malik Beasley, who went from $15.6 million to $2.7 million at 26.8. Kuminga would be almost 3 years younger and falling from more than $24 million. (These are raw dollars, not adjusted for inflation.)",
      "The minimum also isn't always the end. Of the 759 real vet-min pay cuts in my data, only 101, about one in eight, got a real contract the next season, like Malik Monk did. 316 kept getting minimum deals, and 342 were out of the league within a year. Taking the minimum is a public sign that the market doesn't value you right now, and most players never get that value back, but some do.",
      "Shaun Livingston is the best example. He was the #4 pick in 2004, and in 2007 he blew out his knee so badly that doctors talked about amputation. He spent years bouncing around the league on minimum deals, 10-day contracts and short stints, then signed with the Warriors in 2014 and won three titles as their backup point guard. As a Warriors fan, I'd take that ending for Kuminga.",
      "Whatever Kuminga ends up signing, I can add his number to the data and see exactly where he lands.",
    ],
  },
};
