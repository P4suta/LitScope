import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { InfoTooltip } from "./info-tooltip";

describe("InfoTooltip", () => {
  it("renders trigger button with aria-label", () => {
    render(<InfoTooltip label="Test definition" />);

    const button = screen.getByRole("button", { name: "Info: Test definition" });
    expect(button).toBeInTheDocument();
    expect(button).toHaveTextContent("i");
  });

  it("includes aria-label with the label text", () => {
    render(<InfoTooltip label="Some metric" interpret="Higher is better" />);

    expect(screen.getByLabelText("Info: Some metric")).toBeInTheDocument();
  });

  it("renders without interpret prop", () => {
    render(<InfoTooltip label="Only short text" />);

    expect(screen.getByRole("button")).toBeInTheDocument();
  });
});
