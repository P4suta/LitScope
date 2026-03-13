import { Link } from "@tanstack/react-router";
import { useUiStore } from "@/stores/ui-store";

const navItems = [
  { to: "/", label: "Dashboard" },
  { to: "/works", label: "Works" },
  { to: "/compare", label: "Compare" },
  { to: "/authors", label: "Authors" },
  { to: "/timeline", label: "Timeline" },
  { to: "/topics", label: "Topics" },
] as const;

export function Sidebar() {
  const sidebarOpen = useUiStore((s) => s.sidebarOpen);

  if (!sidebarOpen) return null;

  return (
    <aside className="fixed inset-y-0 left-0 z-30 flex w-64 flex-col border-r border-border bg-surface">
      <div className="flex h-14 items-center px-6">
        <Link to="/" className="text-xl font-bold text-primary">
          LitScope
        </Link>
      </div>
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navItems.map(({ to, label }) => (
          <Link
            key={to}
            to={to}
            className="block rounded-lg px-3 py-2 text-sm font-medium transition-colors text-text-muted hover:bg-surface-dim"
            activeProps={{
              className:
                "block rounded-lg px-3 py-2 text-sm font-medium transition-colors bg-primary/10 text-primary",
            }}
            activeOptions={{ exact: to === "/" }}
          >
            {label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
