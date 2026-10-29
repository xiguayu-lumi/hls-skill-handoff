from dataclasses import asdict, dataclass
from typing import Literal


@dataclass(frozen=True)
class ValidationIssue:
    severity: Literal["error", "warning"]
    code: str
    message: str
    item_id: str | None = None
    location: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return asdict(self)
