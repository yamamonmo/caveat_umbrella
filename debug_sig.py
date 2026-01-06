
try:
    from voicevox_core.blocking import Synthesizer
    import inspect
    print(f"Synthesizer signature: {inspect.signature(Synthesizer)}")
    print(f"Synthesizer doc: {Synthesizer.__doc__}")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
