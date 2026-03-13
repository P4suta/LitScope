import { createFileRoute, Link } from "@tanstack/react-router";
import { POSDistributionChart } from "@/components/charts/pos-distribution-chart";
import { WordFrequencyChart } from "@/components/charts/word-frequency-chart";
import { ZipfPlot } from "@/components/charts/zipf-plot";
import { Section } from "@/components/ui/section";
import { Stat } from "@/components/ui/stat";
import { useReadability, useSyntax, useVocabulary } from "@/hooks/use-analysis";
import { useWork } from "@/hooks/use-works";

export const Route = createFileRoute("/works/$workId")({
  component: WorkDetail,
});

function WorkDetail() {
  const { workId } = Route.useParams();
  interface WorkData {
    title: string;
    author: string;
    genre: string;
    chap_count: number;
    sent_count?: number;
    word_count?: number;
    analyses_run?: string[];
  }
  const { data: work } = useWork(workId) as { data: WorkData | undefined };
  const { data: vocab } = useVocabulary(workId);
  const { data: read } = useReadability(workId);
  const { data: syntax } = useSyntax(workId);

  const fmt = (v: number | null | undefined, d = 2) => (v != null ? Number(v).toFixed(d) : "—");

  return (
    <div className="space-y-8">
      <div>
        <Link to="/works" className="text-sm text-text-muted hover:text-primary">
          ← Works
        </Link>
        <h1 className="mt-2 text-3xl font-bold">{work?.title ?? workId}</h1>
        {work && (
          <p className="mt-1 text-text-muted">
            {work.author} · {work.genre}
          </p>
        )}
      </div>

      {/* Overview stats */}
      {work && (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          <Stat label="Chapters" value={work.chap_count} />
          <Stat label="Sentences" value={work.sent_count?.toLocaleString()} />
          <Stat label="Words" value={work.word_count?.toLocaleString()} />
          <Stat label="Analyses" value={work.analyses_run?.length ?? 0} />
        </div>
      )}

      {/* Vocabulary */}
      {vocab && (
        <Section title="Vocabulary" sectionKey="vocabulary">
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <Stat
              label="Unique Lemmas"
              value={vocab.unique_lemmas.toLocaleString()}
              metricKey="unique_lemmas"
            />
            <Stat label="TTR" value={fmt(vocab.ttr, 4)} metricKey="ttr" />
            <Stat label="MTLD" value={fmt(vocab.mtld, 1)} metricKey="mtld" />
            <Stat label="Hapax Ratio" value={fmt(vocab.hapax_ratio, 4)} metricKey="hapax_ratio" />
          </div>
          <div className="mt-4">
            <h4 className="text-sm font-medium text-text-muted">Top Words</h4>
            <WordFrequencyChart words={vocab.top_words} />
          </div>
          <div className="mt-4">
            <h4 className="text-sm font-medium text-text-muted">Zipf Distribution</h4>
            <ZipfPlot
              words={vocab.top_words}
              alpha={vocab.zipf_alpha}
              rSquared={vocab.zipf_r_squared}
              intercept={vocab.zipf_intercept}
            />
          </div>
        </Section>
      )}

      {/* Readability */}
      {read && (
        <Section title="Readability" sectionKey="readability">
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <Stat label="ARI" value={fmt(read.ari, 1)} metricKey="ari" />
            <Stat
              label="Mean Sentence Length"
              value={fmt(read.mean_sentence_length, 1)}
              metricKey="mean_sentence_length"
            />
            <Stat
              label="Median Sentence Length"
              value={read.median_sentence_length}
              metricKey="median_sentence_length"
            />
            <Stat
              label="Std Dev"
              value={fmt(read.stdev_sentence_length, 1)}
              metricKey="stdev_sentence_length"
            />
          </div>
          <div className="mt-4 grid grid-cols-2 gap-4 md:grid-cols-2">
            <Stat
              label="Shortest Sentence"
              value={read.min_sentence_length}
              metricKey="min_sentence_length"
            />
            <Stat
              label="Longest Sentence"
              value={read.max_sentence_length}
              metricKey="max_sentence_length"
            />
          </div>
        </Section>
      )}

      {/* POS Distribution */}
      {syntax && (
        <Section title="Part-of-Speech Distribution" sectionKey="pos_distribution">
          <POSDistributionChart distribution={syntax.pos_distribution} />
          <div className="mt-4 grid grid-cols-2 gap-4 md:grid-cols-3">
            <Stat
              label="Active Voice"
              value={syntax.active_voice_count?.toLocaleString()}
              metricKey="active_voice"
            />
            <Stat
              label="Passive Voice"
              value={syntax.passive_voice_count?.toLocaleString()}
              metricKey="passive_voice"
            />
            <Stat
              label="Passive Ratio"
              value={fmt(syntax.passive_ratio, 3)}
              metricKey="passive_ratio"
            />
          </div>
        </Section>
      )}
    </div>
  );
}
