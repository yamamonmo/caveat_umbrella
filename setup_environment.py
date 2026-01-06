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
VOICEVOX_CORE_VERSION = "0.16.3" 
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
            # Avoid CVE-2007-4559 (safely extract) - simple version for trusted source
            tar.extractall(path=MODELS_DIR)
        print("  Done.")
    except Exception as e:
        print(f"  [Error] Failed to extract dictionary: {e}")
    finally:
        if os.path.exists(dic_tar):
            os.remove(dic_tar)

def get_release_assets():
    try:
        print(f"  Fetching release assets for version {VOICEVOX_CORE_VERSION}...")
        resp = requests.get(VOICEVOX_RELEASE_API)
        resp.raise_for_status()
        return resp.json().get("assets", [])
    except Exception as e:
        print(f"  [Error] Failed to fetch release info: {e}")
        return []

def setup_voicevox_core(assets):
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
        print(f"  Detected Linux Aarch64 ({arch}). finding compatible wheel...")
        
        # Find wheel for aarch64
        # Target: voicevox_core-*-linux_aarch64.whl or manylinux...aarch64.whl
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
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", dest_whl])
                print("  Successfully installed voicevox_core.")
            except subprocess.CalledProcessError as e:
                print(f"  [Error] Failed to install wheel: {e}")

            # Cleanup
            # os.remove(dest_whl) # Optional: keep it or delete it
        else:
            print("  [Warning] Could not find compatible aarch64 wheel in release assets.")
            print("  Please install voicevox_core using the official installer or manually.")

    else:
        print(f"  [Info] Current platform is {system} {arch}. Skipping auto-install of RPi wheel.")

def setup_voicevox_libs(assets):
    """
    Download and extract the required shared libraries (libonnxruntime, libvoicevox_core)
    for Linux Aarch64.
    """
    arch = platform.machine().lower()
    if not ("aarch64" in arch or "arm64" in arch):
        return

    print("Checking VOICEVOX Core Shared Libraries...")
    
    # Find the zip file having arm64/aarch64 in name
    # e.g. voicevox_core-linux-arm64-0.16.3.zip (Note: often 'arm64' on GitHub assets even if 'aarch64' system)
    target_asset = None
    for asset in assets:
        name = asset["name"]
        # Look for linux and (arm64 or aarch64) and zip
        if "linux" in name and ("arm64" in name or "aarch64" in name) and name.endswith(".zip"):
            # Exclude 'gpu' or 'cuda' unless we specifically want them (stick to cpu/default for now)
            if "gpu" not in name and "cuda" not in name:
                target_asset = asset
                break
    
    if not target_asset:
        print("  [Error] Could not find shared libraries zip for aarch64/arm64.")
        return

    zip_url = target_asset["browser_download_url"]
    zip_name = target_asset["name"]
    zip_path = os.path.join(MODELS_DIR, zip_name)

    # Libraries we need to have in the root (or readable path)
    # Note: 0.16.x might have different lib names or versions, but usually libvoicevox_core.so is key
    needed_libs = ["libvoicevox_core.so"]
    
    # Check if they exist (simplistic check)
    if os.path.exists("libvoicevox_core.so") and os.path.exists("libonnxruntime.so.1.13.1"): 
        # Note: onnxruntime version might change per voicevox release, strict check is hard without manifest
        print("  [Skip] Shared libraries seem to exist.")
        # proceed to download anyway if unsure? for now skip if main lib exists
        return

    download_file(zip_url, zip_path)
    
    print("  Extracting shared libraries...")
    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            for file_info in z.infolist():
                # We search for the .so files inside
                if file_info.filename.endswith(".so") or ".so." in file_info.filename:
                    base_name = os.path.basename(file_info.filename)
                    # Allow libonnxruntime, libvoicevox_core
                    if "libonnxruntime" in base_name or "libvoicevox_core" in base_name:
                        print(f"    Extracting {base_name}...")
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
    
    # Fetch assets once to use for both wheel and libs
    assets = get_release_assets()
    if assets:
        setup_voicevox_core(assets)
        setup_voicevox_libs(assets)
    else:
        print("Skipping VOICEVOX Core setup due to API failure.")

if __name__ == "__main__":
    main()
