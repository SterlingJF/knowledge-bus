import { Button } from "../component-core/button";
import { Separator } from "../component-core/separator";

export function SplitStart() {
  return <Button />;
}

export function SplitRule() {
  return <Separator />;
}

export const split = [SplitStart, SplitRule];
