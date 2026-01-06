
import sys
import os
import platform
import subprocess

def check_step(name):
    print(f"\n[+] Checking {name}...")

def success(msg):
    print(f"  OK: {msg}")

def fail(msg):
    print(f"  FAIL: {msg}")

def main():
    print("=== Caveat Umbrella Diagnostic Script ===")
    
    # 1. Platform Info
    check_step("Platform Info")
    print(f"  System: {platform.system()} {platform.release()}")
    print(f"  Machine: {platform.machine()}")
    print(f"  Python: {sys.version}")
    
    # 2. Check Files
    check_step("Required Files")
    required_files = [
        "models/yolov3-tiny.weights",
        "models/yolov3-tiny.cfg",
        "models/coco.names",
        "main.py"
    ]
    for f in required_files:
        if os.path.exists(f):
            success(f"{f} found")
        else:
            fail(f"{f} NOT found!")
    
    # 3. Check Imports
    check_step("Library Imports")
    
    libs = [
        ("cv2", "OpenCV"),
        ("numpy", "NumPy"),
        ("requests", "Requests"),
        ("schedule", "Schedule"),
        ("sounddevice", "SoundDevice"),
        ("soundfile", "SoundFile"),
        ("voicevox_core", "VOICEVOX Core")
    ]
    
    for lib_name, human_name in libs:
        try:
            mod = __import__(lib_name)
            success(f"{human_name} imported successfully ({mod.__file__})")
            
            if lib_name == "voicevox_core":
                 # Extra check for voicevox_core accel mode
                 try:
                     from voicevox_core import AccelerationMode
                     success(f"VOICEVOX Core AccelerationMode available")
                 except ImportError:
                     fail("VOICEVOX Core imported but AccelerationMode missing (version mismatch?)")
                     
        except ImportError as e:
            fail(f"{human_name} ({lib_name}) could NOT be imported.")
            print(f"    Error: {e}")
        except Exception as e:
            fail(f"{human_name} crashed on import.")
            print(f"    Error: {e}")

    # 4. Check OpenJTalk Dictionary
    check_step("OpenJTalk Dictionary")
    dic_dir = "models/open_jtalk_dic_utf_8-1.11"
    if os.path.exists(dic_dir) and os.path.isdir(dic_dir):
        success(f"Dictionary directory found at {dic_dir}")
    else:
        fail(f"Dictionary directory missing at {dic_dir}")
        # Check if user has a similarly named directory (e.g. utf_8-111 as they typed)
        if os.path.exists("models"):
            contents = os.listdir("models")
            print(f"    Contents of models/: {contents}")

    print("\n=== Diagnosis Complete ===")

if __name__ == "__main__":
    main()
