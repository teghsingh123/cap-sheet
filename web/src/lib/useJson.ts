import { useEffect, useState } from "react";
import { withBase } from "./base";

// Fetches a JSON file from public/ once per URL. Shared by every post that
// loads chart data built by the Python pipeline.
export function useJson<T>(url: string) {
  const [data, setData] = useState<T | null>(null);
  useEffect(() => {
    fetch(withBase(url))
      .then((res) => res.json())
      .then(setData);
  }, [url]);
  return data;
}
