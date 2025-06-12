def compute_reliability_score(score: int, num_comments: int) -> float:
    return round(min(1.0, (score / 100) * 0.6 + (num_comments / 50) * 0.4), 2)
