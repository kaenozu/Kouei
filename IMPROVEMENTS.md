# Kouei 改善実装レポート

## 実装済み改善一覧

### 1. 機能改善 (New Features)

#### 1.1 買い目最適化
- [x] Kelly基準による最適貭け金計算 (`/api/betting/optimize`)
- [x] フォーメーション/ボックス自動生成 (`/api/betting/formation`)
- [x] 期待値(EV)計算による推奨買い目

#### 1.2 レース展開予測
- [x] 逃げ/差し/捷り/捷り差し/まくりの確率予測
- [x] 予測レスポンスに`展開予測`フィールド追加

#### 1.3 時系列特徴量
- [x] `momentum_score`: 直近レースのモメンタム
- [x] `win_streak`: 連勝数
- [x] `top3_rate_recent`: 直近Nレースの3着以内率
- [x] `avg_rank_recent`: 直近平均着順
- [x] `rank_improvement`: 着順改善傾向

#### 1.4 分析機能拡張
- [x] 類似選手検索 (`/api/similar-racers/{racer_id}`)
- [x] 会場別コースマトリックス (`/api/stadium-matrix/{stadium}`)
- [x] AIコンシェルジュRAG強化

### 2. 性能改善 (Performance)

#### 2.1 キャッシュ活用
- [x] Redisキャッシュの全エンドポイント対応
- [x] DataFrameのメモリキャッシュ（ファイル変更検知で自動リロード）
- [x] 予測結果・オッズ・レース情報のTTL管理

#### 2.2 モデルウォームアップ
- [x] アプリ起動時にPredictorとDataFrameをプリロード
- [x] lifespanイベントハンドラでの初期化

#### 2.3 依存性注入
- [x] `@lru_cache`によるシングルトンインスタンス管理
- [x] FastAPI Dependsによるリソース注入

### 3. 保守性改善 (Maintainability)

#### 3.1 コード分割
- [x] main_api.pyを機能別Routerに分割:
  - `routers/prediction.py`: 予測関連
  - `routers/races.py`: レース情報
  - `routers/portfolio.py`: ポートフォリオ・シミュレーション
  - `routers/analysis.py`: 分析機能
  - `routers/betting.py`: 貭け最適化
  - `routers/sync.py`: データ同期
  - `routers/system.py`: システム管理

#### 3.2 スキーマ定義
- [x] Pydanticスキーマ (`schemas/common.py`):
  - `PredictionRequest`, `PredictionResponse`
  - `BettingOptimizeRequest`, `BacktestRequest`
  - `ConfidenceLevel`, `BetType`, `RaceStatus` (Enum)

#### 3.3 依存性管理
- [x] `dependencies.py`: 共通依存性の一元管理
- [x] 定数の集約（STADIUM_MAP, FEATURE_NAMES_JP）

#### 3.4 ドキュメント
- [x] `dear_llm.md`: AIアシスタント向けプロジェクト説明
- [x] 各モジュールのdocstring整備

#### 3.5 テスト
- [x] `tests/test_features.py`: 特徴量テスト
- [x] `tests/test_betting.py`: 貭け最適化テスト
- [x] `tests/test_api_routers.py`: APIルーターテスト
- [x] `tests/conftest.py`: 共通フィクスチャ
- [x] **42テスト全てパス**

### 4. UI/UX改善 (User Experience)

#### 4.1 フロントエンドコンポーネント
- [x] `components/RaceCard.jsx`: レースカード
- [x] `components/PredictionPanel.jsx`: 予測表示パネル
- [x] `components/BettingOptimizer.jsx`: 買い目最適化UI
- [x] `components/StatsCard.jsx`: 統計カード
- [x] `components/Skeleton.jsx`: ローディングスケルトン

#### 4.2 カスタムフック
- [x] `hooks/useApi.js`: APIフック集
  - `useFetch`, `useStatus`, `useStadiums`
  - `useTodayRaces`, `usePrediction`
  - `usePortfolio`, `useStrategies`
  - `useWebSocket`

#### 4.3 APIクライアント
- [x] `utils/api.js`: 統一APIクライアントクラス

#### 4.4 モバイル対応
- [x] レスポンシブCSS追加
- [x] タッチフレンドリーなボタンサイズ
- [x] テーブルの横スクロール対応

#### 4.5 アクセシビリティ
- [x] フォーカスリングスタイル
- [x] ハイコントラストモード対応
- [x] モーション削減モード対応
- [x] スクリーンリーダー用sr-onlyクラス

### 5. セキュリティ改善

#### 5.1 レート制限
- [x] `middleware/rate_limit.py`: レート制限ミドルウェア
- [x] バースト制限（1秒内の連続リクエスト制限）
- [x] 特定エンドポイントの厳しい制限

