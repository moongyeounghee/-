# -*- coding: utf-8 -*-
import sys
import time

try:
    from pyngrok import ngrok
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyngrok"])
    from pyngrok import ngrok

print("ngrok tunnel starting...")
print("(Streamlit app must be running at localhost:8501)")
print()

ngrok.set_auth_token("3BSehgJJ4Q0vlYGhRQRAvEmv1Dz_3HTgg2GWTXsyTTwMs2e3X")
tunnel = ngrok.connect(8501, "http")
public_url = tunnel.public_url

print("=" * 55)
print("  Public URL ready!")
print("  " + public_url)
print("=" * 55)
print()
print("Share this URL - anyone can access the app.")
print("Free plan: URL changes after ~2 hours.")
print("Access code: AIPORT2026")
print()
print("Press Ctrl+C to stop the tunnel.")
print()

try:
    while True:
        time.sleep(5)
except KeyboardInterrupt:
    print("\nStopping tunnel...")
    ngrok.disconnect(public_url)
    ngrok.kill()
    print("Tunnel closed.")
