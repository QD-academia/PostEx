from enum import Enum


class StrEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class ResearchType(StrEnum):
    BIOINFORMATICS = "bioinformatics"
    OBSERVATIONAL = "observational"


class ContentMode(StrEnum):
    VERBATIM = "verbatim"
    TRACEABLE = "traceable"
    EDITORIAL = "editorial"


class Language(StrEnum):
    ENGLISH = "en"
    CHINESE_SIMPLIFIED = "zh-CN"


class PosterSize(StrEnum):
    A0_LANDSCAPE = "a0-landscape"
    A1_LANDSCAPE = "a1-landscape"
    INCH_36X48_LANDSCAPE = "36x48-landscape"


class ApprovalSubject(StrEnum):
    CLOUD_UPLOAD = "cloud_upload"
    CONTENT_DELETION = "content_deletion"
    PALETTE_APPLICATION = "palette_application"
    SCIENTIFIC_COLOR_UNLOCK = "scientific_color_unlock"
    HERO_RESULT = "hero_result"
    FIGURE_EDIT = "figure_edit"
    POSTER_STRUCTURE = "poster_structure"
    FINAL_RELEASE = "final_release"


class ApprovalDecision(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVOKED = "revoked"


class WorkflowStage(StrEnum):
    LOCAL_READY = "local_ready"
    AWAITING_UPLOAD_APPROVAL = "awaiting_upload_approval"
    CLOUD_READY = "cloud_ready"
    AWAITING_DELETION_APPROVAL = "awaiting_deletion_approval"
    AWAITING_PALETTE_APPROVAL = "awaiting_palette_approval"
    READY_TO_RENDER = "ready_to_render"
    RENDERED = "rendered"
    PREFLIGHT_PASSED = "preflight_passed"
    BRIEF_READY = "brief_ready"
    AWAITING_HERO_APPROVAL = "awaiting_hero_approval"
    AWAITING_FIGURE_APPROVAL = "awaiting_figure_approval"
    AWAITING_STRUCTURE_APPROVAL = "awaiting_structure_approval"


class PosterEmphasis(StrEnum):
    BALANCED = "balanced"
    METHODS = "methods"
    RESULTS = "results"
    IMPACT = "impact"


class StructureDirection(StrEnum):
    HERO_RESULT = "hero-result"
    VISUAL_JOURNEY = "visual-journey"
    EDITORIAL_STORY = "editorial-story"


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
