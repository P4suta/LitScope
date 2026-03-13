import { SECTION_GLOSSARY } from "@/lib/metric-glossary";

export function Section({
  title,
  sectionKey,
  children,
}: {
  title: string;
  sectionKey?: string;
  children: React.ReactNode;
}) {
  const explanation = sectionKey ? SECTION_GLOSSARY[sectionKey] : undefined;

  return (
    <section className="rounded-xl border border-border bg-surface p-6 shadow-sm">
      <h3 className="mb-4 text-xl font-semibold">{title}</h3>
      {explanation && <p className="mb-4 text-sm text-text-muted">{explanation.description}</p>}
      {children}
    </section>
  );
}
