import sys
import os
sys.path.append(os.getcwd())

from ml_engine.role_predictor import predict_role

test_skills = ["aws", "java", "python", "c", "structures", "data structures", "dsa"]
print(f"Testing skills: {test_skills}")

try:
    role, confidence = predict_role(test_skills)
    print(f"\nPredicted Role: {role}")
    print(f"Confidence: {confidence:.2f}")
except FileNotFoundError as e:
    print(f"\nError: Model files not found. {e}")
except Exception as e:
    print(f"\nError: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
