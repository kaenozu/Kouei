# 🚤 Kouei - AI競艇予測システム

[![CI/CD](https://github.com/user/kouei/workflows/CI/CD%20Pipeline/badge.svg)](https://github.com/user/kouei/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

AIを活用した競艇（ボートレース）予測・分析システム。機械学習モデルによる勝率予測、リアルタイムオッズ分析、自動ベッティング最適化などの機能を提供。

## 🔧 最新バージョン (v3.0.0) の変更点

- **モジュラーAPI構造**: 機能別に分離された新しいAPIアーキテクチャ
- **リアルタイムパイプライン**: 統合されたバックグラウンド処理
- **WebSocket通知**: レース開始・結果のリアルタイム通知
- **スナイパー機能**: レース直前の高精度予測

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

# APIサーバー起動 (新しいモジュラー構造)
python -m uvicorn src.api.main_api_new:app --reload --port 8000

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
│   │   ├── main_api_new.py  # メインアプリ（新しいモジュラー構造）
│   │   ├── routers/         # 機能別ルーター
│   │   │   ├── prediction.py # 予測エンドポイント
│   │   │   ├── races.py      # レース情報エンドポイント
│   │   │   ├── analysis.py   # 分析エンドポイント
│   │   │   ├── betting.py    # ベッティングエンドポイント
│   │   │   ├── portfolio.py  # ポートフォリオエンドポイント
│   │   │   ├── system.py     # システムエンドポイント
│   │   │   └── sync.py       # 同期エンドポイント
│   │   └── dependencies.py   # 依存性注入
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

### システム
- `GET /` - APIルート
- `GET /health` - ヘルスチェック
- `GET /api/status` - システム状態

### レース情報
- `GET /api/stadiums` - 競技場一覧
- `GET /api/races` - レース情報
- `GET /api/today` - 本日のレース

### 予測
- `GET /api/prediction` - レース予測
- `GET /api/similar-races` - 類似レース検索
- `POST /api/simulate-what-if` - 仮想シミュレーション

### 分析
- `GET /api/racer/{racer_id}` - 選手統計
- `GET /api/compatibility` - 相性分析
- `GET /api/stadium-matrix/{stadium}` - 会場マトリクス
- `POST /api/concierge/chat` - AIコンシェルジュ

### ベッティング
- `GET /api/odds` - オッズ情報
- `POST /api/betting/optimize` - 最適化
- `POST /api/betting/formation` - フォーメーション

### ポートフォリオ
- `GET /api/portfolio` - ポートフォリオ状態
- `GET /api/simulation` - シミュレーション
- `GET /api/backtest` - バックテスト
- `GET /api/strategies` - 戦略一覧

### 同期
- `GET /api/sync` - 同期状態
- `GET /api/config` - 設定取得
- `POST /api/config` - 設定更新

詳細は `/docs` (Swagger UI) または `/redoc` (ReDoc) を参照。

## 🧪 テスト

```bash
# 依存関係インストール
pip install pytest pytest-cov pytest-asyncio

# 全テスト実行
pytest tests/ -v

# 特定のテスト実行
pytest tests/test_api_routers.py::TestAnalysisEndpoints::test_racer_stats -v

# カバレッジ付き
pytest tests/ --cov=src --cov-report=html

# E2Eテスト (Playwrightが必要)
pip install pytest-playwright
playwright install
pytest tests/e2e/ -v
```

## 📝 ライセンス

MIT License

## 🙏 謝辞

- [LightGBM](https://lightgbm.readthedocs.io/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)

## 📈 パフォーマンスモニタリング

- モデルドリフト検出: `/api/drift-check`
- バックテスト履歴: `/api/backtest/history`
- パイプライン状態: ログまたはWebSocket通知

## 🚀 デプロイメント

### systemdサービス設定

```ini
# /etc/systemd/system/kouei-api.service
[Unit]
Description=Kouei API Service
After=network.target

[Service]
Type=simple
User=exedev
WorkingDirectory=/home/exedev/Kouei
ExecStart=/home/exedev/Kouei/.venv/bin/uvicorn src.api.main_api_new:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

### nginxリバースプロキシ設定

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🤝 コントリビューション

1. Forkしてfeatureブランチを作成
2. 変更をコミット
3. テストを実行
4. Pull Requestを作成

## 📞 サポート

- Issues: GitHub Issuesを使用
- ドキュメント: `/docs` または `/redoc`
- ログ: `logs/` ディレクトリ
