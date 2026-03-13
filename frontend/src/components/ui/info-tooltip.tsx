import * as Tooltip from "@radix-ui/react-tooltip";

export function InfoTooltip({ label, interpret }: { label: string; interpret?: string }) {
  return (
    <Tooltip.Provider delayDuration={200}>
      <Tooltip.Root>
        <Tooltip.Trigger asChild>
          <button
            type="button"
            className="ml-1 inline-flex h-4 w-4 items-center justify-center rounded-full text-[10px] text-text-muted border border-border hover:bg-primary/10 hover:text-primary"
            aria-label={`Info: ${label}`}
          >
            i
          </button>
        </Tooltip.Trigger>
        <Tooltip.Portal>
          <Tooltip.Content
            className="z-50 max-w-xs rounded-lg border border-border bg-surface p-3 text-sm shadow-md"
            sideOffset={5}
          >
            <p className="text-text">{label}</p>
            {interpret && <p className="mt-1 text-xs text-text-muted">{interpret}</p>}
            <Tooltip.Arrow className="fill-surface" />
          </Tooltip.Content>
        </Tooltip.Portal>
      </Tooltip.Root>
    </Tooltip.Provider>
  );
}
