from datetime import datetime
from django.urls import path
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
import json
import subprocess
from pathlib import Path
from rest_framework import status
from common.mongodb import get_db
from resumes.upload import read_resume_file
from resumes.parser import parse_resume_text
from ml_engine.skill_extractor import predict_skills
from ml_engine.role_predictor import predict_role
from ml_engine.skill_gap_analyzer import analyze_skill_gap
from analytics.performance_tracker import get_skill_accuracy_summary
from ml_engine.auto_retrainer import check_and_retrain, get_training_status
import threading


def _merge_manual_keywords(_user_id, extracted):
    # Disabled: only show skills actually present in the resume text.
    return extracted


class ResumeUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        file_obj = request.FILES.get("file")
        if not file_obj:
            return Response({"error": "file is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            raw_text, ext = read_resume_file(file_obj, file_obj.name)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        parsed = parse_resume_text(raw_text)
        try:
            skills = predict_skills(parsed["cleaned_text"])
        except FileNotFoundError:
            return Response({"error": "skill extractor model not found. Train it with ml_engine/train_skill_extractor.py"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        skills = _merge_manual_keywords(request.user.id, skills)

        db = get_db()
        resume_doc = {
            "user_id": request.user.id,
            "filename": file_obj.name,
            "extension": ext,
            "raw_text": parsed["raw_text"],
            "cleaned_text": parsed["cleaned_text"],
            "keywords": parsed["keywords"],
            "created_at": datetime.utcnow(),
        }
        resume_id = db["resumes"].insert_one(resume_doc).inserted_id

        skill_doc = {
            "user_id": request.user.id,
            "resume_id": str(resume_id),
            "skills": [{"skill": s, "score": score} for s, score in skills],
            "created_at": datetime.utcnow(),
        }
        db["skill_extractions"].insert_one(skill_doc)

        target_role = request.data.get("selected_role")
        gap = None
        if target_role:
            performance = get_skill_accuracy_summary(request.user.id)
            gap = analyze_skill_gap([s["skill"] for s in skill_doc["skills"]], target_role, performance=performance)
            # Signal: Save as role training data
            db["role_training"].insert_one({
                "skills": [s["skill"] for s in skill_doc["skills"]],
                "role": target_role,
                "source": "user_resume_upload",
                "user_id": request.user.id,
                "is_new": True
            })
            
        # Trigger background auto-retrain check
        threading.Thread(target=check_and_retrain, kwargs={"threshold": 10}, daemon=True).start()

        # Added: Predict role based on extracted skills and find matched skills
        prediction = None
        try:
            role, confidence = predict_role([s["skill"] for s in skill_doc["skills"]])
            role_gap = analyze_skill_gap([s["skill"] for s in skill_doc["skills"]], role)
            prediction = {
                "role": role, 
                "confidence": confidence,
                "matched_skills": role_gap["matched_skills"]
            }
        except Exception:
            pass

        return Response({
            "resume_id": str(resume_id),
            "skills": skill_doc["skills"],
            "keywords": parsed["keywords"],
            "education": parsed.get("education"),
            "contact": parsed.get("contact"),
            "gap": gap,
            "prediction": prediction,
        })


class RolePredictionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        skills = request.data.get("skills")
        resume_id = request.data.get("resume_id")
        if not skills and not resume_id:
            return Response({"error": "skills or resume_id required"}, status=status.HTTP_400_BAD_REQUEST)

        db = get_db()
        if resume_id and not skills:
            doc = db["skill_extractions"].find_one({"resume_id": resume_id, "user_id": request.user.id})
            if not doc:
                return Response({"error": "skills not found for resume_id"}, status=status.HTTP_404_NOT_FOUND)
            skills = [s["skill"] for s in doc.get("skills", [])]

        try:
            role, confidence = predict_role(skills)
            role_gap = analyze_skill_gap(skills, role)
            matched_skills = role_gap["matched_skills"]
        except FileNotFoundError:
            return Response({"error": "role predictor model not found. Train it with ml_engine/role_predictor.py"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        pred_doc = {
            "user_id": request.user.id,
            "skills": skills,
            "predicted_role": role,
            "confidence": confidence,
            "matched_skills": matched_skills,
            "created_at": datetime.utcnow(),
        }
        db["role_predictions"].insert_one(pred_doc)
        pred_doc["_id"] = str(pred_doc["_id"])

        return Response(pred_doc)


class SkillGapView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        skills = request.data.get("skills")
        target_role = request.data.get("target_role")
        resume_id = request.data.get("resume_id")

        if not target_role:
            return Response({"error": "target_role is required"}, status=status.HTTP_400_BAD_REQUEST)

        db = get_db()
        if resume_id and not skills:
            doc = db["skill_extractions"].find_one({"resume_id": resume_id, "user_id": request.user.id})
            if not doc:
                return Response({"error": "skills not found for resume_id"}, status=status.HTTP_404_NOT_FOUND)
            skills = [s["skill"] for s in doc.get("skills", [])]

        if not skills:
            return Response({"error": "skills or resume_id required"}, status=status.HTTP_400_BAD_REQUEST)

        performance = get_skill_accuracy_summary(request.user.id)
        gap = analyze_skill_gap(skills, target_role, performance=performance)

        # Signal: Save as role training data
        db["role_training"].insert_one({
            "skills": skills,
            "role": target_role,
            "source": "user_skill_gap_analysis",
            "user_id": request.user.id,
            "is_new": True
        })

        return Response(gap)


class ManualSkillsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        skills = request.data.get("skills", [])
        if not isinstance(skills, list) or not skills:
            return Response({"error": "skills list is required"}, status=status.HTTP_400_BAD_REQUEST)
        normalized = sorted({str(s).strip().lower() for s in skills if str(s).strip()})
        if not normalized:
            return Response({"error": "skills list is empty"}, status=status.HTTP_400_BAD_REQUEST)

        db = get_db()
        db["user_keywords"].update_one(
            {"user_id": request.user.id},
            {"$set": {"keywords": normalized}},
            upsert=True,
        )
        # Add to training data so future models learn from manual skill signals
        db["skill_training"].insert_one(
            {
                "text": "manual skills: " + " ".join(normalized),
                "skills": normalized,
                "source": "manual_skills",
            }
        )
        return Response({"keywords": normalized})


class ManualResumeTextView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        text = request.data.get("text", "")
        if not text or not str(text).strip():
            return Response({"error": "text is required"}, status=status.HTTP_400_BAD_REQUEST)

        parsed = parse_resume_text(str(text))
        try:
            skills = predict_skills(parsed["cleaned_text"])
        except FileNotFoundError:
            return Response({"error": "skill extractor model not found. Train it with ml_engine/train_skill_extractor.py"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        skills = _merge_manual_keywords(request.user.id, skills)

        db = get_db()
        resume_doc = {
            "user_id": request.user.id,
            "filename": "manual_input",
            "extension": ".txt",
            "raw_text": parsed["raw_text"],
            "cleaned_text": parsed["cleaned_text"],
            "keywords": parsed["keywords"],
            "created_at": datetime.utcnow(),
        }
        resume_id = db["resumes"].insert_one(resume_doc).inserted_id

        skill_doc = {
            "user_id": request.user.id,
            "resume_id": str(resume_id),
            "skills": [{"skill": s, "score": score} for s, score in skills],
            "created_at": datetime.utcnow(),
        }
        db["skill_extractions"].insert_one(skill_doc)

        target_role = request.data.get("selected_role")
        gap = None
        if target_role:
            performance = get_skill_accuracy_summary(request.user.id)
            gap = analyze_skill_gap([s["skill"] for s in skill_doc["skills"]], target_role, performance=performance)
            # Signal: Save as role training data
            db["role_training"].insert_one({
                "skills": [s["skill"] for s in skill_doc["skills"]],
                "role": target_role,
                "source": "user_manual_text",
                "user_id": request.user.id,
                "is_new": True
            })

        # Added: Predict role based on extracted skills and find matched skills
        prediction = None
        try:
            role, confidence = predict_role([s["skill"] for s in skill_doc["skills"]])
            role_gap = analyze_skill_gap([s["skill"] for s in skill_doc["skills"]], role)
            prediction = {
                "role": role, 
                "confidence": confidence,
                "matched_skills": role_gap["matched_skills"]
            }
        except Exception:
            pass

        return Response({
            "resume_id": str(resume_id),
            "skills": skill_doc["skills"],
            "keywords": parsed["keywords"],
            "education": parsed.get("education"),
            "contact": parsed.get("contact"),
            "gap": gap,
            "prediction": prediction,
        })


class LastExtractionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        db = get_db()
        doc = db["skill_extractions"].find_one(
            {"user_id": request.user.id},
            sort=[("created_at", -1)]
        )
        if not doc:
            return Response({"error": "no previous extraction found"}, status=status.HTTP_404_NOT_FOUND)
        
        skills = [s["skill"] for s in doc.get("skills", [])]
        prediction = None
        try:
            role, confidence = predict_role(skills)
            role_gap = analyze_skill_gap(skills, role)
            prediction = {
                "role": role, 
                "confidence": confidence,
                "matched_skills": role_gap["matched_skills"]
            }
        except Exception:
            pass

        return Response({
            "resume_id": doc["resume_id"],
            "skills": skills,
            "prediction": prediction,
            "created_at": doc["created_at"]
        })


class TrainingStatusView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        status = get_training_status()
        return Response(status)


class AddManualTrainingDataView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        data_type = request.data.get("type") # "skill" or "role"
        db = get_db()
        
        if data_type == "skill":
            text = request.data.get("text")
            skills = request.data.get("skills")
            if not text or not isinstance(skills, list):
                return Response({"error": "text and skills list required"}, status=status.HTTP_400_BAD_REQUEST)
            
            db["skill_training"].insert_one({
                "text": text,
                "skills": [s.strip().lower() for s in skills if s.strip()],
                "source": "admin_manual_entry",
                "is_new": True,
                "created_at": datetime.utcnow()
            })
            return Response({"status": "skill training data added"})
            
        elif data_type == "role":
            skills = request.data.get("skills")
            role = request.data.get("role")
            if not role or not isinstance(skills, list):
                return Response({"error": "role and skills list required"}, status=status.HTTP_400_BAD_REQUEST)
            
            db["role_training"].insert_one({
                "skills": [s.strip().lower() for s in skills if s.strip()],
                "role": role,
                "source": "admin_manual_entry",
                "is_new": True,
                "created_at": datetime.utcnow()
            })
            return Response({"status": "role training data added"})
            
        elif data_type == "alignment":
            role = request.data.get("role")
            skills = request.data.get("skills")
            if not role or not isinstance(skills, list):
                return Response({"error": "role and skills list required"}, status=status.HTTP_400_BAD_REQUEST)
            
            db["role_skills"].update_one(
                {"role": role},
                {"$set": {"skills": [s.strip().lower() for s in skills if s.strip()], "updated_at": datetime.utcnow()}},
                upsert=True
            )
            return Response({"status": "role alignment updated"})
            
        elif data_type == "dependency":
            skill = request.data.get("skill")
            prereqs = request.data.get("prerequisites")
            if not skill or not isinstance(prereqs, list):
                return Response({"error": "skill and prerequisites list required"}, status=status.HTTP_400_BAD_REQUEST)
            
            db["skill_dependencies"].update_one(
                {"skill": skill.strip().lower()},
                {"$set": {
                    "prerequisite": [s.strip().lower() for s in prereqs if s.strip()],
                    "updated_at": datetime.utcnow()
                }},
                upsert=True
            )
            return Response({"status": "skill dependency updated"})
            
        return Response({"error": "invalid data type"}, status=status.HTTP_400_BAD_REQUEST)


class EngineConfigView(APIView):
    permission_classes = [IsAdminUser]
    
    def get_path(self):
        return Path(__file__).resolve().parent.parent / "ml_engine" / "datasets" / "engine_config.json"

    def get(self, request):
        path = self.get_path()
        try:
            with open(path, "r") as f:
                data = json.load(f)
            return Response(data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        path = self.get_path()
        try:
            with open(path, "w") as f:
                json.dump(request.data, f, indent=4)
            return Response({"status": "config updated"})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RunSystemTestsView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        backend_dir = Path(__file__).resolve().parent.parent
        try:
            # Run the ml_engine/tests.py using the current python interpreter
            result = subprocess.run(
                [sys.executable, "-m", "unittest", "ml_engine/tests.py"],
                cwd=backend_dir,
                capture_output=True,
                text=True
            )
            return Response({
                "status": "success" if result.returncode == 0 else "failed",
                "output": result.stdout + result.stderr,
                "returncode": result.returncode
            })
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminRetrainView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        success = check_and_retrain(threshold=1)
        if success:
            return Response({"status": "retraining triggered and completed"})
        return Response({"status": "no retraining needed or error occurred"}, status=status.HTTP_200_OK)


urlpatterns = [
    path("upload/", ResumeUploadView.as_view(), name="resume-upload"),
    path("predict-role/", RolePredictionView.as_view(), name="role-predict"),
    path("skill-gap/", SkillGapView.as_view(), name="skill-gap"),
    path("manual-skills/", ManualSkillsView.as_view(), name="manual-skills"),
    path("manual-text/", ManualResumeTextView.as_view(), name="manual-text"),
    path("latest-extraction/", LastExtractionView.as_view(), name="latest-extraction"),
    path("training-status/", TrainingStatusView.as_view(), name="training-status"),
    path("add-manual-data/", AddManualTrainingDataView.as_view(), name="add-manual-data"),
    path("engine-config/", EngineConfigView.as_view(), name="engine-config"),
    path("run-tests/", RunSystemTestsView.as_view(), name="run-tests"),
    path("admin-retrain/", AdminRetrainView.as_view(), name="admin-retrain"),
]
