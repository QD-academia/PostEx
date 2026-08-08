#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import yaml
from reportlab.graphics import renderPDF
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from svglib.svglib import svg2rlg

NAVY = colors.HexColor("#102A43")
TEAL = colors.HexColor("#0F5F73")
CYAN = colors.HexColor("#2C8C99")
AMBER = colors.HexColor("#E8B44C")
CANVAS = colors.HexColor("#F7FAFC")
MUTED = colors.HexColor("#486581")
LINE = colors.HexColor("#D9E2EC")


def load_yaml(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Manuscript YAML must contain an object")
    return value


def styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "PaperTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=26,
            leading=31,
            textColor=NAVY,
            alignment=TA_LEFT,
            spaceAfter=10,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=14,
            textColor=TEAL,
            spaceAfter=7,
        ),
        "author": ParagraphStyle(
            "Author",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=15,
            textColor=NAVY,
        ),
        "affiliation": ParagraphStyle(
            "Affiliation",
            parent=base["Normal"],
            fontSize=9.5,
            leading=13,
            textColor=MUTED,
            spaceAfter=12,
        ),
        "h1": ParagraphStyle(
            "Heading1",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=TEAL,
            spaceBefore=8,
            spaceAfter=7,
        ),
        "h2": ParagraphStyle(
            "Heading2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=NAVY,
            spaceBefore=6,
            spaceAfter=3,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.4,
            leading=13.1,
            textColor=NAVY,
            alignment=TA_LEFT,
            spaceAfter=7,
        ),
        "small": ParagraphStyle(
            "Small",
            parent=base["BodyText"],
            fontSize=8.1,
            leading=11,
            textColor=MUTED,
        ),
        "caption": ParagraphStyle(
            "Caption",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8.2,
            leading=11,
            textColor=NAVY,
            spaceBefore=4,
            spaceAfter=8,
        ),
        "metric": ParagraphStyle(
            "Metric",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=17,
            alignment=TA_CENTER,
            textColor=TEAL,
        ),
        "metric_label": ParagraphStyle(
            "MetricLabel",
            parent=base["Normal"],
            fontSize=7.5,
            leading=9,
            alignment=TA_CENTER,
            textColor=MUTED,
        ),
        "disclaimer": ParagraphStyle(
            "Disclaimer",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=9.3,
            leading=13,
            textColor=NAVY,
        ),
    }


def figure_flowable(path: Path, caption: str, style: ParagraphStyle, max_width: float):
    drawing = svg2rlg(str(path))
    if drawing is None:
        raise RuntimeError(f"Unable to read SVG: {path}")
    scale = max_width / float(drawing.width)
    drawing.width *= scale
    drawing.height *= scale
    drawing.scale(scale, scale)
    return KeepTogether([renderPDF.GraphicsFlowable(drawing), Paragraph(caption, style)])


def footer(canvas, doc, running_title: str, paper_id: str) -> None:
    canvas.saveState()
    width, _ = A4
    canvas.setStrokeColor(LINE)
    canvas.line(20 * mm, 15 * mm, width - 20 * mm, 15 * mm)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(20 * mm, 10.4 * mm, f"{running_title} | {paper_id} | fully synthetic")
    canvas.drawRightString(width - 20 * mm, 10.4 * mm, f"Page {doc.page}")
    canvas.restoreState()


