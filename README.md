# 🚤 Kouei - AI競艇予測システム

[![CI/CD](https://github.com/user/kouei/workflows/CI/CD%20Pipeline/badge.svg)](https://github.com/user/kouei/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

AIを活用した競艇（ボートレース）予測・分析システム。機械学習モデルによる勝率予測、リアルタイムオッズ分析、自動ベッティング最適化などの機能を提供。

## ✨ 主な機能

### 予測・分析
- **アンサンブル予測**: LightGBM, XGBoost, CatBoostの統合モデル
- **ONNX高速推論**: 2-3倍高速な予測
- **相性マトリクス分析**: 選手×モーター×コースの3次元分析
- **気象予測統合**: 風向き・潮位の影響分析

### ベッティング最適化
- **Kelly基準**: 最適な賭け金計算
- **フォーメーション最適化**: 期待値ベースの複合買い推奨
- **ボックス買い提案**: 最適なボックス組み合わせ

### UI/UX
- **モバイル対応**: レスポンシブデザイン
- **PWA対応**: オフライン閲覧・プッシュ通知
- **リアルタイム更新**: WebSocket対応
- **AIコンシェルジュ**: 自然言語での質問対応

## 🚀 クイックスタート

### 環境変数設定
```bash
cp .env.example .env
# .envファイルを編集して設定
```

### ローカル実行
```bash
# 依存関係インストール
pip install -r requirements.txt

# APIサーバー起動
python -m uvicorn src.api.main_api:app --reload --port 8000

# フロントエンド起動
cd web-ui && npm install && npm run dev
```

### Docker実行
```bash
docker-compose up -d
```

## 📁 プロジェクト構造

```
kouei/
├── src/
│   ├── api/           # FastAPI エンドポイント
│   ├── model/         # ML モデル (LightGBM, XGBoost, CatBoost, ONNX)
│   ├── features/      # 特徴量エンジニアリング
│   ├── collector/     # データ収集 (非同期対応)
│   ├── analysis/      # 分析ロジック
│   ├── portfolio/     # ベッティング最適化
│   ├── inference/     # 推論・解説生成
│   ├── config/        # 設定管理
│   └── utils/         # ユーティリティ
├── web-ui/            # React フロントエンド
├── tests/             # テストコード
├── models/            # 学習済みモデル
├── data/              # データディレクトリ
└── config/            # 設定ファイル
```

## 🔧 設定

### 環境変数 (.env)

| 変数名 | 説明 | デフォルト |
|--------|------|-----------|
| `API_PORT` | APIサーバーポート | 8000 |
| `REDIS_HOST` | Redisホスト | localhost |
| `USE_ONNX` | ONNX推論を使用 | true |
| `DISCORD_WEBHOOK_URL` | Discord通知URL | - |
| `LLM_PROVIDER` | LLMプロバイダ (openai/anthropic/none) | none |

## 📊 API エンドポイント

### コアAPI (v1)
- `GET /api/status` - システム状態
- `GET /api/prediction` - レース予測
- `GET /api/simulation` - シミュレーション結果
- `POST /api/sync` - データ同期

### 拡張API (v2)
- `GET /api/v2/compatibility` - 相性分析
- `GET /api/v2/weather/forecast` - 気象予測
- `POST /api/v2/betting/optimize` - ベッティング最適化
- `POST /api/v2/commentary/generate` - AI解説生成

詳細は `/docs` (Swagger UI) を参照。

## 🧪 テスト

```bash
# 全テスト実行
pytest tests/ -v

# カバレッジ付き
pytest tests/ --cov=src --cov-report=html
```

## 📝 ライセンス

MIT License

## 🙏 謝辞

- [LightGBM](https://lightgbm.readthedocs.io/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)
