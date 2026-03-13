# LitScope

**Literary text analysis platform for computational literary studies.**

LitScope analyzes Standard Ebooks EPUB corpora using 20 analysis modules — from classical text statistics to NLP-based syntactic analysis and machine learning-driven topic modeling — and presents results via an interactive dashboard.

---

**文学テキスト総合分析プラットフォーム**

LitScope は Standard Ebooks の EPUB コーパスを対象に、古典的テキスト統計から NLP ベースの構文解析、機械学習によるトピックモデリングまで 20 種の分析モジュールで解析し、インタラクティブなダッシュボードで結果を提示します。

---

**文学文本综合分析平台**

LitScope 以 Standard Ebooks 的 EPUB 语料库为对象，集成了从经典文本统计到基于 NLP 的句法分析、机器学习驱动的主题建模等 20 个分析模块，并通过交互式仪表板展示分析结果。

---

## Quick Start

```bash
uv sync
uv run litscope ingest <epub-directory>
uv run litscope analyze
uv run litscope serve
```

## License

MIT