def build(source: Path, output: Path) -> None:
    data = load_yaml(source)
    sheet = styles()
    output.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=19 * mm,
        bottomMargin=20 * mm,
        title=str(data["title"]),
        author=str(data["authors"]),
        subject="Fully synthetic PostEx evaluation manuscript",
    )
    story = []

    badge = Table(
        [[Paragraph("FULLY SYNTHETIC - NOT A REAL STUDY", sheet["subtitle"])]],
        colWidths=[170 * mm],
    )
    badge.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), AMBER),
                ("BOX", (0, 0), (-1, -1), 0.8, NAVY),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.extend(
        [
            badge,
            Spacer(1, 10),
            Paragraph(str(data["title"]), sheet["title"]),
            Paragraph(str(data["status"]), sheet["subtitle"]),
            Paragraph(str(data["authors"]), sheet["author"]),
            Paragraph(str(data["affiliation"]), sheet["affiliation"]),
        ]
    )

    disclaimer = Table(
        [[Paragraph(f"<b>Rights-safe fixture.</b> {data['disclaimer']}", sheet["disclaimer"])]],
        colWidths=[170 * mm],
    )
    disclaimer.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), CANVAS),
                ("BOX", (0, 0), (-1, -1), 1, TEAL),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ]
        )
    )
    story.extend([disclaimer, Spacer(1, 12), Paragraph("Abstract", sheet["h1"])])
    for label in ("background", "methods", "results", "conclusion"):
        story.extend(
            [
                Paragraph(label.title(), sheet["h2"]),
                Paragraph(str(data["abstract"][label]), sheet["body"]),
            ]
        )
    story.append(
        Paragraph("Keywords: " + ", ".join(data["keywords"]), sheet["small"])
    )
    story.append(Spacer(1, 11))

    metric_cells = [
        [
            Paragraph("1,240", sheet["metric"]),
            Paragraph("480 to 12", sheet["metric"]),
            Paragraph("0.74-0.78", sheet["metric"]),
            Paragraph("92%", sheet["metric"]),
        ],
        [
            Paragraph("synthetic profiles", sheet["metric_label"]),
            Paragraph("anonymous features", sheet["metric_label"]),
            Paragraph("authored C-index", sheet["metric_label"]),
            Paragraph("sign stability", sheet["metric_label"]),
        ],
    ]
    metric_table = Table(metric_cells, colWidths=[42.5 * mm] * 4)
    metric_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.8, LINE),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, LINE),
                ("TOPPADDING", (0, 0), (-1, 0), 8),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
            ]
        )
    )
    story.extend([metric_table, PageBreak()])

    sections = {item["heading"]: item for item in data["sections"]}
    for heading in ("1. Introduction", "2. Methods"):
        story.append(Paragraph(heading, sheet["h1"]))
        for paragraph in sections[heading]["paragraphs"]:
            story.append(Paragraph(str(paragraph), sheet["body"]))
    fig1 = data["figures"][0]
    story.extend(
        [
            Spacer(1, 7),
            figure_flowable(source.parent / fig1["path"], fig1["caption"], sheet["caption"], 170 * mm),
            PageBreak(),
        ]
    )

    story.append(Paragraph("3. Results", sheet["h1"]))
    story.append(Paragraph(sections["3. Results"]["paragraphs"][0], sheet["body"]))
    rows = [["Cohort", "n", "AURORA-12", "Baseline", "Slope", "Abs. error"]]
    rows.extend(data["cohorts"])
    cohort_table = Table(rows, colWidths=[45 * mm, 17 * mm, 27 * mm, 24 * mm, 23 * mm, 25 * mm])
    cohort_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, LINE),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.extend([cohort_table, Spacer(1, 11)])
    fig2 = data["figures"][1]
    story.extend(
        [
            figure_flowable(source.parent / fig2["path"], fig2["caption"], sheet["caption"], 170 * mm),
            PageBreak(),
        ]
    )

    for paragraph in sections["3. Results"]["paragraphs"][1:]:
        story.append(Paragraph(str(paragraph), sheet["body"]))
    fig3 = data["figures"][2]
    story.extend(
        [
            figure_flowable(source.parent / fig3["path"], fig3["caption"], sheet["caption"], 170 * mm),
        ]
    )

    fig4 = data["figures"][3]
    story.extend(
        [
            figure_flowable(source.parent / fig4["path"], fig4["caption"], sheet["caption"], 150 * mm),
            PageBreak(),
            Paragraph("4. Discussion", sheet["h1"]),
        ]
    )
    for paragraph in sections["4. Discussion"]["paragraphs"]:
        story.append(Paragraph(str(paragraph), sheet["body"]))
    story.append(Paragraph("5. Conclusion", sheet["h1"]))
    for paragraph in sections["5. Conclusion"]["paragraphs"]:
        story.append(Paragraph(str(paragraph), sheet["body"]))
    story.append(Paragraph("Declarations and reproducibility", sheet["h1"]))
    statement_labels = {
        "ethics": "Ethics statement",
        "data_availability": "Data availability",
        "code_availability": "Code availability",
        "competing_interests": "Competing interests",
        "acknowledgements": "Acknowledgements",
    }
    for key, label in statement_labels.items():
        story.extend(
            [
                Paragraph(label, sheet["h2"]),
                Paragraph(str(data["statements"][key]), sheet["body"]),
            ]
        )
    story.extend(
        [
            Paragraph("References", sheet["h1"]),
            Paragraph(str(data["references_note"]), sheet["body"]),
            Spacer(1, 10),
        ]
    )
    license_box = Table(
        [[Paragraph(f"Fixture license: {data['license']} | Paper ID: {data['paper_id']}", sheet["disclaimer"])]],
        colWidths=[170 * mm],
    )
    license_box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), CANVAS),
                ("BOX", (0, 0), (-1, -1), 1, TEAL),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    story.append(license_box)

    on_page = lambda canvas, document: footer(  # noqa: E731
        canvas, document, str(data["running_title"]), str(data["paper_id"])
    )
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    build(args.source.resolve(), args.output.resolve())
    print(args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
