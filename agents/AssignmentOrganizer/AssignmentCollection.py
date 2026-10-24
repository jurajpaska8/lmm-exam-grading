from dataclasses import dataclass, field

@dataclass
class AssignmentCollection:
    student_name: str
    student_idx: int
    files_pages: list[tuple[str, int]] = field(default_factory=list)