import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ErrorBoundary } from "./error-boundary";

function ThrowingChild({ message }: { message: string }): React.ReactNode {
  throw new Error(message);
}

describe("ErrorBoundary", () => {
  beforeEach(() => {
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  it("renders children when no error", () => {
    render(
      <ErrorBoundary>
        <p>OK</p>
      </ErrorBoundary>,
    );
    expect(screen.getByText("OK")).toBeInTheDocument();
  });

  it("renders default error UI on throw", () => {
    render(
      <ErrorBoundary>
        <ThrowingChild message="boom" />
      </ErrorBoundary>,
    );
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
    expect(screen.getByText("boom")).toBeInTheDocument();
  });

  it("renders custom fallback on throw", () => {
    render(
      <ErrorBoundary fallback={<p>Custom error</p>}>
        <ThrowingChild message="boom" />
      </ErrorBoundary>,
    );
    expect(screen.getByText("Custom error")).toBeInTheDocument();
  });

  it("calls componentDidCatch with error info", () => {
    const spy = vi.spyOn(ErrorBoundary.prototype, "componentDidCatch");

    render(
      <ErrorBoundary>
        <ThrowingChild message="catch me" />
      </ErrorBoundary>,
    );

    expect(spy).toHaveBeenCalledOnce();
    expect(spy.mock.calls[0]![0].message).toBe("catch me");
    spy.mockRestore();
  });
});
