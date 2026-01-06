import os
import sys
import time
import json
import requests
import schedule
import numpy as np
import sounddevice as sd
import soundfile as sf
import io
import cv2
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# ==========================================
# ⚙️ 設定エリア
# ==========================================

# 位置情報 (Open-Meteo用)
LATITUDE = float(os.getenv("LATITUDE", "35.6895"))
LONGITUDE = float(os.getenv("LONGITUDE", "139.6917"))

# 実行時刻
CHECK_TIME = os.getenv("CHECK_TIME", "07:30")

# 降水確率の閾値
RAIN_THRESHOLD_PERCENT = float(os.getenv("RAIN_THRESHOLD_PERCENT", "0.3"))

# SPEAKER ID (ずんだもん=3)
SPEAKER_ID = int(os.getenv("SPEAKER_ID", "3"))

# モデル設定
MODELS_DIR = "models"
YOLO_WEIGHTS = os.path.join(MODELS_DIR, "yolov3-tiny.weights")
YOLO_CONFIG = os.path.join(MODELS_DIR, "yolov3-tiny.cfg")
COCO_NAMES = os.path.join(MODELS_DIR, "coco.names")
OPEN_JTALK_DICT_DIR = os.path.join(MODELS_DIR, "open_jtalk_dic_utf_8-1.11")

# VOICEVOX Core 初期化用グローバル変数
core = None

# ==========================================
# 🔊 音声合成関数 (VOICEVOX Core)
# ==========================================
def init_voicevox_core():
    global core
    try:
        from voicevox_core import VoicevoxCore, AccelerationMode
        
        if not os.path.exists(OPEN_JTALK_DICT_DIR):
            print(f"❌ 辞書ディレクトリが見つかりません: {OPEN_JTALK_DICT_DIR}")
            print("setup.sh または setup_environment.py を実行してください。")
            sys.exit(1)

        print("🔊 VOICEVOX Coreを初期化中...")
        # AccelerationMode.AUTO はGPUがあれば使い、なければCPUを使う
        core = VoicevoxCore(
            acceleration_mode=AccelerationMode.AUTO,
            open_jtalk_dict_dir=OPEN_JTALK_DICT_DIR
        )
        
        # モデル読み込み
        if not core.is_model_loaded(SPEAKER_ID):
            core.load_model(SPEAKER_ID)
            
        print("✅ VOICEVOX Core 準備完了")
        
    except ImportError as e:
        print(f"❌ voicevox_core が読み込めませんでした。詳細: {e}")
        # import traceback
        # traceback.print_exc()
        print("setup.sh を実行してセットアップを行ってください。")
        # 開発中のWindows等でライブラリがない場合のフォールバック（ログのみ）
        core = None

def speak(text):
    """
    VOICEVOX Coreを使ってテキストを音声に変換し、再生する
    """
    print(f"🗣️ ずんだもん: 「{text}」")
    
    if core is None:
        print("⚠️ 音声合成エンジンが利用できないため、スキップします。")
        return

    try:
        # 音声合成 (wavバイナリが返る)
        wav_bytes = core.tts(text, SPEAKER_ID)
        
        # 再生
        # バイト列をファイルライクオブジェクトにしてsoundfileで読み込む
        data, samplerate = sf.read(io.BytesIO(wav_bytes))
        sd.play(data, samplerate)
        sd.wait()
        
    except Exception as e:
        print(f"❌ 音声再生エラー: {e}")

