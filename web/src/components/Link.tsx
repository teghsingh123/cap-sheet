import type { MouseEvent, ReactNode } from "react";
import { navigate } from "../lib/router";
import { withBase } from "../lib/base";

export function Link({
  to,
  className,
  children,
}: {
  to: string;
  className?: string;
  children: ReactNode;
}) {
  const onClick = (e: MouseEvent<HTMLAnchorElement>) => {
    // Let ctrl/cmd-click, middle-click, etc. open a new tab as usual.
    if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    e.preventDefault();
    navigate(to);
  };
  return (
    <a href={withBase(to)} className={className} onClick={onClick}>
      {children}
    </a>
  );
}
