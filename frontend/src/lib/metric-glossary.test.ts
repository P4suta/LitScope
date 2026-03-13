import { describe, expect, it } from "vitest";
import { METRIC_GLOSSARY, SECTION_GLOSSARY } from "./metric-glossary";

describe("SECTION_GLOSSARY", () => {
  const expectedSections = [
    "vocabulary",
    "readability",
    "pos_distribution",
    "genre_distribution",
    "timeline",
    "topics",
    "compare",
  ];

  it.each(expectedSections)("contains section key '%s'", (key) => {
    const section = SECTION_GLOSSARY[key];
    expect(section).toBeDefined();
    expect(section!.description.length).toBeGreaterThan(0);
  });
});

describe("METRIC_GLOSSARY", () => {
  const expectedMetrics = [
    "ttr",
    "mtld",
    "hapax_ratio",
    "unique_lemmas",
    "ari",
    "flesch_kincaid",
    "coleman_liau",
    "mean_sentence_length",
    "median_sentence_length",
    "stdev_sentence_length",
    "min_sentence_length",
    "max_sentence_length",
    "passive_ratio",
    "active_voice",
    "passive_voice",
    "zipf_alpha",
    "zipf_r_squared",
  ];

  it.each(expectedMetrics)("contains metric key '%s'", (key) => {
    const metric = METRIC_GLOSSARY[key];
    expect(metric).toBeDefined();
    expect(metric!.short.length).toBeGreaterThan(0);
  });

  it("every entry has a non-empty short description", () => {
    for (const [key, val] of Object.entries(METRIC_GLOSSARY)) {
      expect(val.short, `${key} should have a short description`).toBeTruthy();
    }
  });
});
