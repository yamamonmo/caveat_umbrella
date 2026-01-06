# 🌦️ ずんだもん生活支援AI (Zunda-Life-Support)

Raspberry Pi 4 で動作する、天気連動型の生活支援AIシステムです。
毎朝指定した時刻に天気予報を確認し、雨が降りそうな場合はカメラで「傘を持っているか」をチェックします。
結果に応じて、キャラクター（ずんだもん）が音声で注意喚起や称賛をしてくれます。


## 📦 必要要件 (Requirements)

* **ハードウェア**
    * Raspberry Pi 4 (RAM 4GB以上推奨)
    * USBウェブカメラ
    * スピーカー (3.5mmジャック または USB接続)
    * インターネット接続環境
* **ソフトウェア / API**
    * Raspberry Pi OS (64-bit 推奨)
    * Python 3.7+
    * VOICEVOX Engine (音声合成バックエンド)
    * OpenWeatherMap API Key (天気情報の取得)

## 🚀 セットアップ手順 (Setup)

# 仮想環境の作成

```bash

python3 -m venv .venv

```
# 仮想環境の有効化

```bash

source .venv/bin/activate

```

```bash

# 必要なライブラリを一括インストール
# - opencv-python: OpenCV本体
# - requests: API通信
# - schedule: 定期実行
# sounddevice: 再生用 (PortAudioラッパー)
# soundfile: WAVバイナリの読み込み用
# - numpy: 数値計算 (OpenCV依存)
pip install opencv-python requests schedule sounddevice soundfile numpy

```

### 1. ライブラリのインストール
ターミナルを開き、必要なパッケージとPythonライブラリをインストールします。

```bash

# システムパッケージ
sudo apt update
sudo apt install -y libopenblas-dev libopencv-dev portaudio19-dev python3-full

# Pythonライブラリ
pip install requests schedule simpleaudio opencv-python numpy
```

### 2. YOLO (画像認識モデル) のダウンロード
同じディレクトリにYOLOv3-Tinyの学習済みモデルをダウンロードします。

```bash
# 重みファイル
wget [https://pjreddie.com/media/files/yolov3-tiny.weights](https://pjreddie.com/media/files/yolov3-tiny.weights)
# 設定ファイル
wget [https://github.com/pjreddie/darknet/blob/master/cfg/yolov3-tiny.cfg?raw=true](https://github.com/pjreddie/darknet/blob/master/cfg/yolov3-tiny.cfg?raw=true) -O yolov3-tiny.cfg
# クラス名ファイル
wget [https://github.com/pjreddie/darknet/blob/master/data/coco.names?raw=true](https://github.com/pjreddie/darknet/blob/master/data/coco.names?raw=true) -O coco.names
```

### 3. VOICEVOX Engine の起動
別途インストールした VOICEVOX Engine を起動し、ポート `50021` で待機させてください。
（Dockerを使用する場合の例）:
```bash
docker run --rm -it -p "127.0.0.1:50021:50021" voicevox/voicevox_engine:cpu-ubuntu20.04-latest
```


## ▶️ 実行方法 (Usage)

すべてのファイル（`main.py`, `yolov3-tiny.*`, `coco.names`）が同じフォルダにある状態で実行します。

```bash
python3 main.py
```

指定した時刻（デフォルトは 07:30）になると自動的に動作します。
