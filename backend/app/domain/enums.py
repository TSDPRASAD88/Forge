from enum import StrEnum


class ExamType(StrEnum):
    GATE_CSE = "gate_cse"
    SSC_CGL = "ssc_cgl"


class Topic(StrEnum):
    PERCENTAGES = "percentages"
    RATIOS = "ratios"
    PROFIT_LOSS = "profit_loss"
    # more topics later: RATIOS, PROFIT_LOSS, TIME_WORK, ...


class Difficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"