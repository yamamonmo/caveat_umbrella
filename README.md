# 🌦️ ずんだもん生活支援AI (Dockerless Edition)

Raspberry Pi 4 で動作する、天気連動型の生活支援AIシステムです。
Dockerを使用せず、**Voicevox Core** を直接利用して軽量に動作します。
毎朝指定した時刻に Open-Meteo で天気を確認し、雨が降りそうな場合はWebカメラで「傘を持っているか」をチェックします。

## 📦 必要要件 (Requirements)

* **ハードウェア**
    * Raspberry Pi 4 (64-bit OS 推奨)
    * USBウェブカメラ
    * スピーカー (3.5mmジャック または USB接続)
    * インターネット接続環境
* **ソフトウェア**
    * Raspberry Pi OS (64-bit / Bullseye or Bookworm)
    * Python 3.9+

## 🚀 セットアップ手順 (Setup)

### 1. 自動セットアップ
付属の `setup.sh` を実行するだけで、仮想環境の作成から必要なモデル(YOLO, Voicevox Core, 辞書)のダウンロードまで自動で行われます。

```bash
# スクリプトに実行権限を付与
chmod +x setup.sh

# セットアップ開始
./setup.sh
```

この操作で以下の処理が行われます：
- 仮想環境 (`.venv`) の作成
- 必要なライブラリのインストール (`requirements.txt`)
- YOLO学習済みモデル (`yolov3-tiny`) のダウンロード
- Open JTalk 辞書のセットアップ
- VOICEVOX Core のセットアップ

### 2. 環境設定
`.env.example` をコピーして `.env` を作成し、必要に応じて編集します（緯度・経度など）。

```bash
cp .env.example .env
nano .env
```

| 変数名 | 説明 |
| --- | --- |
| `LATITUDE` | 設置場所の緯度 (デフォルト: 東京) |
| `LONGITUDE` | 設置場所の経度 |
| `CHECK_TIME` | チェックを行う毎朝の時刻 (例: 07:30) |

## ▶️ 実行方法 (Usage)

セットアップ完了後、以下の手順で起動します。

```bash
# 仮想環境に入る
source .venv/bin/activate

# アプリケーション起動
python main.py
```

### テスト実行
すぐに動作を確認したい場合は、`--test` オプションを付けて実行します。

```bash
python main.py --test
```

## 📂 ディレクトリ構成
```
.
├── main.py              # メインスクリプト
├── setup.sh             # 自動セットアップスクリプト
├── setup_environment.py # リソース取得用スクリプト
├── requirements.txt     # 依存ライブラリ一覧
├── .env                 # 環境変数設定
└── models/              # ダウンロードされたモデルファイル格納場所
```
