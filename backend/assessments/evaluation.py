from collections import defaultdict


def evaluate_attempt(questions, answers):
    # answers: dict question_id -> selected_option
    total = len(questions)
    correct = 0
    skill_stats = defaultdict(lambda: {"correct": 0, "total": 0})

    for q in questions:
        qid = str(q.get("_id"))
        skill = q.get("skill", "unknown").lower()
        selected = answers.get(qid)
        is_correct = selected == q.get("correct_answer")
        if is_correct:
            correct += 1
        skill_stats[skill]["total"] += 1
        skill_stats[skill]["correct"] += 1 if is_correct else 0

    accuracy = correct / total if total else 0.0
    return {
        "total": total,
        "correct": correct,
        "accuracy": accuracy,
        "skill_stats": skill_stats,
    }
