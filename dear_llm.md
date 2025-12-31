# Kouei - AI競艇予測システム

## プロジェクト概要
AIを活用した競艇（ボートレース）予測・分析システム。機械学習モデルによる勝率予測、リアルタイムオッズ分析、自動ベッティング最適化を提供。

## 🔧 最新バージョン (v3.0.0) の変更点

- **モジュラーAPI構造**: 機能別に分離された新しいAPIアーキテクチャ
- **リアルタイムパイプライン**: 統合されたバックグラウンド処理
- **WebSocket通知**: レース開始・結果のリアルタイム通知
- **スナイパー機能**: レース直前の高精度予測

## 技術スタック
- **Backend**: Python 3.12, FastAPI, SQLite/PostgreSQL
- **ML**: LightGBM, XGBoost, CatBoost, ONNX
- **Frontend**: React 18, Vite, Recharts
- **Cache**: Redis
- **Deploy**: Docker, systemd

## ディレクトリ構造
```
kouei/
├── src/
│   ├── api/              # FastAPI ルーター
│   │   ├── main_api_new.py  # メインアプリ（新しいエントリポイント）
│   │   ├── routers/         # 機能別ルーター
│   │   │   ├── prediction.py # 予測エンドポイント
│   │   │   ├── races.py      # レース情報エンドポイント
│   │   │   ├── analysis.py   # 分析エンドポイント
│   │   │   ├── betting.py    # ベッティングエンドポイント
│   │   │   ├── portfolio.py  # ポートフォリオエンドポイント
│   │   │   ├── system.py     # システムエンドポイント
│   │   │   └── sync.py       # 同期エンドポイント
│   │   └── dependencies.py # 依存性注入
│   ├── model/            # ML モデル
│   ├── features/         # 特徴量エンジニアリング
│   ├── collector/        # データ収集
│   ├── analysis/         # 分析ロジック
│   ├── portfolio/        # ベッティング最適化
│   ├── inference/        # 推論・解説生成
│   ├── services/         # ビジネスロジック
│   ├── config/           # 設定管理
│   └── utils/            # ユーティリティ
├── web-ui/               # React フロントエンド
│   └── src/
│       ├── components/   # UIコンポーネント
│       ├── pages/        # ページコンポーネント
│       ├── hooks/        # カスタムフック
│       ├── store/        # Redux状態管理
│       └── utils/        # ユーティリティ
├── tests/                # テストコード
├── models/               # 学習済みモデル
└── data/                 # データディレクトリ
```

## 主要なエンドポイント
- `GET /api/status` - システム状態
- `GET /api/prediction` - レース予測
- `GET /api/today` - 本日のレース一覧
- `GET /api/racer/{racer_id}` - 選手統計
- `POST /api/betting/optimize` - 買い目最適化
- `GET /api/simulation` - バックテスト
- `GET /api/similar-races` - 類似レース検索
- `POST /api/concierge/chat` - AIコンシェルジュ

## 開発ガイドライン
1. 型ヒントを必ず使用
2. Pydanticでリクエスト/レスポンスを定義
3. テストカバレッジ70%以上を目標
4. コミット前にpytest実行

## 環境変数
- `API_PORT`: APIサーバーポート (default: 8000)
- `REDIS_HOST`: Redisホスト (default: localhost)
- `USE_ONNX`: ONNX推論使用 (default: true)
- `LLM_PROVIDER`: LLMプロバイダ (openai/anthropic/none)

## テスト実行
```bash
# 全テスト実行
pytest tests/ -v --cov=src --cov-report=html

# 特定のテスト実行
pytest tests/test_api_routers.py::TestAnalysisEndpoints::test_racer_stats -v

# E2Eテスト
pytest tests/e2e/ -v
```

## 🚀 開発環境構築

### 仮想環境作成
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# または .venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### データベース初期化
```bash
# データベースは自動作成されるが、必要に応じて
python src/db/database.py
```

### APIサーバー起動
```bash
# 新しいモジュラー構造で起動
python -m uvicorn src.api.main_api_new:app --reload --port 8000
```

### フロントエンド起動
```bash
cd web-ui
npm install
npm run dev
```

## 📊 APIドキュメント

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🧪 テストカバレッジ目標

- APIルーター: 80%以上
- 分析モジュール: 70%以上
- ベッティング最適化: 75%以上
- モデル推論: 60%以上

## 📈 パフォーマンスモニタリング

- モデルドリフト: `/api/drift-check`
- バックテスト履歴: `/api/backtest/history`
- パイプライン状態: ログまたはWebSocket通知

## 🚀 デプロイメント

本番環境ではsystemdサービスを使用してAPIサーバーを起動します。

```bash
sudo systemctl enable kouei-api
sudo systemctl start kouei-api
```
