import { Button } from "../component-core/button";
import { Separator } from "../component-core/separator";

export function Toc({ headings }: { headings: string[] }) {
  return (
    <nav>
      {headings.map((heading) => (
        <Button key={heading}>{heading}</Button>
      ))}
      <Separator />
    </nav>
  );
}
