export function Toc({ headings }: { headings: string[] }) {
  return (
    <nav>
      {headings.map((heading) => (
        <a key={heading} href={`#${heading}`}>
          {heading}
        </a>
      ))}
    </nav>
  );
}
