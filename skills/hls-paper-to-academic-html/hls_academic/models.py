from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


StudyDesign = Literal[
    "experiment",
    "quasi_experiment",
    "observational",
    "experience_sampling",
    "cross_sectional",
    "longitudinal",
    "qualitative",
    "systematic_review",
    "meta_analysis",
    "method",
]


class EvidenceItem(StrictModel):
    id: str = Field(pattern=r"^E\d{3}$")
    category: Literal[
        "research_question",
        "method",
        "sample",
        "main_finding",
        "null_finding",
        "mechanism",
        "moderation",
        "limitation",
        "author_interpretation",
    ]
    claim_zh: str = Field(min_length=1)
    claim_strength: Literal["supported", "mixed", "tentative", "not_supported"]
    study_id: str = Field(min_length=1)
    study_design: StudyDesign
    source_page: int = Field(ge=1)
    source_section: str = Field(min_length=1)
    source_table: str | None
    source_figure: str | None
    original_excerpt: str = Field(min_length=1)
    numbers: dict[str, Any]
    allowed_wording: list[str] = Field(min_length=1)
    forbidden_wording: list[str]
    caveat: str = Field(min_length=1)


class EvidenceMap(StrictModel):
    schema_version: Literal["1.0"]
    paper_id: str = Field(min_length=1)
    paper_page_count: int = Field(ge=1)
    items: list[EvidenceItem]

    @model_validator(mode="after")
    def validate_items(self) -> "EvidenceMap":
        ids = [item.id for item in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate evidence id")
        invalid_pages = [
            item.id for item in self.items if item.source_page > self.paper_page_count
        ]
        if invalid_pages:
            raise ValueError(f"evidence page exceeds paper: {invalid_pages}")
        return self


class SourceAsset(StrictModel):
    id: str = Field(pattern=r"^[AF]\d{3}$")
    kind: Literal["text_crop", "figure"]
    page: int = Field(ge=1)
    clip: tuple[float, float, float, float] | None
    xref: int | None = Field(default=None, ge=1)
    evidence_ids: list[str] = Field(min_length=1)
    output: str = Field(pattern=r"^assets/source/[AF]\d{3}\.png$")
    alt_zh: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_source_selector(self) -> "SourceAsset":
        if self.kind == "text_crop" and self.clip is None:
            raise ValueError("text_crop requires clip")
        if self.kind == "figure" and self.xref is None:
            raise ValueError("figure requires xref")
        return self


class SourceAssetManifest(StrictModel):
    schema_version: Literal["1.0"]
    paper_id: str = Field(min_length=1)
    paper_page_count: int = Field(ge=1)
    assets: list[SourceAsset] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_assets(self) -> "SourceAssetManifest":
        ids = [asset.id for asset in self.assets]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate source asset id")
        invalid_pages = [
            asset.id for asset in self.assets if asset.page > self.paper_page_count
        ]
        if invalid_pages:
            raise ValueError(f"source asset page exceeds paper: {invalid_pages}")
        return self


class AngleOption(StrictModel):
    id: str = Field(pattern=r"^A\d{2}$")
    title: str
    reader_question: str
    thesis: str
    evidence_ids: list[str] = Field(min_length=1)
    evidence_strength: int = Field(ge=1, le=5)
    reader_value: int = Field(ge=1, le=5)
    clarity: int = Field(ge=1, le=5)
    novelty: int = Field(ge=1, le=5)
    visual_potential: int = Field(ge=1, le=5)
    risk_notes: list[str]


class AngleOptions(StrictModel):
    schema_version: Literal["1.0"]
    paper_id: str
    options: list[AngleOption] = Field(min_length=3, max_length=5)
    recommended_id: str


PageType = Literal[
    "cover",
    "paper_identity",
    "abstract_brief",
    "agenda",
    "section",
    "problem",
    "concept",
    "comparison",
    "method",
    "sample",
    "process",
    "finding",
    "metrics",
    "outcome_matrix",
    "chart",
    "moderation",
    "mediation",
    "mechanism",
    "quote",
    "risk",
    "limitations",
    "future",
    "references",
]


class DeckPlanSlide(StrictModel):
    id: str = Field(pattern=r"^S\d{2}$")
    page_type: PageType
    communication_goal: str = Field(min_length=1)
    title: str = Field(min_length=1)
    lead: str
    content_blocks: list[dict[str, Any]]
    visual_plan: dict[str, Any]
    evidence_ids: list[str]
    risk_note: str


class DeckPlan(StrictModel):
    schema_version: Literal["1.0"]
    paper_id: str
    selected_angle_id: str
    slides: list[DeckPlanSlide] = Field(min_length=1)


class VisualSpec(StrictModel):
    component: str = Field(min_length=1)
    data: dict[str, Any]


class DeckSlide(StrictModel):
    id: str = Field(pattern=r"^S\d{2}$")
    page_type: PageType
    title: str = Field(min_length=1)
    lead: str
    content_blocks: list[dict[str, Any]]
    visual: VisualSpec
    evidence_ids: list[str]
    source_label: str
    section: dict | None = None  # optional override of section band text


class Deck(StrictModel):
    schema_version: Literal["1.0"]
    title: str = Field(min_length=1)
    paper_id: str = Field(min_length=1)
    evidence_ids: list[str]
    slides: list[DeckSlide] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_references(self) -> "Deck":
        declared = set(self.evidence_ids)
        used = {evidence_id for slide in self.slides for evidence_id in slide.evidence_ids}
        missing = sorted(used - declared)
        if missing:
            raise ValueError(f"undeclared evidence: {missing}")
        slide_ids = [slide.id for slide in self.slides]
        if len(slide_ids) != len(set(slide_ids)):
            raise ValueError("duplicate slide id")
        return self
