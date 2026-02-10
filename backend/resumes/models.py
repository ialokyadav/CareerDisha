from django.db import models

class MongoResume(models.Model):
    """Placeholder for MongoDB 'resumes' collection"""
    class Meta:
        verbose_name = "Mongo Resume"
        verbose_name_plural = "Mongo Resumes"
        managed = True # Create slim tables to avoid Admin errors

class MongoExtraction(models.Model):
    """Placeholder for MongoDB 'skill_extractions' collection"""
    class Meta:
        verbose_name = "Mongo Skill Extraction"
        verbose_name_plural = "Mongo Skill Extractions"
        managed = True

class MongoPrediction(models.Model):
    """Placeholder for MongoDB 'role_predictions' collection"""
    class Meta:
        verbose_name = "Mongo Role Prediction"
        verbose_name_plural = "Mongo Role Predictions"
        managed = True
