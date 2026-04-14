def calculate_score(correct, time_taken, combo, difficulty="medium"):
    multiplier = {
        "easy": 1,
        "medium": 2,
        "hard": 3
    }.get(difficulty, 2)

    if correct:
        base = (10 + max(0, int(8 - time_taken)))
        return base * combo * multiplier
    return -5