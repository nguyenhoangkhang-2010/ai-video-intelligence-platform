import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { GearTrain } from "@/components/dial/GearTrain";

const STAGES = ["Ingest", "Transcribe", "Understand", "Index", "Ready"];

describe("GearTrain", () => {
  it("labels stages as HTML in one equal-width column per gear", () => {
    render(<GearTrain stages={STAGES} activeIndex={1} />);

    const steps = screen.getAllByRole("listitem");
    expect(steps.map((step) => step.textContent)).toEqual([
      "01Ingest",
      "02Transcribe",
      "03Understand",
      "04Index",
      "05Ready",
    ]);
    expect(steps[0]!.parentElement?.style.gridTemplateColumns).toBe("repeat(5, minmax(0, 1fr))");
    // No SVG <text>: labels must not shrink with the drawing.
    expect(document.querySelector("svg text")).toBeNull();
  });

  it("marks the running stage and the finished ones", () => {
    render(<GearTrain stages={STAGES} activeIndex={2} />);

    const steps = screen.getAllByRole("listitem");
    expect(steps[2]).toHaveAttribute("aria-current", "step");
    expect(steps[0]!.querySelector("svg")).not.toBeNull(); // check mark
    expect(steps[3]!.querySelector("svg")).toBeNull();
  });

  it("places gears one pitch apart on a single axis and stops turning when complete", () => {
    const { container, rerender } = render(<GearTrain stages={STAGES} activeIndex={1} />);

    const centres = [...container.querySelectorAll("svg > g")].map((gear) => {
      const match = gear.getAttribute("transform")?.match(/translate\(([\d.]+) ([\d.]+)\)/);
      return { x: Number(match?.[1]), y: Number(match?.[2]) };
    });
    const gaps = centres.slice(1).map((centre, index) => centre.x - centres[index]!.x);
    expect(new Set(gaps).size).toBe(1);
    expect(new Set(centres.map((centre) => centre.y)).size).toBe(1);
    expect(container.querySelectorAll(".animate-spin")).toHaveLength(5);

    rerender(<GearTrain stages={STAGES} activeIndex={4} complete />);
    expect(container.querySelectorAll(".animate-spin")).toHaveLength(0);
  });
});
