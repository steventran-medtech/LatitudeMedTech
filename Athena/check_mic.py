import sys
sys.path.insert(0, "voice")
import voice_bridge
import sounddevice as sd

print("Selected device:", voice_bridge.DEVICE_NAME)
print("Device index:   ", voice_bridge.INPUT_DEVICE)
print("Device rate:    ", voice_bridge.DEVICE_RATE, "Hz")
print()
print("Input device scores (higher = preferred):")
for i, d in enumerate(sd.query_devices()):
    if d["max_input_channels"] > 0:
        score = voice_bridge._score_mic(d["name"])
        marker = " <-- SELECTED" if i == voice_bridge.INPUT_DEVICE else ""
        print(f"  [{i:2d}] score={score:4d}  {d['name'][:50]}{marker}")
