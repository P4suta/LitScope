# Contributing to LitScope

Thank you for your interest in contributing to LitScope!

LitScope へのコントリビュートに興味を持っていただきありがとうございます！

感谢您对 LitScope 项目的关注！

## Development Setup / 開発環境構築 / 开发环境搭建

### Local Development / ローカル開発 / 本地开发

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/litscope.git
   cd litscope
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Run tests to verify setup:
   ```bash
   uv run pytest
   ```

### Docker Development / Docker 開発 / Docker 开发

You can also develop using Docker:

Docker を使った開発も可能です：

也可以使用 Docker 进行开发：

```bash
# Build the image / イメージのビルド / 构建镜像
docker build -t litscope:dev .

# Run with local data directory / ローカルデータで実行 / 使用本地数据运行
docker compose up
```

## Code Quality / コード品質 / 代码质量

We maintain strict code quality standards:

厳格なコード品質基準を維持しています：

我们维护严格的代码质量标准：

- **100% test coverage** — All code must be covered by tests / 全コードをテストでカバー / 所有代码必须被测试覆盖
- **Type checking** — mypy strict mode / mypy 厳格モード / mypy 严格模式
- **Linting** — Ruff / リント
- **Formatting** — Ruff / フォーマット / 代码格式化

Run all checks before submitting a PR / PR 提出前に全チェックを実行 / 提交 PR 前运行所有检查:

```bash
uv run pytest --cov=litscope --cov-branch --cov-report=term-missing && uv run ruff check src/ tests/ && uv run mypy src/
```

## Testing / テスト / 测试

### Unit Tests / ユニットテスト / 单元测试

```bash
uv run pytest tests/unit/
```

### Integration Tests / 統合テスト / 集成测试

Integration tests run the full pipeline (ingest → analyze → API query) and require spaCy models:

統合テストはフルパイプライン（取り込み → 分析 → API クエリ）を実行し、spaCy モデルが必要です：

集成测试运行完整管道（导入 → 分析 → API 查询），需要 spaCy 模型：

```bash
uv run pytest tests/integration/
```

### All Tests with Coverage / カバレッジ付き全テスト / 带覆盖率的全部测试

```bash
uv run pytest --cov=litscope --cov-branch --cov-report=term-missing
```

## CI Pipeline / CI パイプライン / CI 管道

GitHub Actions runs automatically on push and PRs:

GitHub Actions がプッシュと PR で自動実行されます：

GitHub Actions 在推送和 PR 时自动运行：

1. **Quality job** — Lint → Format check → Type check → Unit tests (with coverage) → Integration tests
2. **Docker job** — Build Docker image (runs after quality passes)

See `.github/workflows/ci.yml` for details.

## Git Conventions / Git 規約 / Git 规范

### Commit Messages / コミットメッセージ / 提交信息

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>
```

- **type**: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `ci`, `style`
- **scope**: `ingestion`, `analysis`, `storage`, `api`, `frontend`, `config`
- One logical change per commit — don't mix features, fixes, and refactors
- 1コミット = 1論理的変更。機能追加・修正・リファクタを混ぜない
- 每次提交 = 一个逻辑变更。不要混合功能、修复和重构

### Branches / ブランチ / 分支

- `main` — Stable. No direct commits, PR merges only. / 安定版。直接コミット禁止 / 稳定版，仅通过 PR 合并
- `develop` — Development integration branch. / 開発統合ブランチ / 开发集成分支
- Feature branches: `feat/<scope>/<short-description>`
- Fix branches: `fix/<scope>/<short-description>`

## Development Philosophy / 開発哲学 / 开发理念

- **Library delegation** — Prefer library methods over naive implementations / ライブラリメソッドを優先 / 优先使用库方法
- **Minimal loops/branches** — Favor declarative/functional styles / 宣言的・関数型スタイルを優先 / 偏好声明式/函数式风格
- **TDD** — Write tests first, then implement / テストファーストで実装 / 先写测试，再实现
- **Document-driven** — Update docs with every implementation change / 実装変更ごとにドキュメント更新 / 每次实现变更时更新文档

## Reporting Issues / 問題報告 / 报告问题

Please open an issue on GitHub with:

GitHub で Issue を作成してください：

请在 GitHub 上创建 Issue：

- A clear description of the problem / 問題の明確な説明 / 问题的清晰描述
- Steps to reproduce / 再現手順 / 复现步骤
- Expected vs. actual behavior / 期待される動作と実際の動作 / 预期行为与实际行为
- Environment details (OS, Python version) / 環境情報 / 环境信息
