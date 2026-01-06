
try:
    import voicevox_core.blocking
    import inspect
    
    print(f"Members: {dir(voicevox_core.blocking)}")
    
    if hasattr(voicevox_core.blocking, "OpenJtalk"):
        print(f"OpenJtalk sig: {inspect.signature(voicevox_core.blocking.OpenJtalk)}")
    
    if hasattr(voicevox_core.blocking, "Onnxruntime"):
        print(f"Onnxruntime sig: {inspect.signature(voicevox_core.blocking.Onnxruntime)}")

    # Also check top level just in case
    import voicevox_core
    if hasattr(voicevox_core, "Onnxruntime"):
         print(f"voicevox_core.Onnxruntime sig: {inspect.signature(voicevox_core.Onnxruntime)}")

except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
