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

# Run analysis pipeline (Phase 2) / 分析パイプライン実行 / 运行分析管道
uv run litscope analyze

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

### Data Model / データモデル / 数据模型

| Table / テーブル | Description / 説明 / 描述 |
|---|---|
| `works` | Literary works with metadata / 作品マスタ / 作品主表 |
| `chapters` | Chapters within works / チャプター / 章节 |
| `sentences` | Sentences with text and counts / 文 / 句子 |
| `tokens` | Tokens with lemma, POS, stop word flag / トークン / 词元 |

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

## Tech Stack / 技術スタック / 技术栈

| Layer | Technology |
|---|---|
| Backend | Python 3.12+, FastAPI, DuckDB, spaCy, BERTopic |
| Frontend | React 19, TypeScript 5+, D3.js, Tailwind CSS, Vite |
| Package Management | uv (Python), npm (Frontend) |
| Deployment | Docker Compose |

## License / ライセンス / 许可证

MIT
