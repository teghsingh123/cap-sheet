import { useJson } from "../../lib/useJson";
import type { SigningsData, ProveItData, YoungFaData } from "./types";

export function useChartData() {
  return useJson<SigningsData>("/data/all_signings.json");
}

export function useProveItData() {
  return useJson<ProveItData>("/data/prove_it.json");
}

export function useYoungFaData() {
  return useJson<YoungFaData>("/data/young_fa.json");
}
