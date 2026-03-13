# LitScope API Documentation / API ドキュメント / API 文档

## Overview / 概要 / 概述

LitScope provides a RESTful API built with FastAPI. All endpoints are under the `/api/v1` prefix.

LitScope は FastAPI で構築された RESTful API を提供します。全エンドポイントは `/api/v1` プレフィックス下にあります。

LitScope 提供基于 FastAPI 构建的 RESTful API。所有端点位于 `/api/v1` 前缀下。

**Base URL**: `http://localhost:8000/api/v1`

**Interactive docs**: `http://localhost:8000/docs` (Swagger UI) / `http://localhost:8000/redoc` (ReDoc)

## Endpoints / エンドポイント / 端点

| Method | Path | Description / 説明 / 描述 |
|--------|------|---------------------------|
| `GET` | `/health` | Health check / ヘルスチェック / 健康检查 |
| `POST` | `/ingest` | Ingest EPUBs from directory / EPUB 取り込み / 导入 EPUB |
| `GET` | `/works` | List works (paginated) / 作品一覧 / 作品列表 |
| `GET` | `/works/{work_id}` | Work detail / 作品詳細 / 作品详情 |
| `GET` | `/works/{work_id}/vocabulary` | Vocabulary analysis / 語彙分析 / 词汇分析 |
| `GET` | `/works/{work_id}/syntax` | Syntax analysis / 構文分析 / 句法分析 |
| `GET` | `/works/{work_id}/readability` | Readability analysis / 可読性分析 / 可读性分析 |
| `GET` | `/compare?work_id=X&work_id=Y` | Compare works / 作品比較 / 作品比较 |

## Error Format / エラー形式 / 错误格式

All errors follow [RFC 7807](https://www.rfc-editor.org/rfc/rfc7807) Problem Details format:

全エラーは RFC 7807 Problem Details 形式に準拠します。

所有错误遵循 RFC 7807 Problem Details 格式：

```json
{
  "type": "about:blank",
  "title": "Not Found",
  "status": 404,
  "detail": "Work not found: nonexistent-id"
}
```

### Status Code Mapping / ステータスコード対応 / 状态码映射

| Exception | Status | Title |
|-----------|--------|-------|
| `EpubParseError` | 422 | Unprocessable Entity |
| `IngestionError` | 422 | Unprocessable Entity |
| `AnalyzerNotFoundError` | 404 | Not Found |
| `WorkNotFoundError` | 404 | Not Found |
| `CircularDependencyError` | 400 | Bad Request |
| `DependencyNotSatisfiedError` | 400 | Bad Request |
| `DatabaseError` | 500 | Internal Server Error |
| Unhandled exceptions | 500 | Internal Server Error |

## Request Tracing / リクエストトレーシング / 请求追踪

Every response includes an `X-Request-ID` header (UUID v4) for log correlation.

全レスポンスにログ関連付け用の `X-Request-ID` ヘッダー（UUID v4）が付与されます。

每个响应都包含 `X-Request-ID` 头（UUID v4），用于日志关联。

## Pagination / ページネーション / 分页

List endpoints support pagination via `page` and `page_size` query parameters:

```
GET /api/v1/works?page=2&page_size=10
```

Response includes `total`, `page`, and `page_size` fields alongside `items`.

## Filtering / フィルタリング / 过滤

The `/works` endpoint supports filtering:

| Parameter | Description / 説明 / 描述 |
|-----------|---------------------------|
| `author` | Filter by author name / 著者名でフィルタ / 按作者过滤 |
| `genre` | Filter by genre / ジャンルでフィルタ / 按类型过滤 |
| `search` | Search in title or author / タイトル・著者名検索 / 搜索标题或作者 |

## Caching / キャッシュ / 缓存

Analysis results are stored in DuckDB and served directly. No additional caching layer is needed for typical workloads. For production deployments with high traffic, consider placing a reverse proxy (nginx, Caddy) in front of the API.

分析結果は DuckDB に保存され直接提供されます。一般的なワークロードでは追加のキャッシュレイヤーは不要です。高トラフィックの本番環境では、API の前にリバースプロキシ（nginx, Caddy）の配置を検討してください。

分析结果存储在 DuckDB 中并直接提供。对于典型工作负载，不需要额外的缓存层。对于高流量的生产部署，建议在 API 前放置反向代理（nginx、Caddy）。
