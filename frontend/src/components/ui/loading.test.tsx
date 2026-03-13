import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Loading } from "./loading";

describe("Loading", () => {
  it("renders default message", () => {
    render(<Loading />);
    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("renders custom message", () => {
    render(<Loading message="Fetching data" />);
    expect(screen.getByText("Fetching data")).toBeInTheDocument();
  });
});
