import { useUiStore } from "@/stores/ui-store";

export function Header() {
  const toggleSidebar = useUiStore((s) => s.toggleSidebar);

  return (
    <header className="flex h-14 items-center border-b border-border bg-surface px-6">
      <button
        type="button"
        onClick={toggleSidebar}
        className="rounded-lg p-2 text-text-muted transition-colors hover:bg-surface-dim"
        aria-label="Toggle sidebar"
      >
        <svg
          className="h-5 w-5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
          role="img"
          aria-label="Menu"
        >
          <title>Menu</title>
          <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>
    </header>
  );
}
