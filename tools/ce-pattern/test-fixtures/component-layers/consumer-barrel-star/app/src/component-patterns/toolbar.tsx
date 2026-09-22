import { Button, Separator, cn } from "@fixture/components";

export function Toolbar() {
  return (
    <div className={cn("toolbar")}>
      <Button />
      <Separator />
    </div>
  );
}
