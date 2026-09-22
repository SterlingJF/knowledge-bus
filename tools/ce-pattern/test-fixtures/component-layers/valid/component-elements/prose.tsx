import type { ReactNode } from "react";

import { Button } from "../component-core/button";

export function Prose({ children }: { children: ReactNode }) {
  return <Button className="prose">{children}</Button>;
}