#### 5.2 入力バリデーション
- [x] Pydanticによるリクエストバリデーション
- [x] 日付/会場コードの正規表現バリデーション

---

## テスト結果

```
======================== 42 passed, 3 warnings in 3.77s ========================
```

全テストパス。

---

## APIエンドポイント一覧（新規追加）

| エンドポイント | メソッド | 説明 |
|------------|--------|------|
| `/api/betting/optimize` | POST | Kelly基準で買い目最適化 |
| `/api/betting/formation` | POST | フォーメーション/ボックス生成 |
| `/api/similar-racers/{racer_id}` | GET | 類似選手検索 |
| `/api/stadium-matrix/{stadium}` | GET | 会場別コースマトリックス |
| `/api/config` | GET/POST | 設定取得/更新 |
| `/api/drift-check` | GET | モデルドリフトチェック |
| `/health` | GET | ヘルスチェック |

---

## ファイル構造（新規追加）

```
src/api/
├── main_api_new.py      # 新メインAPI
├── dependencies.py      # 依存性注入
├── routers/
│   ├── __init__.py
│   ├── prediction.py
│   ├── races.py
│   ├── portfolio.py
│   ├── analysis.py
│   ├── betting.py
│   ├── sync.py
│   └── system.py
├── schemas/
│   └── common.py
└── middleware/
    └── rate_limit.py

src/features/
└── time_series.py       # 時系列特徴量

src/services/
└── prediction_service.py  # 予測サービス

web-ui/src/
├── components/
│   ├── RaceCard.jsx
│   ├── PredictionPanel.jsx
│   ├── BettingOptimizer.jsx
│   ├── StatsCard.jsx
│   └── Skeleton.jsx
├── hooks/
│   └── useApi.js
└── utils/
    └── api.js

tests/
├── conftest.py
├── test_features.py
├── test_betting.py
└── test_api_routers.py
```

---

## 使用方法

### 新APIの起動

```bash
cd /home/exedev/Kouei
source .venv/bin/activate
python -m uvicorn src.api.main_api_new:app --host 0.0.0.0 --port 8000
```

### テスト実行

```bash
python -m pytest tests/ --ignore=tests/e2e -v
```

### 買い目最適化APIの使用例

```bash
curl -X POST http://localhost:8000/api/betting/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "date": "20241230",
    "jyo": "02",
    "race": 1,
    "budget": 10000,
    "bet_type": "sanrentan",
    "kelly_fraction": 0.5
  }'
```

---

## 追加実装 (2026-01-06)

### 6. 季節特徴量 (Seasonal Features)

#### 6.1 新特徴量
- `season_sin`, `season_cos`: 季節の周期的エンコーディング
- `is_winter`, `is_summer`: 冬季/夏季フラグ
- `month`, `day_of_week`: 月/曜日
- `daylight_proxy`: 日照時間の代理変数
- `temperature`, `humidity`: 気温・湿度（データがある場合）

#### 6.2 実装ファイル
- `src/features/seasonal_features.py`
- `src/features/preprocessing.py`（統合）

### 7. 自動再トレーニングパイプライン

#### 7.1 機能
- ドリフト検出時の自動再トレーニング
- スケジュール実行（週次/月次）
- モデルバックアップ・ロールバック

#### 7.2 API
| エンドポイント | メソッド | 説明 |
|------------|--------|------|
| `/api/retrain/status` | GET | 再トレーニング状態確認 |
| `/api/retrain/trigger` | POST | 手動トリガー |
| `/api/retrain/schedule` | POST | スケジュール設定 |

#### 7.3 実装ファイル
- `src/model/auto_retrain.py`
- `src/api/routers/retrain.py`

### 8. LLM予測説明機能 (LLM Explainer)

#### 8.1 機能
- SHAP値を人間が理解しやすい日本語説明に変換
- OpenAI/Anthropic API対応（オプション）
- ルールベースのフォールバック
- レース全体のサマリー生成

#### 8.2 API
| エンドポイント | メソッド | 説明 |
|------------|--------|------|
| `/api/explain/status` | GET | 説明機能の状態 |
| `/api/explain/race` | POST | レース予測の説明生成 |
| `/api/explain/single` | POST | 単一予測の説明 |
| `/api/explain/features` | GET | 特徴量の日本語訳一覧 |

#### 8.3 実装ファイル
- `src/inference/llm_explainer.py`
- `src/api/routers/explainer.py`
- `web-ui/src/components/PredictionExplainer.jsx`

### 新規ファイル一覧

```
src/features/seasonal_features.py   # 季節特徴量
src/model/auto_retrain.py           # 自動再トレーニング
src/api/routers/retrain.py          # 再トレーニングAPI
src/inference/llm_explainer.py      # LLM説明生成
src/api/routers/explainer.py        # 説明API
web-ui/src/components/PredictionExplainer.jsx  # 説明UIコンポーネント
```
