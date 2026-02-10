import sys
import os
sys.path.append(os.getcwd())

from ml_engine.skill_extractor import predict_skills

test_text = "I am a developer with experience in java and aws cloud. I also know python."
print(f"Testing text: {test_text}")

try:
    skills = predict_skills(test_text)
    print("\nExtracted Skills:")
    for skill, score in skills:
        print(f"- {skill}: {score:.2f}")
    
    if not skills:
        print("No skills extracted.")
except Exception as e:
    print(f"Error: {e}")
