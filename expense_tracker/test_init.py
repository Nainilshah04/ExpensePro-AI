import sys
print("Step 1: Starting test...", flush=True)

try:
    from services.ai_service import ai_engine
    print("Step 2: AI Engine imported successfully!", flush=True)
    res = ai_engine.predict_category("Swiggy cheese pizza")
    print(f"Step 3: Sample prediction: {res}", flush=True)
    import models
    print("Step 4: models imported successfully!", flush=True)
    import app
    print("Step 5: Flask app imported and initialized successfully!", flush=True)
    print("SUCCESS: ALL COMPONENTS OPERATIONAL!", flush=True)
except Exception as e:
    import traceback
    traceback.print_exc()
