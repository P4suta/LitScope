export interface MetricExplanation {
  short: string;
  interpret?: string;
}

export interface SectionExplanation {
  description: string;
}

export const SECTION_GLOSSARY: Record<string, SectionExplanation> = {
  vocabulary: {
    description:
      "Measures of vocabulary richness and diversity. Higher values generally indicate more varied word usage.",
  },
  readability: {
    description:
      "Estimated readability scores reflecting sentence structure and vocabulary complexity.",
  },
  pos_distribution: {
    description:
      "Part-of-speech distribution reveals stylistic tendencies — descriptive, action-driven, or otherwise.",
  },
  genre_distribution: { description: "Distribution of genres across the corpus." },
  timeline: {
    description:
      "Vocabulary diversity over publication years, showing how literary style evolved across eras.",
  },
  topics: {
    description:
      "Characteristic keywords extracted via TF-IDF. Font size is proportional to the score.",
  },
  compare: {
    description: "Metrics normalized to 0–1 for relative comparison across works via radar chart.",
  },
};

export const METRIC_GLOSSARY: Record<string, MetricExplanation> = {
  ttr: {
    short: "Type-Token Ratio — unique words divided by total words.",
    interpret: "0–1. Higher = more diverse vocabulary. Tends to decrease with text length.",
  },
  mtld: {
    short: "Measure of Textual Lexical Diversity — length-independent vocabulary diversity.",
    interpret: "Higher = more diverse. Typical literary range: 50–150.",
  },
  hapax_ratio: {
    short: "Proportion of words that appear only once.",
    interpret: "Higher = less repetition, richer vocabulary. Typical: 0.40–0.60.",
  },
  unique_lemmas: {
    short: "Number of unique lemmas (base forms) in the text.",
  },
  ari: {
    short: "Automated Readability Index — based on character and word counts per sentence.",
    interpret: "Roughly maps to US grade level. ARI 8 ≈ 8th grade. Literary works: 7–12.",
  },
  flesch_kincaid: {
    short: "Flesch-Kincaid Grade Level — based on syllables and sentence length.",
  },
  coleman_liau: {
    short: "Coleman-Liau Index — based on character and sentence counts.",
  },
  mean_sentence_length: {
    short: "Average number of words per sentence.",
    interpret: "Under 15 = concise style. Over 25 = complex or classical style.",
  },
  median_sentence_length: {
    short: "Median sentence length in words — less sensitive to outliers than the mean.",
  },
  stdev_sentence_length: {
    short: "Standard deviation of sentence length — measures variability.",
  },
  min_sentence_length: {
    short: "Shortest sentence in the text (word count).",
  },
  max_sentence_length: {
    short: "Longest sentence in the text (word count).",
  },
  passive_ratio: {
    short: "Proportion of sentences in passive voice.",
    interpret: "0–1. Academic/formal text: 0.15–0.30. Fiction: 0.05–0.15.",
  },
  active_voice: {
    short: "Number of sentences in active voice.",
  },
  passive_voice: {
    short: "Number of sentences in passive voice.",
  },
  zipf_alpha: {
    short: "Power-law exponent of Zipf's law — slope of the word frequency distribution.",
    interpret: "Around −1.0 is typical Zipf. Deviation suggests unusual vocabulary distribution.",
  },
  zipf_r_squared: {
    short: "R² of the Zipf regression — goodness of fit.",
    interpret: "Closer to 1.0 = closer to ideal Zipf distribution. Most texts > 0.95.",
  },
};
