import cv2
import numpy as np
import requests
import json
import time
import schedule
import simpleaudio as sa
import os

# ==========================================
# ⚙️ 設定エリア (環境に合わせて変更してください)
# ==========================================

# OpenWeatherMap API設定
OPENWEATHER_API_KEY = "ここに取得したAPIキーを入力"
CITY_NAME = "Tokyo,JP"
WEATHER_ENDPOINT = "http://api.openweathermap.org/data/2.5/forecast"

# VOICEVOX設定
VOICEVOX_URL = "http://127.0.0.1:50021"
SPEAKER_ID = 3  # 3: ずんだもん(ノーマル), 1: ずんだもん(あまあま) など

# YOLO (画像認識) 設定
YOLO_WEIGHTS = "yolov3-tiny.weights"
YOLO_CONFIG = "yolov3-tiny.cfg"
COCO_NAMES = "coco.names"

# 実行時刻設定
CHECK_TIME = "07:30"

# 降水確率の閾値 (予報のリスト中にRain判定があるか、またはpopがこの値を超えたら雨とみなす)
RAIN_THRESHOLD_PERCENT = 0.3  # 30%

# ==========================================
# 🔊 音声合成関数 (VOICEVOX)
# ==========================================
def speak(text):
    """
    VOICEVOX APIを使ってテキストを音声に変換し、再生する
    """
    print(f"🗣️ ずんだもん: 「{text}」")
    try:
        # 1. 音声合成用のクエリを作成
        query_payload = {"text": text, "speaker": SPEAKER_ID}
        query_res = requests.post(
            f"{VOICEVOX_URL}/audio_query", 
            params=query_payload
        )
        query_res.raise_for_status()
        query_data = query_res.json()

        # 2. 音声を合成
        synth_payload = {"speaker": SPEAKER_ID}
        synth_res = requests.post(
            f"{VOICEVOX_URL}/synthesis",
            params=synth_payload,
            json=query_data
        )
        synth_res.raise_for_status()

        # 3. 再生 (simpleaudioを使用)
        # バイナリデータからWaveObjectを作成して再生
        wave_obj = sa.WaveObject.from_wave_read(synth_res.content)
        play_obj = wave_obj.play()
        play_obj.wait_done() # 再生終了まで待機

    except Exception as e:
        print(f"❌ 音声再生エラー: {e}")
        print("VOICEVOX Engineが起動しているか確認してください。")

# ==========================================
# 🌦️ 天気予報関数 (OpenWeatherMap)
# ==========================================
def check_rain_forecast():
    """
    今後24時間以内に雨が降る予報があるかチェックする
    戻り値: True(雨予報あり), False(晴れ/曇り)
    """
    print("🌤️ 天気予報を確認中...")
    params = {
        "q": CITY_NAME,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "ja"
    }
    
    try:
        response = requests.get(WEATHER_ENDPOINT, params=params)
        response.raise_for_status()
        data = response.json()
        
        # 直近の予報データを確認 (3時間ごと×8枠 = 24時間分)
        forecasts = data.get("list", [])[:8]
        
        will_rain = False
        for f in forecasts:
            weather_main = f["weather"][0]["main"]
            pop = f.get("pop", 0) # 降水確率 (0.0 - 1.0)
            
            # 天気がRain/Drizzle/Thunderstorm、または降水確率が高い場合
            if weather_main in ["Rain", "Drizzle", "Thunderstorm"] or pop >= RAIN_THRESHOLD_PERCENT:
                will_rain = True
                break
        
        return will_rain

    except Exception as e:
        print(f"❌ 天気取得エラー: {e}")
        speak("天気予報の取得に失敗したのだ。")
        return False # エラー時はとりあえずFalseにする

# ==========================================
# 📷 画像認識関数 (YOLO + OpenCV)
# ==========================================
def check_umbrella():
    """
    カメラを起動し、YOLOを使って傘(umbrella)があるかチェックする
    戻り値: True(傘あり), False(傘なし)
    """
    print("📷 カメラを起動して傘を探しています...")
    
    # YOLOモデルの読み込み
    try:
        net = cv2.dnn.readNet(YOLO_WEIGHTS, YOLO_CONFIG)
        with open(COCO_NAMES, "r") as f:
            classes = [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        print("❌ YOLO関連ファイルが見つかりません。")
        speak("画像認識の設定ファイルが見つからないのだ。")
        return False

    layer_names = net.getLayerNames()
    try:
        output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]
    except:
        # OpenCVのバージョンによって挙動が違う場合のフォールバック
        output_layers = [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]

    # カメラ起動
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ カメラが開けません")
        speak("カメラが起動できないのだ。")
        return False

    has_umbrella = False
    
    # 判定の精度を上げるため、数フレーム確認する
    check_frames = 10 
    
    for _ in range(check_frames):
        ret, frame = cap.read()
        if not ret:
            break
        
        height, width, channels = frame.shape

        # YOLOに入力するためのBlob作成
        blob = cv2.dnn.blobFromImage(frame, 0.00392, (320, 320), (0, 0, 0), True, crop=False)
        net.setInput(blob)
        outs = net.forward(output_layers)

        # 検出結果の解析
        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                
                # 信頼度が0.5以上かつ、クラス名が umbrella の場合
                if confidence > 0.5 and classes[class_id] == "umbrella":
                    has_umbrella = True
                    break
            if has_umbrella: break
        if has_umbrella: break
    
    cap.release()
    return has_umbrella

# ==========================================
# 🧠 メインルーチン
# ==========================================
def morning_routine():
    """
    毎朝実行される一連の流れ
    """
    print(f"\n⏰ {CHECK_TIME} になりました。ルーチンを開始します。")
    
    # 1. 天気チェック
    is_rainy = check_rain_forecast()
    
    if not is_rainy:
        # 晴れの場合
        speak("おはようございます。今日は雨の心配はなさそうなのだ。行ってらっしゃいなのだ！")
    else:
        # 雨の場合
        speak("おはようございます。今日は雨が降りそうなのだ。傘を持っているか確認するのだ。カメラに傘を見せてほしいのだ。")
        
        # ユーザーが準備する時間を少し待つ
        time.sleep(3)
        
        # 2. 傘チェック
        has_umbrella = check_umbrella()
        
        if has_umbrella:
            speak("確認できたのだ！ 準備万端でえらいのだ。気をつけて行ってらっしゃいなのだ！")
        else:
            # 警告音（ブザー音などを鳴らしても良いが今回はセリフで強調）
            speak("傘が見当たらないのだ！ 今日は雨だから、忘れずに傘を持っていくのだ！")

# ==========================================
# 🚀 エントリーポイント
# ==========================================
if __name__ == "__main__":
    print(f"🤖 ずんだもん生活支援AI 起動中...")
    print(f"📅 毎日 {CHECK_TIME} に天気と傘のチェックを行います。")
    print("Ctrl+C で終了します。")

    # スケジュール登録
    schedule.every().day.at(CHECK_TIME).do(morning_routine)

    # テスト用: 今すぐ動作確認したい場合は以下のコメントアウトを外してください
    # morning_routine()

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 システムを終了します。")