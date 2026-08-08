import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const BASE_WIDTH = 4494;
const BASE_HEIGHT = 3179;

function parseArgs(argv) {
  const values = {};
  for (let index = 2; index < argv.length; index += 2) {
    values[argv[index].replace(/^--/, "")] = argv[index + 1];
  }
  for (const required of ["spec", "output"]) {
    if (!values[required]) throw new Error(`Missing --${required}`);
  }
  return values;
}

async function readBytes(filePath) {
  const buffer = await fs.readFile(filePath);
  return buffer.buffer.slice(buffer.byteOffset, buffer.byteOffset + buffer.byteLength);
}

async function writeBlob(filePath, blob) {
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

function contentType(filePath) {
  const suffix = path.extname(filePath).toLowerCase();
  if (suffix === ".svg") return "image/svg+xml";
  if (suffix === ".jpg" || suffix === ".jpeg") return "image/jpeg";
  return "image/png";
}

function createHelpers(slide, canvas) {
  const sx = canvas.width / BASE_WIDTH;
  const sy = canvas.height / BASE_HEIGHT;
  const scale = Math.min(sx, sy);
  const px = (value) => value * sx;
  const py = (value) => value * sy;
  const pw = (value) => value * sx;
  const ph = (value) => value * sy;
  const font = (value, minimum = 0) => Math.max(value, minimum) * scale;

  function rect(x, y, width, height, fill, name, lineFill = "none", lineWidth = 0, radius = "rounded-xl") {
    return slide.shapes.add({
      geometry: "roundRect",
      name,
      position: { left: px(x), top: py(y), width: pw(width), height: ph(height) },
      fill,
      line: { style: "solid", fill: lineFill, width: lineWidth * scale },
      borderRadius: radius,
    });
  }

  function text(value, x, y, width, height, style, name) {
    const shape = slide.shapes.add({
      geometry: "textbox",
      name,
      position: { left: px(x), top: py(y), width: pw(width), height: ph(height) },
      fill: "none",
      line: { style: "solid", fill: "none", width: 0 },
    });
    shape.text = String(value ?? "");
    shape.text.style = {
      fontFamily: "Arial",
      ...style,
      fontSize: font(style.fontSize ?? 38, style.minimumFontSize ?? 0),
    };
    return shape;
  }

  async function image(filePath, alt, x, y, width, height, name) {
    slide.images.add({
      blob: await readBytes(filePath),
      contentType: contentType(filePath),
      alt,
      fit: "contain",
      name,
      position: { left: px(x), top: py(y), width: pw(width), height: ph(height) },
    });
  }

  return { rect, text, image, px, py, pw, ph, font };
}

function mixHex(left, right, fraction) {
  const parse = (value) => [1, 3, 5].map((index) => Number.parseInt(value.slice(index, index + 2), 16));
  const a = parse(left);
  const b = parse(right);
  return `#${a.map((value, index) => Math.round(value + (b[index] - value) * fraction).toString(16).padStart(2, "0")).join("")}`;
}

function gradientBand(h, stops, x, y, width, height, name) {
  if (!Array.isArray(stops) || stops.length < 2) return;
  const count = 32;
  const segmentCount = stops.length - 1;
  const sliceWidth = width / count + 1;
  for (let index = 0; index < count; index += 1) {
    const position = (index / (count - 1)) * segmentCount;
    const segment = Math.min(segmentCount - 1, Math.floor(position));
    const color = mixHex(stops[segment], stops[segment + 1], position - segment);
    h.rect(x + index * (width / count), y, sliceWidth, height, color, `${name}-${index + 1}`, "none", 0, "rounded-none");
  }
}

function sectionTitle(h, theme, title, x, y, width, name) {
  h.text(
    title,
    x,
    y,
    width,
    58,
    { fontSize: 48, minimumFontSize: 38, bold: true, color: theme.primary },
    `${name}-title`,
  );
  h.rect(x, y + 67, Math.min(width, 330), 10, theme.accent, `${name}-rule`, "none", 0, "rounded-sm");
}

function evidence(h, theme, value, x, y, width, name) {
  h.text(
    value,
    x,
    y,
    width,
    38,
    { fontSize: 25, minimumFontSize: 22, color: theme.secondary, italic: true },
    name,
  );
}

function body(h, theme, value, x, y, width, height, name, size = 38) {
  return h.text(
    value,
    x,
    y,
    width,
    height,
    { fontSize: size, minimumFontSize: 37.4, color: theme.ink },
    name,
  );
}

function metric(h, theme, item, x, y, width, color, name) {
  const value = String(item.value ?? "");
  const valueFontSize = Math.min(68, Math.floor(width / Math.max(value.length * 0.62, 1)));
  h.text(
    value,
    x,
    y,
    width,
    78,
    { fontSize: valueFontSize, minimumFontSize: 45, bold: true, color },
    `${name}-value`,
  );
  h.text(
    item.label,
    x,
    y + 82,
    width,
    88,
    { fontSize: 31, minimumFontSize: 24, bold: true, color: theme.ink },
    `${name}-label`,
  );
}

async function logoSlots(h, theme, branding) {
  const slots = branding.logo_mode === "provided" ? branding.logos ?? [] : branding.placeholders ?? [];
  if (branding.logo_mode === "none" || slots.length === 0) return;
  const visible = slots.slice(0, 3);
  const gap = 20;
  const slotWidth = (980 - gap * (visible.length - 1)) / visible.length;
  for (const [index, slot] of visible.entries()) {
    const x = 3370 + index * (slotWidth + gap);
    h.rect(x, 58, slotWidth, 130, "#FFFFFF", `logo-slot-${slot.id}`, theme.neutral, 2, "rounded-lg");
    if (branding.logo_mode === "provided") {
      await h.image(slot.path, slot.alt_text ?? `${slot.role} logo`, x + 16, 70, slotWidth - 32, 106, `logo-${slot.id}`);
    } else {
      h.text(
        slot.label,
        x + 12,
        96,
        slotWidth - 24,
        52,
        { fontSize: 27, minimumFontSize: 22, bold: true, color: theme.primary, alignment: "center" },
        `logo-placeholder-${slot.id}`,
      );
    }
  }
}

async function figureBlock(h, theme, item, x, y, width, height, name) {
  h.rect(x, y, width, height, "#FFFFFF", `${name}-frame`, theme.neutral, 3, "rounded-xl");
  if (item.path) {
    await h.image(item.path, item.alt, x + 20, y + 20, width - 40, height - 98, `${name}-image`);
  } else {
    h.rect(x + 20, y + 20, width - 40, height - 98, theme.canvas, `${name}-placeholder`, theme.neutral, 2, "rounded-lg");
    h.text(
      item.placeholder ?? "FIGURE PLACEHOLDER",
      x + 60,
      y + height / 2 - 60,
      width - 120,
      90,
      { fontSize: 36, minimumFontSize: 28, bold: true, color: theme.secondary, alignment: "center" },
      `${name}-placeholder-label`,
    );
  }
  h.text(
    item.caption,
    x + 24,
    y + height - 72,
    width - 48,
    42,
    { fontSize: 30, minimumFontSize: 29.4, bold: true, color: theme.ink },
    `${name}-caption`,
  );
  evidence(h, theme, item.source, x + 24, y + height - 39, width - 48, `${name}-source`);
}

async function build(spec, outputPath) {
  const canvas = spec.canvas;
  const theme = spec.theme;
  const content = spec.content;
  const deck = Presentation.create({ slideSize: canvas });
  const slide = deck.slides.add();
  slide.background.fill = theme.canvas;
  const h = createHelpers(slide, canvas);

  h.rect(0, 0, BASE_WIDTH, 520, theme.primary, "header-band", "none", 0, "rounded-none");
  if ((theme.gradient_stops ?? []).length > 1) {
    gradientBand(h, theme.gradient_stops, 0, 0, BASE_WIDTH, 30, "top-cape-gradient");
    gradientBand(h, theme.gradient_stops, 0, 490, BASE_WIDTH, 30, "header-cape-gradient");
  } else {
    h.rect(0, 0, BASE_WIDTH, 30, theme.accent, "top-accent", "none", 0, "rounded-none");
  }
  h.text(content.title, 140, 62, 3120, 230, { fontSize: 98, minimumFontSize: 72, bold: true, color: "#FFFFFF" }, "poster-title");
  h.text(content.authors, 145, 306, 3090, 66, { fontSize: 37, minimumFontSize: 30, bold: true, color: "#FFFFFF" }, "authors");
  h.text(content.affiliations, 145, 382, 3090, 52, { fontSize: 29, minimumFontSize: 24, color: theme.canvas }, "affiliations");
  h.text(content.citation, 145, 445, 2550, 42, { fontSize: 26, minimumFontSize: 22, bold: true, color: theme.accent }, "citation");
  await logoSlots(h, theme, spec.branding ?? { logo_mode: "none" });

  h.rect(3370, 210, 980, 240, theme.panel, "header-summary", "none", 0, "rounded-2xl");
  const headerMetrics = content.header_metrics.slice(0, 3);
  const metricColors = [theme.primary, theme.secondary, theme.accent];
  for (const [index, item] of headerMetrics.entries()) {
    metric(h, theme, item, 3440 + index * 300, 240, 260, metricColors[index], `header-metric-${index + 1}`);
  }

  const x1 = 140;
  const w1 = 1220;
  sectionTitle(h, theme, content.question_heading, x1, 590, w1, "question");
  body(h, theme, content.question, x1, 682, w1, 235, "research-question");
  evidence(h, theme, content.question_evidence, x1, 912, w1, "question-evidence");
  sectionTitle(h, theme, content.pipeline_heading, x1, 970, w1, "pipeline");
  for (const [index, step] of content.pipeline_steps.slice(0, 4).entries()) {
    const y = 1064 + index * 80;
    h.rect(x1, y, 62, 62, theme.accent, `pipeline-${index + 1}-number-bg`, "none", 0, "rounded-lg");
    h.text(index + 1, x1, y + 7, 62, 46, { fontSize: 31, minimumFontSize: 24, bold: true, color: theme.ink, alignment: "center" }, `pipeline-${index + 1}-number`);
    h.text(step, x1 + 82, y + 4, w1 - 82, 58, { fontSize: 38, minimumFontSize: 37.4, bold: true, color: theme.ink }, `pipeline-${index + 1}-text`);
  }
  h.rect(x1, 1410, w1, 360, theme.panel, "dataset-panel", theme.neutral, 3, "rounded-xl");
  h.text(content.dataset_kicker, x1 + 28, 1440, 460, 40, { fontSize: 29, minimumFontSize: 24, bold: true, color: theme.primary }, "dataset-kicker");
  body(h, theme, content.datasets, x1 + 28, 1495, w1 - 56, 230, "datasets");
  evidence(h, theme, content.dataset_evidence, x1 + 28, 1723, w1 - 56, "dataset-evidence");
  sectionTitle(h, theme, content.figure_one_heading, x1, 1825, w1, "figure-one-heading");
  await figureBlock(h, theme, content.figures[0], x1, 1915, w1, 1040, "figure-one");

  const x2 = 1420;
  const w2 = 1435;
  h.rect(x2, 590, w2, 265, theme.accent, "central-takeaway", "none", 0, "rounded-2xl");
  if ((theme.gradient_stops ?? []).length > 1) {
    gradientBand(h, theme.gradient_stops, x2, 590, w2, 20, "takeaway-cape-gradient");
  }
  h.text(content.takeaway, x2 + 44, 625, w2 - 88, 100, { fontSize: 55, minimumFontSize: 42, bold: true, color: theme.ink, alignment: "center" }, "central-takeaway-title");
  h.text(content.takeaway_subtitle, x2 + 70, 754, w2 - 140, 48, { fontSize: 32, minimumFontSize: 26, bold: true, color: theme.ink, alignment: "center" }, "central-takeaway-subtitle");
  evidence(h, theme, content.takeaway_evidence, x2 + 46, 810, w2 - 92, "takeaway-evidence");
  sectionTitle(h, theme, content.figure_two_heading, x2, 905, w2, "figure-two-heading");
  await figureBlock(h, theme, content.figures[1], x2, 995, w2, 1335, "figure-two");
  sectionTitle(h, theme, content.validation_heading, x2, 2380, w2, "validation-heading");
  h.rect(x2, 2470, w2, 425, theme.panel, "validation-panel", theme.neutral, 3, "rounded-xl");
  body(h, theme, content.validation, x2 + 36, 2503, w2 - 72, 310, "validation");
  evidence(h, theme, content.validation_evidence, x2 + 36, 2847, w2 - 72, "validation-evidence");
  h.rect(x2, 2930, w2, 115, theme.primary, "performance-strip", "none", 0, "rounded-xl");
  h.text(content.performance_strip, x2 + 34, 2960, w2 - 68, 52, { fontSize: 34, minimumFontSize: 28, bold: true, color: "#FFFFFF", alignment: "center" }, "performance-strip-text");

  const x3 = 2915;
  const w3 = 1439;
  sectionTitle(h, theme, content.biology_heading, x3, 590, w3, "biology-heading");
  const biologyColors = [theme.primary, theme.secondary, theme.accent];
  for (const [index, item] of content.biology_metrics.slice(0, 3).entries()) {
    metric(h, theme, item, x3 + index * 475, 690, 420, biologyColors[index], `biology-${index + 1}`);
  }
  evidence(h, theme, content.biology_evidence, x3, 890, w3, "biology-evidence");
  await figureBlock(h, theme, content.figures[2], x3, 965, w3, 720, "figure-three");
  sectionTitle(h, theme, content.validation_visual_heading, x3, 1735, w3, "validation-visual-heading");
  await figureBlock(h, theme, content.figures[3], x3, 1825, w3, 750, "figure-four");
  sectionTitle(h, theme, content.conclusion_heading, x3, 2625, w3, "conclusion-heading");
  h.rect(x3, 2715, w3, 330, theme.panel, "conclusion-panel", theme.neutral, 3, "rounded-xl");
  body(h, theme, content.conclusion, x3 + 34, 2748, w3 - 68, 230, "conclusion");
  evidence(h, theme, content.conclusion_evidence, x3 + 34, 2992, w3 - 68, "conclusion-evidence");

  h.rect(0, 3080, BASE_WIDTH, 99, theme.ink, "footer-band", "none", 0, "rounded-none");
  h.text(content.footer_source, 140, 3107, 3000, 42, { fontSize: 26, minimumFontSize: 22, color: "#FFFFFF" }, "footer-source");
  h.text(content.footer_status, 3120, 3107, 1230, 42, { fontSize: 25, minimumFontSize: 21, bold: true, color: theme.accent, alignment: "right" }, "footer-status");

  slide.speakerNotes.textFrame.setText(
    ["[Sources]", ...(spec.sources ?? []).map((item) => `- ${item}`), "[/Sources]"].join("\n"),
  );

  const output = path.resolve(outputPath);
  const directory = path.dirname(output);
  const stem = path.basename(output, path.extname(output));
  await fs.mkdir(directory, { recursive: true });
  await writeBlob(path.join(directory, `${stem}.png`), await deck.export({ slide, format: "png", scale: 1 }));
  await fs.writeFile(path.join(directory, `${stem}.layout.json`), await (await slide.export({ format: "layout" })).text());
  const snapshot = await deck.inspect({ kind: "slide,textbox,shape,image,notes", maxChars: 20000 });
  await fs.writeFile(path.join(directory, `${stem}.inspect.ndjson`), snapshot.ndjson);
  const pptx = await PresentationFile.exportPptx(deck);
  await pptx.save(output);
}

const args = parseArgs(process.argv);
const spec = JSON.parse(await fs.readFile(path.resolve(args.spec), "utf8"));
await build(spec, args.output);
