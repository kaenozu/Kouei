# Kouei AI Kyotei System - User Manual

## 🚀 システム概要

KoueiはAIを活用した競艇（ボートレース）予測・分析システムです。機械学習モデルによる勝率予測、リアルタイムオッズ分析、自動ベッティング最適化を提供します。

## 📋 主要機能

### 1. スマートベッティング
- 高確率レースの自動検出（しきい値70%以上）
- 期待値（EV）計算
- リアルタイム状態追跡

### 2. AIコンシェルジュ
- レース詳細分析
- 購入戦略アドバイス
- 日次ダイジェスト

### 3. データ収集
- 自動データ収集
- リアルタイムオッズ更新
- 過去データバックフィル

### 4. 精度監視
- 的中率追跡
- ROIモニタリング
- モデルドリフト検出

## 🌐 アクセス方法

### Web UI
```
http://localhost:8080
```

### APIエンドポイント
```
http://localhost:8001
```

### APIドキュメント
```
http://localhost:8001/docs
```

## 🛠️ 主要APIエンドポイント

### スマートベッティング
```
GET /api/smart-bets
  ?date=YYYYMMDD     # 対象日付（省略可）
  &threshold=0.7     # 確率しきい値（0.5-0.95）
  &max_bets=20       # 最大表示件数

GET /api/smart-bets/backtest
  ?threshold=0.7     # 確率しきい値
  &days=7            # 過去日数
```

### AIコンシェルジュ
```
GET /api/concierge/status
  システムステータス確認

GET /api/concierge/daily-digest
  ?date=YYYYMMDD     # 対象日付（省略可）

POST /api/concierge/analyze-race
  {
    "date": "20241201",
    "jyo_cd": "01",
    "race_no": 1
  }

POST /api/concierge/chat
  {
    "question": "今日の高確率レースは？"
  }
```

### データ収集
```
POST /api/collection/start
  自動収集開始

POST /api/collection/stop
  自動収集停止

GET /api/collection/status
  収集ステータス確認

POST /api/collection/backfill
  {
    "start_date": "20241201",
    "end_date": "20241231"
  }

POST /api/collection/collect-today
  本日データ手動収集
```

### モニタリング
```
GET /api/monitoring/accuracy-stats
  ?days=30           # 過去日数

GET /api/monitoring/drift-check
  ?window=7          # ドリフト検出ウィンドウ

GET /api/monitoring/dashboard
  モニタリングダッシュボード
```

## 📊 Web UI操作ガイド

### ダッシュボード画面
1. 高確率レース一覧表示
2. 精度統計情報
3. 確信度別的中率チャート

### レース詳細画面
1. 各艇の予測確率
2. 選手情報
3. 装備性能
4. 天候条件

### 分析画面
1. 日次ダイジェスト
2. 会場別分析
3. 市場トレンド

## ⚙️ システム管理

### サービス起動
```bash
# APIサーバー
sudo systemctl start kouei-api

# Web UI
sudo systemctl start kouei-web
```

### サービス停止
```bash
sudo systemctl stop kouei-api
sudo systemctl stop kouei-web
```

### サービス状態確認
```bash
sudo systemctl status kouei-api
sudo systemctl status kouei-web
```

### ログ確認
```bash
# APIログ
sudo journalctl -u kouei-api -f

# Web UIログ
sudo journalctl -u kouei-web -f
```

## 🧪 開発者向け情報

### 環境構築
```bash
# 仮想環境作成
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# フロントエンド依存関係
cd web-ui
npm install
```

### 開発サーバー起動
```bash
# APIサーバー（開発）
python -m uvicorn src.api.main_api_new:app --reload --port 8001

# Web UI（開発）
cd web-ui
npm run dev
```

### テスト実行
```bash
# 単体テスト
pytest tests/ -v

# 統合テスト
pytest tests/integration/ -v
```

## 🔧 トラブルシューティング

### APIサーバーが起動しない
1. ポート8001が使用中でないか確認
2. データベース接続を確認
3. ログを確認（`journalctl -u kouei-api`）

### Web UIが表示されない
1. ポート8080が使用中でないか確認
2. ビルドが完了しているか確認
3. ログを確認（`journalctl -u kouei-web`）

### 予測精度が低い
1. モデルの再学習が必要か確認
2. データ収集が正常に行われているか確認
3. 精度監視ダッシュボードで詳細を確認

## 📞 サポート

問題が解決しない場合は以下の情報を添えてお問い合わせください：
- システムバージョン
- エラーログ
- 再現手順
