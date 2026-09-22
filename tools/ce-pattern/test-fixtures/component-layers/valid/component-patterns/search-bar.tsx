import { Button } from "@fixture/components/component-core/button";
import { Separator } from "@fixture/components/component-core/separator";
import { NavLink } from "@fixture/components/component-elements/nav-link";

export function SearchBar() {
  return (
    <form>
      <NavLink href="/" />
      <Separator />
      <Button type="submit" />
    </form>
  );
}
