import os
import requests
import tarfile
import zipfile
import subprocess
import sys
import platform
import shutil

# Configuration
MODELS_DIR = "models"
YOLO_URLS = {
    "yolov3-tiny.weights": "https://pjreddie.com/media/files/yolov3-tiny.weights",
    "yolov3-tiny.cfg": "https://raw.githubusercontent.com/pjreddie/darknet/master/cfg/yolov3-tiny.cfg",
    "coco.names": "https://raw.githubusercontent.com/pjreddie/darknet/master/data/coco.names"
}
OPEN_JTALK_DIC_URL = "https://sourceforge.net/projects/open-jtalk/files/Dictionary/open_jtalk_dic-1.11/open_jtalk_dic_utf_8-1.11.tar.gz/download"

# Voicevox Core Release
# Note: Using 0.15.3 as a stable baseline that has aarch64 wheels. 
# Adjust version if needed or logic to find latest.
VOICEVOX_CORE_VERSION = "0.15.3" 
VOICEVOX_RELEASE_API = f"https://api.github.com/repos/VOICEVOX/voicevox_core/releases/tags/{VOICEVOX_CORE_VERSION}"

def download_file(url, dest_path):
    if os.path.exists(dest_path):
        print(f"  [Skip] Already exists: {dest_path}")
        return
    
    print(f"  Downloading: {url}...")
    try:
        resp = requests.get(url, stream=True)
        resp.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        print("  Done.")
    except Exception as e:
        print(f"  [Error] Failed to download {url}: {e}")
        if os.path.exists(dest_path):
            os.remove(dest_path)

def setup_yolo():
    print("Checking YOLO models...")
    for filename, url in YOLO_URLS.items():
        download_file(url, os.path.join(MODELS_DIR, filename))

def setup_open_jtalk():
    print("Checking Open JTalk Dictionary...")
    dic_tar = os.path.join(MODELS_DIR, "open_jtalk_dic.tar.gz")
    dic_dir = os.path.join(MODELS_DIR, "open_jtalk_dic_utf_8-1.11")
    
    if os.path.isdir(dic_dir):
        print(f"  [Skip] Dictionary directory exists: {dic_dir}")
        return

    download_file(OPEN_JTALK_DIC_URL, dic_tar)
    
    print("  Extracting dictionary...")
    try:
        with tarfile.open(dic_tar, "r:gz") as tar:
            tar.extractall(path=MODELS_DIR)
        print("  Done.")
    except Exception as e:
        print(f"  [Error] Failed to extract dictionary: {e}")
    finally:
        if os.path.exists(dic_tar):
            os.remove(dic_tar)

def setup_voicevox_core():
    print("Checking VOICEVOX Core...")
    # Check if installed
    try:
        import voicevox_core
        print("  [Skip] voicevox_core is already installed in the environment.")
        return
    except ImportError:
        pass

    # Determine architecture
    arch = platform.machine().lower()
    system = platform.system().lower()
    
    # Simple check for RPi (linux aarch64)
    if system == "linux" and ("aarch64" in arch or "arm64" in arch):
        print(f"  Detected Linux Aarch64 ({arch}). Fetching VOICEVOX Core wheel...")
        
        try:
            resp = requests.get(VOICEVOX_RELEASE_API)
            resp.raise_for_status()
            assets = resp.json().get("assets", [])
            
            # Find wheel for aarch64
            # Look for: voicevox_core-*-linux_aarch64.whl or manylinux...aarch64.whl
            target_asset = None
            for asset in assets:
                name = asset["name"]
                if name.endswith("whl") and "aarch64" in name:
                    target_asset = asset
                    break
            
            if target_asset:
                whl_url = target_asset["browser_download_url"]
                whl_name = target_asset["name"]
                dest_whl = os.path.join(MODELS_DIR, whl_name)
                
                download_file(whl_url, dest_whl)
                
                print(f"  Installing {whl_name}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", dest_whl])
                
                # Cleanup
                # os.remove(dest_whl) # Optional: keep it or delete it
            else:
                print("  [Warning] Could not find compatible aarch64 wheel in release assets.")
                print("  Please install voicevox_core using the official installer or manually.")
                
        except Exception as e:
            print(f"  [Error] Failed to setup VOICEVOX Core: {e}")

    else:
        print(f"  [Info] Current platform is {system} {arch}. Skipping auto-install of RPi wheel.")
        print("  If you are testing on Windows/Mac, please install voicevox_core manually if needed.")

def setup_voicevox_libs():
    """
    Download and extract the required shared libraries (libonnxruntime, libvoicevox_core)
    for Linux Aarch64, as they are missing from the wheel.
    """
    arch = platform.machine().lower()
    if not ("aarch64" in arch or "arm64" in arch):
        return

    print("Checking VOICEVOX Core Shared Libraries...")
    
    # URL for the core libraries zip
    # Using the same version as the wheel logic (0.15.3)
    CORE_ZIP_URL = f"https://github.com/VOICEVOX/voicevox_core/releases/download/{VOICEVOX_CORE_VERSION}/voicevox_core-linux-aarch64-cpu-{VOICEVOX_CORE_VERSION}.zip"
    
    # Libraries we need to have in the root (or readable path)
    needed_libs = ["libonnxruntime.so.1.13.1", "libvoicevox_core.so"]
    
    # Check if they exist
    missing = [lib for lib in needed_libs if not os.path.exists(lib)]
    if not missing:
        print("  [Skip] Shared libraries already exist.")
        return

    print(f"  Downloading Core Libraries from {CORE_ZIP_URL}...")
    zip_path = "voicevox_core_libs.zip"
    download_file(CORE_ZIP_URL, zip_path)
    
    print("  Extracting shared libraries...")
    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            # The zip usually has a folder structure like "voicevox_core-linux-..."
            # We search for the .so files inside
            for file_info in z.infolist():
                if file_info.filename.endswith(".so") or ".so." in file_info.filename:
                    # We only want the specific libs we need
                    base_name = os.path.basename(file_info.filename)
                    if any(n in base_name for n in ["libonnxruntime", "libvoicevox_core"]):
                        print(f"    Extracting {base_name}...")
                        # Extract to current directory
                        with z.open(file_info) as source, open(base_name, "wb") as target:
                            shutil.copyfileobj(source, target)
                            
        print("  Done. (Note: You may need to run with LD_LIBRARY_PATH=. python3 main.py)")
        
    except Exception as e:
        print(f"  [Error] Failed to extract libraries: {e}")
    finally:
        if os.path.exists(zip_path):
            os.remove(zip_path)

def main():
    if not os.path.exists(MODELS_DIR):
        os.makedirs(MODELS_DIR)
    
    setup_yolo()
    setup_open_jtalk()
    setup_voicevox_core()
    setup_voicevox_libs()

if __name__ == "__main__":
    main()
