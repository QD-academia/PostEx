from dataclasses import dataclass

from postex.enums import ResearchType


@dataclass(frozen=True)
class ResearchProfile:
    research_type: ResearchType
    required_sections: tuple[str, ...]
    preferred_visuals: tuple[str, ...]


PROFILES = {
    ResearchType.BIOINFORMATICS: ResearchProfile(
        ResearchType.BIOINFORMATICS,
        (
            "research_question",
            "datasets",
            "analysis_pipeline",
            "key_results",
            "external_validation",
            "conclusion",
        ),
        ("pipeline", "heatmap", "volcano_plot", "forest_plot", "performance_plot"),
    ),
    ResearchType.OBSERVATIONAL: ResearchProfile(
        ResearchType.OBSERVATIONAL,
        (
            "background",
            "cohort_construction",
            "baseline_characteristics",
            "statistical_model",
            "primary_outcome",
            "sensitivity_analysis",
            "limitations",
        ),
        ("cohort_flow", "table_one", "forest_plot", "subgroup_plot"),
    ),
}
