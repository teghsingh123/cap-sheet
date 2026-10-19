export interface CliffRecord {
  player: string;
  brefId: string;
  year: number;
  age: number;
  yearsOfService: number;
  prevSalary: number | null;
  salary: number;
  dropPct: number | null;
  ratioOfMin: number;
  team: string;
  draftPick: number | null;
  isKumingaComp: boolean;
}

export interface SigningsData {
  signings: CliffRecord[];
}

export type ProveItOutcome = "bounced_back" | "stuck" | "flamed_out";

export interface ProveItRecord {
  player: string;
  brefId: string;
  year: number;
  age: number;
  vetMinSalary: number;
  nextYearSalary: number | null;
  multiple: number | null;
  outcome: ProveItOutcome;
  draftPick: number | null;
}

export interface ProveItData {
  signings: ProveItRecord[];
}

export interface YoungFaRecord {
  player: string;
  brefId: string;
  year: number;
  age: number;
  salary: number;
  team: string;
  draftPick: number | null;
}

export interface YoungFaData {
  signings: YoungFaRecord[];
}
