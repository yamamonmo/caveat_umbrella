
try:
    import voicevox_core.blocking
    import inspect
    
    Ort = voicevox_core.blocking.Onnxruntime
    print(f"Onnxruntime dir: {dir(Ort)}")
    
    # helper to print sig if callable
    def print_sig(name, obj):
        if callable(obj):
            try:
                print(f"{name} sig: {inspect.signature(obj)}")
            except:
                print(f"{name} is callable but signature failed")
        else:
            print(f"{name} is not callable")

    print_sig("Onnxruntime", Ort)
    if hasattr(Ort, "load_once"):
        print_sig("Onnxruntime.load_once", Ort.load_once)
    if hasattr(Ort, "from_options"):
         print_sig("Onnxruntime.from_options", Ort.from_options)

    # Check OpenJtalk too just to be sure
    Ojt = voicevox_core.blocking.OpenJtalk
    print_sig("OpenJtalk", Ojt)

except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
