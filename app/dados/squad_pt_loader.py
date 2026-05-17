from datasets import load_dataset

from app.dados.squad_pt_models import SquadPTQuestion


def load_squad_pt(split: str = "train"):
    return load_dataset(
        "pierreguillou/squad-pt",
        split=split,
    )


def get_questions(limit: int = 100, split: str = "train") -> list[SquadPTQuestion]:
    dataset = load_squad_pt(split=split)
    n = min(limit, len(dataset))

    questions: list[SquadPTQuestion] = []

    for item in dataset.select(range(n)):
        expected_answer = ""

        if item["answers"]["text"]:
            expected_answer = item["answers"]["text"][0]

        questions.append(
            SquadPTQuestion(
                context=item["context"],
                question=item["question"],
                expected_answer=expected_answer,
            )
        )

    return questions
