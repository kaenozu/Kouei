# Kouei - AI競艇予測システム

## プロジェクト概要
AIを活用した競艇（ボートレース）予測・分析システム。機械学習モデルによる勝率予測、リアルタイムオッズ分析、自動ベッティング最適化を提供。

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
│   │   ├── main_api.py   # メインアプリ（エントリポイント）
│   │   ├── routers/      # 機能別ルーター
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
- `POST /api/betting/optimize` - 買い目最適化
- `GET /api/simulation` - バックテスト

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
pytest tests/ -v --cov=src --cov-report=html
```
