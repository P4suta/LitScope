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

## Features / 機能 / 功能

- **EPUB Ingestion** — Parse Standard Ebooks EPUB files with differential ingestion (skip unchanged files)
- **Text Normalization** — HTML stripping, NFKC Unicode normalization, spaCy tokenization
- **20 Analysis Modules** — Vocabulary statistics, syntactic analysis, topic modeling, sentiment analysis, stylometry, and more
- **Interactive Dashboard** — React + D3.js visualization of analysis results
- **CLI** — Command-line interface for ingestion, analysis, and serving

## Quick Start / クイックスタート / 快速开始

### Prerequisites / 前提条件 / 前置条件

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- spaCy English model: `uv pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl`

### Installation / インストール / 安装

```bash
git clone https://github.com/your-org/litscope.git
cd litscope
uv sync
```

### Usage / 使い方 / 使用方法

```bash
# Ingest EPUB files / EPUB ファイルの取り込み / 导入 EPUB 文件
uv run litscope ingest <epub-directory>

# Check database status / データベース状態の確認 / 查看数据库状态
uv run litscope status

# Run all analyzers / 全分析モジュール実行 / 运行所有分析模块
uv run litscope analyze

# Run specific analyzers / 特定モジュール実行 / 运行特定模块
uv run litscope analyze --analyzers vocabulary_frequency,lexical_richness

# Analyze a single work / 特定作品の分析 / 分析单个作品
uv run litscope analyze --work <work-id> --analyzers sentence_length

# Start API server (Phase 3) / API サーバー起動 / 启动 API 服务器
uv run litscope serve
```

## Architecture / アーキテクチャ / 架构

LitScope follows a 5-layer architecture (dependencies flow top-to-bottom only):

```
┌─────────────────────────────────────┐
│  Presentation (React + D3.js)       │
├─────────────────────────────────────┤
│  API (FastAPI + Pydantic)           │
├─────────────────────────────────────┤
│  Analysis (20 analyzer modules)     │
├─────────────────────────────────────┤
│  Storage (DuckDB)                   │
├─────────────────────────────────────┤
│  Ingestion (EPUB → structured data) │
└─────────────────────────────────────┘
```

### Ingestion Pipeline / インジェスションパイプライン / 导入管道

```
EPUB File → EpubParser → MetadataExtractor → TextNormalizer → Database
                │               │                   │
           SHA-256 hash    Dublin Core       spaCy tokenization
           HTML chapters   title/author      sentences/tokens
```

### Analysis Pipeline / 分析パイプライン / 分析管道

LitScope uses a plugin-based analyzer framework with automatic dependency resolution.

LitScope はプラグインベースの分析フレームワークを使用し、依存関係を自動解決します。

LitScope 使用基于插件的分析框架，自动解析依赖关系。

**Classical Analyzers / 古典分析 / 经典分析:**
| Analyzer | Description / 説明 / 描述 |
|---|---|
| `vocabulary_frequency` | Lemma frequencies and TF / 語彙頻度と TF / 词频与 TF |
| `lexical_richness` | TTR, hapax ratio, Yule's K, MTLD / 語彙豊富さ指標 / 词汇丰富度 |
| `sentence_length` | Mean, median, stdev of sentence lengths / 文長統計 / 句长统计 |
| `readability` | Flesch-Kincaid, Coleman-Liau, ARI / 可読性指標 / 可读性指标 |
| `zipf_fitness` | Zipf's law fit (alpha, R²) / ジップの法則適合度 / 齐普夫定律拟合 |

**Syntactic Analyzers / 構文分析 / 句法分析:**
| Analyzer | Description / 説明 / 描述 |
|---|---|
| `pos_distribution` | POS tag frequencies and ratios / 品詞分布 / 词性分布 |
| `pos_transition` | POS bigram transition matrix / 品詞遷移行列 / 词性转移矩阵 |
| `sentence_openings` | First 1-3 POS patterns / 文頭パターン / 句首模式 |
| `voice_ratio` | Active/passive voice ratio / 能動態・受動態比率 / 主被动语态比率 |

### Data Model / データモデル / 数据模型

| Table / テーブル | Description / 説明 / 描述 |
|---|---|
| `works` | Literary works with metadata / 作品マスタ / 作品主表 |
| `chapters` | Chapters within works / チャプター / 章节 |
| `sentences` | Sentences with text and counts / 文 / 句子 |
| `tokens` | Tokens with lemma, POS, stop word flag / トークン / 词元 |
| `analysis_results` | Analyzer outputs with metrics / 分析結果 / 分析结果 |
| `word_frequencies` | Per-work lemma frequencies / 語彙頻度 / 词频 |
| `pos_distributions` | POS tag distributions / 品詞分布 / 词性分布 |
| `pos_transitions` | POS bigram transitions / 品詞遷移 / 词性转移 |
| `sentence_opening_patterns` | Sentence opening POS patterns / 文頭パターン / 句首模式 |

## Development / 開発 / 开发

```bash
# Run tests / テスト実行 / 运行测试
uv run pytest

# Run tests with coverage / カバレッジ付きテスト / 运行带覆盖率的测试
uv run pytest --cov=litscope --cov-report=term-missing

# Lint / リント / 代码检查
uv run ruff check src/ tests/

# Format / フォーマット / 代码格式化
uv run ruff format src/ tests/

# Type check / 型チェック / 类型检查
uv run mypy src/
```

## Configuration / 設定 / 配置

All settings use environment variables with `LITSCOPE_` prefix. Defaults are provided (zero-config policy).

| Variable | Default | Description |
|---|---|---|
| `LITSCOPE_DB_PATH` | `litscope.duckdb` | DuckDB database file path |
| `LITSCOPE_EPUB_DIR` | `data/epubs` | Default EPUB directory |
| `LITSCOPE_LOG_LEVEL` | `INFO` | Logging level |
| `LITSCOPE_SPACY_MODEL` | `en_core_web_sm` | spaCy model name |
| `LITSCOPE_SENTIMENT_SEGMENTS` | `100` | Number of sentiment arc segments |
| `LITSCOPE_DIALOGUE_SEGMENTS` | `100` | Number of dialogue density segments |
| `LITSCOPE_TIME_SLICE_YEARS` | `25` | Time slice width for temporal analysis |

## Tech Stack / 技術スタック / 技术栈

| Layer | Technology |
|---|---|
| Backend | Python 3.12+, FastAPI, DuckDB, spaCy, BERTopic |
| Frontend | React 19, TypeScript 5+, D3.js, Tailwind CSS, Vite |
| Package Management | uv (Python), npm (Frontend) |
| Deployment | Docker Compose |

## License / ライセンス / 许可证

MIT
