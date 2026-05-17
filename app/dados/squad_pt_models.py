from dataclasses import dataclass


@dataclass
class SquadPTQuestion:
    context: str
    question: str
    expected_answer: str
