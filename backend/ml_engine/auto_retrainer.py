import time
from common.mongodb import get_db
from ml_engine.train_skill_extractor import train as train_skills
from ml_engine.role_predictor import train_role_model as train_roles

def check_and_retrain(threshold=5):
    """
    Checks if there's enough new training data to justify a retrain.
    """
    db = get_db()
    
    # Check new role signals
    new_role_count = db["role_training"].count_documents({"is_new": True})
    
    # Check new skill signals
    new_skill_count = db["skill_training"].count_documents({"is_new": True})
    
    print(f"Auto-Retrainer: Found {new_role_count} new roles, {new_skill_count} new skills.")
    
    if new_role_count >= threshold or new_skill_count >= threshold:
        print("Threshold met. Starting automatic retraining...")
        
        try:
            if new_skill_count >= threshold:
                train_skills()
            
            if new_role_count >= threshold:
                train_roles()
            
            # Mark as processed
            db["role_training"].update_many({"is_new": True}, {"$set": {"is_new": False}})
            db["skill_training"].update_many({"is_new": True}, {"$set": {"is_new": False}})
            
            print("Automatic retraining completed successfully.")
            return True
        except Exception as e:
            print(f"Error during auto-retraining: {e}")
            return False
            
    return False

def get_training_status():
    """
    Returns the current counts of training data.
    """
    db = get_db()
    
    new_role_count = db["role_training"].count_documents({"is_new": True})
    total_role_count = db["role_training"].count_documents({})
    
    new_skill_count = db["skill_training"].count_documents({"is_new": True})
    total_skill_count = db["skill_training"].count_documents({})
    
    total_alignment_count = db["role_skills"].count_documents({})
    total_dependency_count = db["skill_dependencies"].count_documents({})
    
    return {
        "roles": {
            "new": new_role_count,
            "total": total_role_count
        },
        "skills": {
            "new": new_skill_count,
            "total": total_skill_count
        },
        "alignments": {
            "total": total_alignment_count
        },
        "dependencies": {
            "total": total_dependency_count
        }
    }


if __name__ == "__main__":
    status = get_training_status()
    print(f"Current Training Status: {status}")
    check_and_retrain(threshold=1) # Run once for testing