# ==========================================
# 🌦️ 天気予報関数 (Open-Meteo)
# ==========================================
def check_rain_forecast():
    """
    Open-Meteo APIを使用して、今後12時間以内に雨が降るかチェックする
    """
    print("🌤️ Open-Meteoで天気予報を確認中...")
    
    endpoint = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "hourly": "precipitation_probability",
        "timezone": "auto",
        "forecast_days": 1
    }
    
    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        data = response.json()
        
        hourly = data.get("hourly", {})
        probs = hourly.get("precipitation_probability", [])
        
        # 現在時刻から12時間分をチェック
        # (APIは0時から始まるリストを返すので、現在時刻のインデックスを取得する簡易実装)
        current_hour = int(time.strftime("%H"))
        # 24時間データのうち、現在時刻以降〜＋12時間
        check_probs = probs[current_hour : current_hour + 12]
        
        will_rain = False
        max_prob = 0
        
        for p in check_probs:
            # Noneが入る場合があるので0扱いにする
            prob = p if p is not None else 0
            if prob > max_prob:
                max_prob = prob
                
            # 降水確率が閾値を超えたら雨判定 (閾値0.3 => 30%)
            if prob >= (RAIN_THRESHOLD_PERCENT * 100):
                will_rain = True
        
        print(f"☂️ 最大降水確率: {max_prob}% (判定: {'雨' if will_rain else '晴れ'})")
        return will_rain
        
    except Exception as e:
        print(f"❌ 天気取得エラー: {e}")
        speak("天気予報の取得に失敗したのだ。")
        return False

# ==========================================
# 📷 画像認識関数 (YOLO + OpenCV)
# ==========================================
def check_umbrella():
    """
    カメラを起動し、YOLOを使って傘(umbrella)があるかチェックする
    """
    print("📷 カメラを起動して傘を探しています...")
    
    if not os.path.exists(YOLO_WEIGHTS) or not os.path.exists(YOLO_CONFIG):
        print("❌ YOLOモデルファイルが見つかりません。")
        speak("画像認識のモデルがないのだ。セットアップを確認してほしいのだ。")
        return False

    try:
        net = cv2.dnn.readNet(YOLO_WEIGHTS, YOLO_CONFIG)
        with open(COCO_NAMES, "r") as f:
            classes = [line.strip() for line in f.readlines()]
    except Exception as e:
        print(f"❌ モデル読み込みエラー: {e}")
        return False

    layer_names = net.getLayerNames()
    try:
        output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]
    except:
        output_layers = [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ カメラが開けません")
        speak("カメラが起動できないのだ。接続を確認するのだ。")
        return False

    has_umbrella = False
    check_frames = 15 # フレーム数を少し増やす
    
    for i in range(check_frames):
        ret, frame = cap.read()
        if not ret:
            break
        
        # YOLO入力処理
        blob = cv2.dnn.blobFromImage(frame, 0.00392, (320, 320), (0, 0, 0), True, crop=False)
        net.setInput(blob)
        outs = net.forward(output_layers)

        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                
                if confidence > 0.5 and classes[class_id] == "umbrella":
                    has_umbrella = True
                    print(f"☂️ 傘を検出しました！ (信頼度: {confidence:.2f})")
                    break
            if has_umbrella: break
        if has_umbrella: break
        
        time.sleep(0.1)
    
    cap.release()
    return has_umbrella

# ==========================================
# 🧠 メインルーチン
# ==========================================
def morning_routine():
    print(f"\n⏰ {CHECK_TIME} になりました。ルーチンを開始します。")
    
    is_rainy = check_rain_forecast()
    
    if not is_rainy:
        speak("おはようございます。今日は雨の心配はなさそうなのだ。行ってらっしゃいなのだ！")
    else:
        speak("おはようございます。今日は雨が降りそうなのだ。傘を持っているか確認するのだ。")
        # 準備待ち
        time.sleep(2)
        
        has_umbrella = check_umbrella()
        
        if has_umbrella:
            speak("確認できたのだ！ 傘を持っていてえらいのだ。気をつけて行ってらっしゃいなのだ！")
        else:
            speak("大変なのだ！ 傘が見当たらないのだ！ 雨に濡れちゃうから、絶対に傘を持っていくのだ！")

# ==========================================
# 🚀 エントリーポイント
# ==========================================
if __name__ == "__main__":
    print(f"🤖 ずんだもん生活支援AI (Dockerless Edition) 起動中...")
    
    # 1. 音声合成エンジンの初期化
    init_voicevox_core()
    
    # 2. スケジュール登録
    print(f"📅 毎日 {CHECK_TIME} にチェックを行います。")
    schedule.every().day.at(CHECK_TIME).do(morning_routine)
    
    print("Ctrl+C で終了します。")

    # (デバッグ用) 起動時に引数 --test があれば即時実行
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("🧪 テストモード: 今すぐルーチンを実行します")
        morning_routine()

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 システムを終了します。")
