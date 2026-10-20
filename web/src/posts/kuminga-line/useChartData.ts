import { useJson } from "../../lib/useJson";
import type { SigningsData, ProveItData, YoungFaData } from "./types";

export function useChartData() {
  return useJson<SigningsData>("/data/kuminga-line/all_signings.json");
}

export function useProveItData() {
  return useJson<ProveItData>("/data/kuminga-line/prove_it.json");
}

export function useYoungFaData() {
  return useJson<YoungFaData>("/data/kuminga-line/young_fa.json");
}
