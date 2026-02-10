from collections import defaultdict
from assessments.question_bank import find_questions
from ml_engine.adaptive_engine import adjust_difficulty


def generate_test(skills_priority, base_difficulty="Medium", total_questions=10):
    # skills_priority: list of skills ordered by importance
    if not skills_priority:
        return []

    per_skill = max(1, total_questions // len(skills_priority))
    questions = []

    for skill in skills_priority:
        qs = find_questions([skill], base_difficulty, limit=per_skill)
        questions.extend(qs)

    # If not enough, fill with any difficulty adjustment
    if len(questions) < total_questions:
        remaining = total_questions - len(questions)
        fallback_diff = adjust_difficulty(0.6, base_difficulty)
        for skill in skills_priority:
            qs = find_questions([skill], fallback_diff, limit=remaining)
            questions.extend(qs)
            if len(questions) >= total_questions:
                break

    return questions[:total_questions]


def build_skill_priority(missing_skills, weak_skills, required_skills):
    priority = []
    for skill in missing_skills:
        if skill not in priority:
            priority.append(skill)
    for skill in weak_skills:
        if skill not in priority:
            priority.append(skill)
    for skill in required_skills:
        if skill not in priority:
            priority.append(skill)
    return priority
