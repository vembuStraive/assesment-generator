from dataclasses import dataclass, field


@dataclass
class Choice:
    letter: str   # 'A', 'B', 'C', 'D'
    text: str


@dataclass
class Question:
    number: int
    stem: str
    q_type: str           # 'multichoice' | 'truefalse' | 'essay'
    choices: list = field(default_factory=list)   # list[Choice]
    correct_letter: str = ''  # MC: 'A'–'D'; TF: 'TRUE' | 'FALSE'; essay: ''
    model_answer: str = ''    # essay / SA model answer text


@dataclass
class Chapter:
    title: str            # e.g. "Chapter 01 Professional Communication..."
    number: int
    questions: list = field(default_factory=list)  # list[Question]
