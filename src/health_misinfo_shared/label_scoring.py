CATEGORY_WEIGHTS = {
    "understandability": 15,
    "type_of_claim": 10,
    "type_of_medical_claim": 5,
    "support": 7,
    "harm": 10,
}
LABEL_SCORES = {
    "understandability": {"understandable": 1, "vague": -3, "not understandable": -10},
    "type_of_claim": {
        "opinion": -2,
        "personal": -3,
        "citation": 5,
        "hedged claim": -3,
        "statement of fact": 3,
        "advice/recommendation": 3,
        "promotion": -10,
        "not a claim": -10,
    },
    "type_of_medical_claim": {
        "symptom": 5,
        "cause/effect": 5,
        "correlation": 3,
        "prevention": 5,
        "treatment/cure": 5,
        "outcome": 3,
        "statistics": 3,
        "not medical": -10,
    },
    "support": {
        "uncontroversial statement": -5,
        "disputed claim": 7,
        "widely discredited": 10,
        "novel claim": 7,
        "can't tell": 0,
    },
    "harm": {
        "high harm": 15,
        "some harm": 10,
        "low harm": 5,
        "indirect harm": 5,
        "harmless": -10,
        "can't tell": 0,
    },
}
SUMMARY_THRESHOLDS = {
    k: v
    for k, v in sorted(
        {
            "worth checking": 200,
            "may be worth checking": 100,
            "not worth checking": float("-inf"),
        }.items(),
        key=lambda item: item[1],
        reverse=True,
    )
}


def calculate_claim_summary_score(labels: dict[str, str]) -> str:
    total_score = 0
    for category, scores in LABEL_SCORES.items():
        label = labels.get(category)
        score = scores.get(label, 0)
        weight = CATEGORY_WEIGHTS.get(category, 0)
        total_score += score * weight
    return total_score


def decide_claim_summary_label(score: int) -> str:
    for summary, threshold in SUMMARY_THRESHOLDS.items():
        if score > threshold:
            claim_summary = summary
            return claim_summary


def get_claim_summary(labels: dict[str, str]) -> dict[str, dict[str, str]]:
    total_claim_score = calculate_claim_summary_score(labels)
    return decide_claim_summary_label(total_claim_score)
