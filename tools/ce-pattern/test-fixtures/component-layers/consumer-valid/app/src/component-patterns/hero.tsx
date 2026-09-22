import { Card, NavLink } from "@fixture/components";
import { Separator } from "@fixture/components/component-core/separator";
import { Button } from "../component-core";

export function Hero() {
  return (
    <header>
      <NavLink href="/" />
      <Separator />
      <Card />
      <Button />
    </header>
  );
}
