const pptxgen = require("pptxgenjs");

const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "Microsoft Copilot";
pptx.company = "Asterion Global Commercial";
pptx.subject = "Customer-facing Microsoft Fabric IQ commercial insurance demonstration";
pptx.title = "From Renewal Evidence to Explainable Action";
pptx.lang = "en-US";
pptx.theme = {
  headFontFace: "Georgia",
  bodyFontFace: "Aptos",
  lang: "en-US",
};
const C = {
  navy: "142D3D",
  navy2: "1F4457",
  teal: "1F7A7A",
  tealLight: "D9EEEE",
  copper: "C7653B",
  copperLight: "F3DDD2",
  gold: "D9A441",
  cream: "F7F4EE",
  white: "FFFFFF",
  ink: "20313A",
  muted: "66757F",
  line: "D9D3C8",
  green: "2E7D5B",
  greenLight: "DDEEE6",
  red: "A5463D",
  redLight: "F2DDDA",
};

function makeShadow() {
  return { type: "outer", color: "000000", blur: 4, angle: 45, offset: 2, opacity: 0.12 };
}

function contentSlide() {
  const slide = pptx.addSlide();
  slide.background = { color: C.cream };
  slide.addShape(pptx.ShapeType.rect, {
    x: 0, y: 0, w: 0.14, h: 7.5,
    fill: { color: C.copper }, line: { color: C.copper },
  });
  slide.addText("FABRIC IQ | COMMERCIAL INSURANCE", {
    x: 0.55, y: 7.12, w: 4.4, h: 0.18, fontFace: "Aptos", fontSize: 9,
    bold: true, color: C.muted, margin: 0, charSpacing: 1.2,
  });
  slide.addText("Synthetic customer demonstration", {
    x: 9.65, y: 7.12, w: 3.0, h: 0.18, fontFace: "Aptos", fontSize: 9,
    color: C.muted, align: "right", margin: 0,
  });
  return slide;
}

function addTitle(slide, title, kicker) {
  if (kicker) {
    slide.addText(kicker.toUpperCase(), {
      x: 0.72, y: 0.43, w: 4.6, h: 0.22, fontFace: "Aptos", fontSize: 10,
      bold: true, color: C.copper, charSpacing: 1.8, margin: 0,
    });
  }
  slide.addText(title, {
    x: 0.72, y: 0.78, w: 11.8, h: 0.78, fontFace: "Georgia", fontSize: 27,
    bold: true, color: C.navy, margin: 0, breakLine: false, fit: "shrink",
  });
}

function addPill(slide, text, x, y, w, fill, color = C.navy) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x, y, w, h: 0.34, rectRadius: 0.06,
    fill: { color: fill }, line: { color: fill },
  });
  slide.addText(text, {
    x: x + 0.06, y: y + 0.06, w: w - 0.12, h: 0.16,
    fontFace: "Aptos", fontSize: 9.5, bold: true, color, align: "center", margin: 0,
  });
}

function addCard(slide, x, y, w, h, title, body, accent = C.teal, options = {}) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x, y, w, h, rectRadius: 0.05,
    fill: { color: options.fill || C.white },
    line: { color: options.line || C.line, width: 1 },
    shadow: options.shadow === false ? undefined : makeShadow(),
  });
  slide.addShape(pptx.ShapeType.rect, {
    x, y, w: 0.08, h, fill: { color: accent }, line: { color: accent },
  });
  slide.addText(title, {
    x: x + 0.28, y: y + 0.23, w: w - 0.48, h: 0.3,
    fontFace: "Aptos", fontSize: options.titleSize || 15, bold: true, color: C.navy, margin: 0,
  });
  slide.addText(body, {
    x: x + 0.28, y: y + 0.65, w: w - 0.5, h: h - 0.86,
    fontFace: "Aptos", fontSize: options.bodySize || 12.5, color: C.ink,
    margin: 0, breakLine: false, valign: "top", fit: "shrink",
  });
}

function addStat(slide, x, y, w, value, label, color = C.copper) {
  slide.addText(value, {
    x, y, w, h: 0.66, fontFace: "Georgia", fontSize: 34, bold: true,
    color, align: "center", margin: 0, fit: "shrink",
  });
  slide.addText(label, {
    x, y: y + 0.72, w, h: 0.38, fontFace: "Aptos", fontSize: 11.5,
    bold: true, color: C.muted, align: "center", margin: 0, fit: "shrink",
  });
}

function addStep(slide, n, x, y, title, body, color = C.teal) {
  slide.addShape(pptx.ShapeType.ellipse, {
    x, y, w: 0.58, h: 0.58, fill: { color }, line: { color },
  });
  slide.addText(String(n), {
    x, y: y + 0.11, w: 0.58, h: 0.24, fontFace: "Aptos", fontSize: 16,
    bold: true, color: C.white, align: "center", margin: 0,
  });
  slide.addText(title, {
    x: x + 0.78, y: y - 0.01, w: 2.2, h: 0.28, fontFace: "Aptos",
    fontSize: 14, bold: true, color: C.navy, margin: 0,
  });
  slide.addText(body, {
    x: x + 0.78, y: y + 0.36, w: 2.2, h: 0.55, fontFace: "Aptos",
    fontSize: 11.5, color: C.ink, margin: 0, fit: "shrink",
  });
}

function addNotes(slide, text) {
  // PptxGenJS 4.0.1 emits an invalid notesMaster sequence when slide masters are used.
  // Keep facilitator guidance in this source until that package defect is resolved.
  void slide;
  void text;
}

function addArrow(slide, x, y, w, color = C.copper) {
  slide.addShape(pptx.ShapeType.chevron, {
    x, y, w, h: 0.35, fill: { color }, line: { color },
  });
}

// 1. Title
{
  const s = pptx.addSlide();
  s.background = { color: C.navy };
  s.addShape(pptx.ShapeType.arc, {
    x: 8.85, y: -0.8, w: 5.3, h: 5.3, adjustPoint: 0.3,
    line: { color: C.copper, width: 8, transparency: 10 }, fill: { color: C.navy, transparency: 100 },
    rotate: 18,
  });
  s.addShape(pptx.ShapeType.ellipse, {
    x: 10.5, y: 1.05, w: 1.28, h: 1.28,
    fill: { color: C.copper }, line: { color: C.copper },
  });
  s.addText("83", {
    x: 10.5, y: 1.36, w: 1.28, h: 0.4, fontFace: "Georgia",
    fontSize: 25, bold: true, color: C.white, align: "center", margin: 0,
  });
  s.addText("From renewal evidence\nto explainable action", {
    x: 0.9, y: 1.3, w: 8.6, h: 1.72, fontFace: "Georgia", fontSize: 39,
    bold: true, color: C.white, margin: 0, breakLine: false, fit: "shrink",
  });
  s.addText("A customer-facing Microsoft Fabric IQ demonstration for commercial insurance", {
    x: 0.94, y: 3.35, w: 7.8, h: 0.72, fontFace: "Aptos", fontSize: 20,
    color: "DDE7EC", margin: 0, fit: "shrink",
  });
  addPill(s, "SYNTHETIC DATA", 0.94, 4.48, 1.72, C.copperLight, C.navy);
  addPill(s, "HUMAN-GOVERNED", 2.85, 4.48, 2.05, C.tealLight, C.navy);
  addPill(s, "EXPLAINABLE SIGNALS", 5.1, 4.48, 2.28, "EAE2CC", C.navy);
  s.addText("Asterion Global Commercial", {
    x: 0.94, y: 6.55, w: 4.2, h: 0.3, fontFace: "Aptos", fontSize: 14,
    bold: true, color: C.white, margin: 0,
  });
  s.addText("Customer demo | October 2026", {
    x: 8.9, y: 6.55, w: 3.4, h: 0.3, fontFace: "Aptos", fontSize: 12,
    color: "B8C9D2", align: "right", margin: 0,
  });
  addNotes(s, "Open with the business outcome, not the technology. This is a synthetic commercial-property renewal scenario. The objective is to show how Fabric IQ connects governed data, business meaning, relationships, and real-time signals while keeping underwriting decisions with people.");
}

// 2. The business problem
{
  const s = contentSlide();
  addTitle(s, "The renewal decision is trapped across disconnected evidence", "Business challenge");
  const groups = [
    ["RISK EVIDENCE", "Exposure values\nCAT models\nClaims development", C.teal],
    ["CONTROL EVIDENCE", "Engineering actions\nProgram requirements\nSubmission status", C.gold],
    ["DECISION CONTEXT", "Renewal timing\nPremium and limits\nUnderwriter authority", C.copper],
  ];
  groups.forEach((group, i) => {
    const x = 0.9 + i * 4.15;
    s.addShape(pptx.ShapeType.roundRect, {
      x, y: 1.85, w: 3.55, h: 2.35, rectRadius: 0.06,
      fill: { color: C.white }, line: { color: group[2], width: 1.5 },
    });
    s.addText(group[0], {
      x: x + 0.28, y: 2.2, w: 2.99, h: 0.26,
      fontSize: 13.5, bold: true, color: group[2], align: "center", margin: 0,
    });
    s.addText(group[1], {
      x: x + 0.35, y: 2.85, w: 2.85, h: 0.98,
      fontSize: 13, color: C.ink, align: "center", margin: 0,
    });
  });
  s.addShape(pptx.ShapeType.roundRect, {
    x: 2.0, y: 4.72, w: 9.3, h: 1.12, rectRadius: 0.06,
    fill: { color: C.navy }, line: { color: C.navy },
  });
  s.addText("Which renewal changed, why, and what evidence should we inspect?", {
    x: 2.45, y: 5.04, w: 8.4, h: 0.42, fontFace: "Georgia", fontSize: 20,
    bold: true, color: C.white, align: "center", margin: 0, fit: "shrink",
  });
  s.addText("The opportunity: one governed account and location identity, one traceable evidence path.", {
    x: 2.0, y: 6.25, w: 9.4, h: 0.42, fontFace: "Aptos", fontSize: 17,
    bold: true, color: C.copper, align: "center", margin: 0,
  });
  addNotes(s, "Ask the customer where this evidence lives today. Emphasize that the problem is not lack of data; it is fragmented meaning and weak evidence traceability. Do not imply causal inference or automated underwriting.");
}

// 3. Fabric IQ concepts
{
  const s = contentSlide();
  addTitle(s, "Fabric IQ turns governed data into shared business meaning", "Concept");
  const stages = [
    ["1", "Data", "OneLake stores a trusted, reusable foundation.", C.navy2],
    ["2", "Semantics", "Measures define the numbers once.", C.teal],
    ["3", "Entity links", "Ontology and Graph connect business entities.", C.gold],
    ["4", "Reasoning", "Agents answer with grounded context.", C.copper],
    ["5", "Monitoring", "Real-Time Intelligence detects change.", C.red],
    ["6", "Human action", "People review evidence and decide.", C.green],
  ];
  stages.forEach((stage, i) => {
    const x = 0.72 + i * 2.05;
    s.addShape(pptx.ShapeType.roundRect, {
      x, y: 2.0, w: 1.72, h: 3.2, rectRadius: 0.06,
      fill: { color: C.white }, line: { color: stage[3], width: 1.5 },
    });
    s.addShape(pptx.ShapeType.ellipse, { x: x + 0.48, y: 1.56, w: 0.76, h: 0.76, fill: { color: stage[3] }, line: { color: stage[3] } });
    s.addText(stage[0], { x: x + 0.48, y: 1.75, w: 0.76, h: 0.25, fontSize: 15, bold: true, color: C.white, align: "center", margin: 0 });
    s.addText(stage[1], { x: x + 0.18, y: 2.55, w: 1.36, h: 0.42, fontFace: "Georgia", fontSize: 16, bold: true, color: C.navy, align: "center", margin: 0, fit: "shrink" });
    s.addText(stage[2], { x: x + 0.2, y: 3.25, w: 1.32, h: 1.2, fontSize: 11, color: C.ink, align: "center", margin: 0, fit: "shrink" });
  });
  s.addShape(pptx.ShapeType.roundRect, {
    x: 3.06, y: 5.68, w: 7.2, h: 0.7, rectRadius: 0.05,
    fill: { color: C.copperLight }, line: { color: C.copperLight },
  });
  s.addText("Design contract: DATA > SEMANTICS > RELATIONSHIPS > REASONING > MONITORING > DECISION > ACTION", {
    x: 2.5, y: 5.91, w: 8.35, h: 0.22, fontSize: 10.5, bold: true,
    color: C.navy, align: "center", margin: 0, charSpacing: 0.35, fit: "shrink",
  });
  addNotes(s, "Use this slide to explain Fabric IQ in plain language. The sequence matters: agents and monitoring are only useful when data, semantics, and relationships are governed first. Human action remains the last step.");
}

// 4. Architecture
{
  const s = contentSlide();
  addTitle(s, "A medallion foundation powers both analytical and real-time experiences", "Solution architecture");
  const layers = [
    { x: 0.82, title: "BRONZE", body: "31 source tables\n+ audit columns", color: "8B6F47" },
    { x: 3.2, title: "SILVER", body: "features, pulse\n+ material signals", color: C.teal },
    { x: 5.58, title: "GOLD", body: "graph-ready nodes\n+ relationships", color: C.gold },
  ];
  layers.forEach((l, i) => {
    s.addShape(pptx.ShapeType.roundRect, {
      x: l.x, y: 2.15, w: 1.9, h: 2.1, rectRadius: 0.05,
      fill: { color: C.white }, line: { color: l.color, width: 2 }, shadow: makeShadow(),
    });
    s.addText(l.title, { x: l.x + 0.16, y: 2.48, w: 1.58, h: 0.32, fontSize: 17, bold: true, color: l.color, align: "center", margin: 0 });
    s.addText(l.body, { x: l.x + 0.18, y: 3.12, w: 1.54, h: 0.66, fontSize: 12, color: C.ink, align: "center", margin: 0, fit: "shrink" });
    if (i < layers.length - 1) addArrow(s, l.x + 2.02, 3.02, 0.27, C.copper);
  });
  s.addShape(pptx.ShapeType.roundRect, {
    x: 8.05, y: 1.55, w: 2.0, h: 1.25, rectRadius: 0.05,
    fill: { color: C.redLight }, line: { color: C.red, width: 1.5 }, shadow: makeShadow(),
  });
  s.addText("EVENTHOUSE", { x: 8.25, y: 1.85, w: 1.6, h: 0.28, fontSize: 15, bold: true, color: C.red, align: "center", margin: 0 });
  s.addText("live change signals", { x: 8.25, y: 2.28, w: 1.6, h: 0.22, fontSize: 11, color: C.ink, align: "center", margin: 0 });
  s.addShape(pptx.ShapeType.roundRect, {
    x: 8.05, y: 3.45, w: 2.0, h: 1.25, rectRadius: 0.05,
    fill: { color: C.tealLight }, line: { color: C.teal, width: 1.5 }, shadow: makeShadow(),
  });
  s.addText("DIRECT LAKE", { x: 8.25, y: 3.75, w: 1.6, h: 0.28, fontSize: 15, bold: true, color: C.teal, align: "center", margin: 0 });
  s.addText("shared measures", { x: 8.25, y: 4.18, w: 1.6, h: 0.22, fontSize: 11, color: C.ink, align: "center", margin: 0 });
  s.addShape(pptx.ShapeType.roundRect, {
    x: 10.62, y: 2.15, w: 1.9, h: 2.1, rectRadius: 0.05,
    fill: { color: C.navy }, line: { color: C.navy }, shadow: makeShadow(),
  });
  s.addText("FABRIC IQ", { x: 10.84, y: 2.52, w: 1.46, h: 0.32, fontFace: "Georgia", fontSize: 17, bold: true, color: C.white, align: "center", margin: 0 });
  s.addText("ontology\nGraph\nagents\nhuman review", { x: 10.9, y: 3.04, w: 1.34, h: 0.88, fontSize: 11.5, color: "DDE7EC", align: "center", margin: 0, fit: "shrink" });
  addArrow(s, 7.62, 2.2, 0.32, C.line);
  addArrow(s, 7.62, 3.95, 0.32, C.line);
  addArrow(s, 10.16, 2.14, 0.32, C.red);
  addArrow(s, 10.16, 4.02, 0.32, C.teal);
  s.addText("Identity + evidence path: Account > Policy > Location > Claim > Renewal > Signal", {
    x: 1.05, y: 5.52, w: 11.2, h: 0.32, fontFace: "Georgia", fontSize: 14.5,
    bold: true, color: C.navy, align: "center", margin: 0, fit: "shrink",
  });
  addNotes(s, "Walk left to right. Bronze preserves source shape, Silver adds explainable features, and Gold produces relationship-ready tables. Direct Lake gives shared business measures; Eventhouse provides the time-sensitive path. Fabric IQ experiences sit on top, not beside, the governed foundation.");
}

// 5. Portfolio proof
{
  const s = contentSlide();
  addTitle(s, "The demo is deterministic, evidence-rich, and safe to rehearse", "Portfolio proof");
  const statData = [
    ["20", "commercial accounts"],
    ["100", "insured locations"],
    ["40", "policy years"],
    ["80", "claims"],
    ["31", "governed tables"],
    ["5,475", "referential checks"],
  ];
  statData.forEach((d, i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    const x = 0.85 + col * 3.98;
    const y = 1.75 + row * 2.18;
    s.addShape(pptx.ShapeType.roundRect, {
      x, y, w: 3.48, h: 1.65, rectRadius: 0.06,
      fill: { color: row === 0 ? C.white : "F1EEE7" },
      line: { color: C.line }, shadow: makeShadow(),
    });
    addStat(s, x + 0.25, y + 0.25, 2.98, d[0], d[1], [C.copper, C.teal, C.gold][col]);
  });
  s.addShape(pptx.ShapeType.roundRect, {
    x: 2.45, y: 6.04, w: 8.42, h: 0.55, rectRadius: 0.05,
    fill: { color: C.greenLight }, line: { color: C.greenLight },
  });
  s.addText("All values are synthetic. Checkpoints prove reproducibility, not production readiness.", {
    x: 2.68, y: 6.21, w: 7.96, h: 0.2, fontSize: 12.5, bold: true,
    color: C.green, align: "center", margin: 0,
  });
  addNotes(s, "Use these numbers to establish demo credibility. The data has stable IDs, matched valuation dates, integer-cent monetary values, and explicit foreign-key checks. Avoid presenting row volume as scale testing.");
}

// 6. Hero account
{
  const s = contentSlide();
  addTitle(s, "A001: one renewal, one transparent evidence story", "Hero account");
  s.addShape(pptx.ShapeType.roundRect, {
    x: 0.82, y: 1.62, w: 4.05, h: 4.75, rectRadius: 0.06,
    fill: { color: C.navy }, line: { color: C.navy }, shadow: makeShadow(),
  });
  s.addText("MERIDIAN SPECIALTY\nCHEMICALS", {
    x: 1.18, y: 2.02, w: 3.33, h: 0.8, fontFace: "Georgia", fontSize: 22,
    bold: true, color: C.white, align: "center", margin: 0, fit: "shrink",
  });
  s.addText("Global property renewal | 28 days", {
    x: 1.22, y: 3.02, w: 3.25, h: 0.28, fontSize: 12.5,
    color: "C8D8E0", align: "center", margin: 0,
  });
  s.addShape(pptx.ShapeType.ellipse, { x: 1.65, y: 3.65, w: 2.38, h: 2.38, fill: { color: C.copper }, line: { color: C.copper } });
  s.addText("77", { x: 1.65, y: 4.15, w: 2.38, h: 0.66, fontFace: "Georgia", fontSize: 44, bold: true, color: C.white, align: "center", margin: 0 });
  s.addText("BASELINE PULSE", { x: 1.65, y: 5.08, w: 2.38, h: 0.24, fontSize: 10.5, bold: true, color: C.white, align: "center", margin: 0, charSpacing: 1.1 });
  const facts = [
    ["$1.14B", "current total insured value", C.teal],
    ["$7M", "modeled CAT AAL", C.gold],
    ["$7M", "current incurred loss", C.copper],
    ["2", "open critical recommendations", C.red],
  ];
  facts.forEach((f, i) => {
    const x = 5.45 + (i % 2) * 3.42;
    const y = 1.8 + Math.floor(i / 2) * 2.25;
    s.addShape(pptx.ShapeType.roundRect, {
      x, y, w: 3.05, h: 1.8, rectRadius: 0.05,
      fill: { color: C.white }, line: { color: C.line }, shadow: makeShadow(),
    });
    s.addText(f[0], { x: x + 0.2, y: y + 0.3, w: 2.65, h: 0.6, fontFace: "Georgia", fontSize: 29, bold: true, color: f[2], align: "center", margin: 0 });
    s.addText(f[1], { x: x + 0.28, y: y + 1.1, w: 2.49, h: 0.35, fontSize: 12, bold: true, color: C.ink, align: "center", margin: 0, fit: "shrink" });
  });
  s.addText("The pulse prioritizes review. It does not price, bind, decline, or infer causation.", {
    x: 5.5, y: 6.05, w: 6.35, h: 0.43, fontSize: 14, bold: true,
    color: C.red, align: "center", margin: 0,
  });
  addNotes(s, "Introduce the fictional hero account. Ask the audience to remember three values: 1.14 billion TIV, pulse 77, and 28 days to renewal. The demo will show why the pulse changes and how to trace it back to evidence.");
}

// 7. Explainable pulse
{
  const s = contentSlide();
  addTitle(s, "The Renewal Risk Pulse is additive, bounded, and explainable", "Concept");
  const components = [
    ["CAT", 20, 25, C.red],
    ["Claims", 16, 20, C.copper],
    ["Growth", 7, 10, C.gold],
    ["Engineering", 17, 20, C.teal],
    ["Concentration", 8, 10, C.navy2],
    ["Missing", 6, 10, C.green],
    ["Proximity", 3, 5, "7D6B91"],
  ];
  components.forEach((c, i) => {
    const y = 1.62 + i * 0.67;
    s.addText(c[0], { x: 0.85, y: y + 0.08, w: 1.35, h: 0.22, fontSize: 12, bold: true, color: C.navy, margin: 0 });
    s.addShape(pptx.ShapeType.roundRect, { x: 2.25, y, w: 6.7, h: 0.36, rectRadius: 0.05, fill: { color: "E6E2DA" }, line: { color: "E6E2DA" } });
    s.addShape(pptx.ShapeType.roundRect, { x: 2.25, y, w: 6.7 * (c[1] / 25), h: 0.36, rectRadius: 0.05, fill: { color: c[3] }, line: { color: c[3] } });
    s.addText(`${c[1]} / ${c[2]} pts`, { x: 9.18, y: y + 0.07, w: 1.0, h: 0.22, fontSize: 11, bold: true, color: c[3], align: "right", margin: 0 });
  });
  s.addShape(pptx.ShapeType.ellipse, {
    x: 10.55, y: 2.15, w: 1.95, h: 1.95, fill: { color: C.navy }, line: { color: C.navy }, shadow: makeShadow(),
  });
  s.addText("77", { x: 10.55, y: 2.62, w: 1.95, h: 0.58, fontFace: "Georgia", fontSize: 38, bold: true, color: C.white, align: "center", margin: 0 });
  s.addText("TOTAL", { x: 10.55, y: 3.4, w: 1.95, h: 0.22, fontSize: 10, bold: true, color: "C8D8E0", align: "center", margin: 0, charSpacing: 1.2 });
  s.addShape(pptx.ShapeType.roundRect, {
    x: 10.35, y: 4.72, w: 2.35, h: 1.05, rectRadius: 0.05,
    fill: { color: C.copperLight }, line: { color: C.copper },
  });
  s.addText("Every signal retains\nsource + evidence key", {
    x: 10.58, y: 4.98, w: 1.89, h: 0.46, fontSize: 12.5, bold: true,
    color: C.navy, align: "center", margin: 0, fit: "shrink",
  });
  s.addText("Weights total 100. Every component is clipped to [0,1]. No hidden model score.", {
    x: 1.36, y: 6.43, w: 8.7, h: 0.28, fontSize: 12.5, bold: true,
    color: C.muted, align: "center", margin: 0,
  });
  addNotes(s, "Explain the score as a transparent prioritization index. The colored bars are contributions, not raw values. Each component is bounded between zero and one; weights sum to 100. This is intentionally not an actuarial or machine-learning claim.");
}

// 8. Real-time loop
{
  const s = contentSlide();
  addTitle(s, "Real-time monitoring detects the moment review priority changes", "Concept");
  s.addChart(pptx.ChartType.line, [
    { name: "Renewal Risk Pulse", labels: ["Baseline", "CAT + reserve update"], values: [77, 83] },
  ], {
    x: 0.85, y: 1.65, w: 7.4, h: 4.7,
    showLegend: false, showTitle: false, showValue: true,
    catAxisLabelFontFace: "Aptos", catAxisLabelFontSize: 12,
    valAxisLabelFontFace: "Aptos", valAxisLabelFontSize: 10,
    valAxisMinVal: 70, valAxisMaxVal: 86, valAxisMajorUnit: 2,
    chartColors: [C.copper], lineSize: 4, showMarker: true, markerSize: 10,
    showCatName: false, dataLabelColor: C.navy, dataLabelPosition: "t",
    chartArea: { fill: { color: C.white }, border: { color: C.line, width: 1 }, roundedCorners: true },
    plotArea: { fill: { color: C.white }, border: { color: C.white } },
    showValue: true, showValAxisTitle: false, showCatAxisTitle: false,
    showGridLines: true, gridLine: { color: "E3DED5", width: 1 },
  });
  addCard(s, 8.65, 1.72, 3.72, 1.25, "1. Ingest", "Eventhouse receives baseline and update events.", C.red, { bodySize: 11.5 });
  addCard(s, 8.65, 3.18, 3.72, 1.25, "2. Validate", "KQL deduplicates events and recomputes the pulse.", C.teal, { bodySize: 11.5 });
  addCard(s, 8.65, 4.64, 3.72, 1.25, "3. Surface", "One verified crossing becomes a review signal.", C.green, { bodySize: 11.5 });
  s.addText("Verified: A001 crossed 77 to 83", {
    x: 8.92, y: 6.2, w: 3.15, h: 0.3, fontSize: 12.5, bold: true,
    color: C.copper, align: "center", margin: 0,
  });
  addNotes(s, "This is the live reveal. Baseline 77 does not cross the review threshold. The staged CAT and reserve update moves the score to 83. KQL validates component ranges and recomputes the score before the crossing is surfaced.");
}

// 9. Run of show
{
  const s = contentSlide();
  addTitle(s, "Customer demo: four acts in twelve minutes", "Run of show");
  const acts = [
    ["01", "Orient", "Open the workspace and show the three Lakehouses.", "2 min", C.navy2],
    ["02", "Trace", "Walk A001 from curated data to the semantic model.", "3 min", C.teal],
    ["03", "Explain", "Decompose pulse 77 into seven visible contributions.", "3 min", C.gold],
    ["04", "Detect", "Run the Eventhouse query and reveal 77 -> 83.", "4 min", C.copper],
  ];
  acts.forEach((a, i) => {
    const x = 0.82 + i * 3.08;
    s.addShape(pptx.ShapeType.roundRect, {
      x, y: 1.85, w: 2.62, h: 3.95, rectRadius: 0.06,
      fill: { color: i === 3 ? C.navy : C.white },
      line: { color: a[4], width: 1.5 }, shadow: makeShadow(),
    });
    s.addText(a[0], { x: x + 0.24, y: 2.12, w: 0.7, h: 0.45, fontFace: "Georgia", fontSize: 24, bold: true, color: a[4], margin: 0 });
    s.addText(a[1], { x: x + 0.24, y: 2.8, w: 2.12, h: 0.42, fontFace: "Georgia", fontSize: 20, bold: true, color: i === 3 ? C.white : C.navy, margin: 0 });
    s.addText(a[2], { x: x + 0.24, y: 3.62, w: 2.12, h: 1.05, fontSize: 12.5, color: i === 3 ? "DDE7EC" : C.ink, margin: 0, fit: "shrink" });
    addPill(s, a[3], x + 0.7, 5.08, 1.22, i === 3 ? C.copper : C.copperLight, i === 3 ? C.white : C.navy);
  });
  s.addText("Presenter principle: show the evidence first; reveal advanced experiences only after the core proof reconciles.", {
    x: 1.32, y: 6.35, w: 10.65, h: 0.35, fontSize: 13.5, bold: true,
    color: C.muted, align: "center", margin: 0,
  });
  addNotes(s, "Set expectations for the live flow. If time is short, complete acts 1 through 4 and skip optional Graph or agent discussions. This sequence protects credibility because each later experience rests on a verified core result.");
}

// 10. Demo step 1
{
  const s = contentSlide();
  addTitle(s, "Demo step 1: prove the governed data foundation", "Live demo");
  const pipeline = [
    ["01", "Generate", "synthetic portfolio", C.navy2],
    ["02", "Persist", "31 Delta tables", "8B6F47"],
    ["03", "Feature", "20 account rows", C.teal],
    ["04", "Score", "A001 pulse 77", C.gold],
    ["05", "Signal", "44 evidence flags", C.copper],
    ["06", "Relate", "nodes + edges", C.green],
    ["07", "Stage", "live event pair", C.red],
  ];
  pipeline.forEach((p, i) => {
    const x = 0.55 + i * 1.8;
    s.addShape(pptx.ShapeType.roundRect, {
      x, y: 2.05, w: 1.48, h: 2.35, rectRadius: 0.05,
      fill: { color: C.white }, line: { color: p[3], width: 1.5 }, shadow: makeShadow(),
    });
    s.addText(p[0], { x: x + 0.12, y: 2.25, w: 0.52, h: 0.3, fontFace: "Georgia", fontSize: 17, bold: true, color: p[3], margin: 0 });
    s.addText(p[1], { x: x + 0.12, y: 2.92, w: 1.24, h: 0.32, fontSize: 14, bold: true, color: C.navy, align: "center", margin: 0, fit: "shrink" });
    s.addText(p[2], { x: x + 0.15, y: 3.47, w: 1.18, h: 0.48, fontSize: 10.5, color: C.ink, align: "center", margin: 0, fit: "shrink" });
    if (i < pipeline.length - 1) addArrow(s, x + 1.52, 3.03, 0.22, C.line);
  });
  addCard(s, 1.0, 5.05, 3.25, 1.15, "Show", "Three Lakehouses and seven completed notebook jobs.", C.teal, { bodySize: 11.5 });
  addCard(s, 5.02, 5.05, 3.25, 1.15, "Say", "Bronze preserves; Silver explains; Gold relates.", C.gold, { bodySize: 11.5 });
  addCard(s, 9.05, 5.05, 3.25, 1.15, "Checkpoint", "31 tables, 3,731 rows, 5,475 checks.", C.copper, { bodySize: 11.5 });
  addNotes(s, "Open the Test workspace after resuming capacity. Show CI_Bronze_Dev, CI_Silver_Dev, and CI_Gold_Dev. In the job history, confirm all seven notebooks completed. Do not rerun the pipeline during a customer presentation unless a rebuild is intentional.");
}

// 11. Demo step 2
{
  const s = contentSlide();
  addTitle(s, "Demo step 2: ask once, answer with shared semantics", "Live demo");
  s.addShape(pptx.ShapeType.roundRect, {
    x: 0.82, y: 1.72, w: 4.5, h: 4.9, rectRadius: 0.06,
    fill: { color: C.navy }, line: { color: C.navy }, shadow: makeShadow(),
  });
  s.addText("Commercial Insurance IQ Model", {
    x: 1.18, y: 2.12, w: 3.78, h: 0.42, fontFace: "Georgia", fontSize: 20,
    bold: true, color: C.white, align: "center", margin: 0, fit: "shrink",
  });
  s.addText("Direct Lake | 27 tables | 30 measures", { x: 1.35, y: 2.78, w: 3.45, h: 0.32, fontSize: 13.5, bold: true, color: C.copper, align: "center", margin: 0, fit: "shrink" });
  const mini = [
    ["Accounts + Policies", "20 accounts | 40 policies"],
    ["RiskPulse + Signals", "A001 = 77 | 4 signals"],
    ["Exposures + CAT + Claims", "$1.14B TIV | $7M CAT"],
  ];
  mini.forEach((m, i) => {
    const y = 3.42 + i * 0.86;
    s.addShape(pptx.ShapeType.roundRect, { x: 1.28, y, w: 3.58, h: 0.58, rectRadius: 0.04, fill: { color: C.navy2 }, line: { color: "4F6C7D" } });
    s.addText(m[0], { x: 1.44, y: y + 0.14, w: 1.78, h: 0.2, fontSize: 11, bold: true, color: C.white, margin: 0, fit: "shrink" });
    s.addText(m[1], { x: 3.22, y: y + 0.14, w: 1.5, h: 0.2, fontSize: 10.5, color: "DDE7EC", align: "right", margin: 0, fit: "shrink" });
  });
  const asks = [
    ["1", "Filter", "AccountId = A001"],
    ["2", "Read", "TIV, CAT AAL, incurred"],
    ["3", "Reconcile", "Pulse and evidence IDs"],
  ];
  asks.forEach((a, i) => addStep(s, a[0], 6.1, 1.95 + i * 1.35, a[1], a[2], [C.teal, C.gold, C.copper][i]));
  s.addShape(pptx.ShapeType.roundRect, {
    x: 6.18, y: 5.95, w: 5.55, h: 0.62, rectRadius: 0.05,
    fill: { color: C.greenLight }, line: { color: C.green },
  });
  s.addText("Verified: 27 tables | A001 = 77 | TIV = $1.14B | CAT = $7M", {
    x: 6.32, y: 6.15, w: 5.28, h: 0.22, fontSize: 11, bold: true,
    color: C.green, align: "center", margin: 0, fit: "shrink",
  });
  addNotes(s, "Open CommercialInsuranceIQModel and run the prepared DAX or use a simple visual filtered to A001. Point out that source cents become dollars only in reviewed measures. Show the engine result, not a screenshot of an expected value.");
}

// 12. Demo step 3
{
  const s = contentSlide();
  addTitle(s, "Demo step 3: prove the threshold crossing", "Live demo | KQL");
  const code = [
    "DedupedEvents()",
    "| where RunId == 'deployed-001'",
    "| sort by AccountId, EventTime, Sequence",
    "| serialize",
    "| extend PreviousPulse = prev(Pulse)",
    "| where PreviousPulse < 80 and Pulse >= 80",
    "| project AccountId, PreviousPulse, Pulse",
  ].join("\n");
  s.addShape(pptx.ShapeType.roundRect, {
    x: 0.82, y: 1.82, w: 6.4, h: 4.55, rectRadius: 0.05,
    fill: { color: "102631" }, line: { color: C.navy2 }, shadow: makeShadow(),
  });
  s.addText(code, {
    x: 1.16, y: 2.12, w: 5.75, h: 3.8, fontFace: "Consolas", fontSize: 15,
    color: "D7E7ED", margin: 0.04, breakLine: false, fit: "shrink",
  });
  s.addShape(pptx.ShapeType.roundRect, {
    x: 7.75, y: 1.82, w: 4.7, h: 1.85, rectRadius: 0.06,
    fill: { color: C.white }, line: { color: C.line }, shadow: makeShadow(),
  });
  s.addText("PRIMARY RESULT", { x: 8.08, y: 2.12, w: 4.04, h: 0.24, fontSize: 10.5, bold: true, color: C.muted, align: "center", margin: 0, charSpacing: 1.1 });
  s.addText("A001", { x: 8.05, y: 2.6, w: 1.05, h: 0.4, fontFace: "Georgia", fontSize: 23, bold: true, color: C.navy, align: "center", margin: 0 });
  s.addText("77", { x: 9.25, y: 2.6, w: 0.8, h: 0.4, fontFace: "Georgia", fontSize: 23, bold: true, color: C.copper, align: "center", margin: 0 });
  addArrow(s, 10.06, 2.65, 0.42, C.copper);
  s.addText("83", { x: 10.58, y: 2.6, w: 0.8, h: 0.4, fontFace: "Georgia", fontSize: 23, bold: true, color: C.red, align: "center", margin: 0 });
  s.addShape(pptx.ShapeType.roundRect, {
    x: 7.75, y: 4.05, w: 4.7, h: 2.32, rectRadius: 0.06,
    fill: { color: C.copperLight }, line: { color: C.copper }, shadow: makeShadow(),
  });
  s.addText("Narrate the proof", { x: 8.1, y: 4.36, w: 4.0, h: 0.3, fontFace: "Georgia", fontSize: 18, bold: true, color: C.navy, align: "center", margin: 0 });
  s.addText("One run ID\nOne account\nOne ordered event pair\nOne validated crossing", {
    x: 8.5, y: 4.95, w: 3.2, h: 0.95, fontSize: 13, color: C.ink,
    align: "center", margin: 0, fit: "shrink",
  });
  addNotes(s, "Open CI_Underwriting_RTI and run the crossing query. Confirm the result is exactly one row for A001 with previous pulse 77 and current pulse 83. Explain that deduplication and score recomputation prevent success-shaped results from malformed events.");
}

// 13. Advanced experiences
{
  const s = contentSlide();
  addTitle(s, "Demo step 4: traverse Ontology, Graph, and governed agents", "Connected Fabric IQ experiences");
  const cards = [
    ["Ontology", "25 entity types, 30 relationships, plus live Eventhouse time-series binding on Account.", "Deployed: 25 entities + RTI binding", C.gold, C.greenLight],
    ["Graph (GQL)", "Connected-risk traversal across accounts, locations, claims, and multinational programs.", "Verified: 5 GQL queries (10/5/20/2/25 rows)", C.teal, C.tealLight],
    ["Data Agent", "Natural-language Q&A grounded in CommercialInsuranceIQModel and CI_Gold_Dev.", "Published: Model + Gold LH + 4 few-shots", C.navy2, C.greenLight],
    ["Operations Agent", "Monitors LatestPulse() for threshold crossings while keeping actions human-governed.", "Configured: stopped by default (Inactive)", C.copper, C.copperLight],
  ];
  cards.forEach((c, i) => {
    const x = 0.82 + (i % 2) * 6.08;
    const y = 1.72 + Math.floor(i / 2) * 2.45;
    s.addShape(pptx.ShapeType.roundRect, {
      x, y, w: 5.55, h: 2.05, rectRadius: 0.06,
      fill: { color: C.white }, line: { color: c[3], width: 1.5 }, shadow: makeShadow(),
    });
    s.addShape(pptx.ShapeType.ellipse, { x: x + 0.3, y: y + 0.34, w: 0.72, h: 0.72, fill: { color: c[3] }, line: { color: c[3] } });
    s.addText(c[0].slice(0, 1), { x: x + 0.3, y: y + 0.53, w: 0.72, h: 0.22, fontSize: 15, bold: true, color: C.white, align: "center", margin: 0 });
    s.addText(c[0], { x: x + 1.22, y: y + 0.28, w: 3.85, h: 0.32, fontFace: "Georgia", fontSize: 18, bold: true, color: C.navy, margin: 0 });
    s.addText(c[1], { x: x + 1.22, y: y + 0.8, w: 3.85, h: 0.45, fontSize: 11.5, color: C.ink, margin: 0, fit: "shrink" });
    addPill(s, c[2], x + 1.2, y + 1.45, 3.95, c[4], C.navy);
  });
  s.addText("Every IQ experience reconciles to the same governed Gold tables, DAX measures, and KQL events.", {
    x: 1.7, y: 6.42, w: 9.9, h: 0.3, fontSize: 13, bold: true,
    color: C.navy, align: "center", margin: 0, fit: "shrink",
  });
  addNotes(s, "Show CommercialInsuranceOntology (25 entities, 30 relationships, plus Account time-series binding), run the 5 GQL queries on CI_Underwriting_Graph_Dev, demonstrate CommercialInsuranceDataAgent, and show RenewalRiskOperationsAgent in its governed Inactive state.");
}

// 14. Governance
{
  const s = contentSlide();
  addTitle(s, "Trust comes from explicit boundaries, not polished answers", "Governance");
  const good = [
    "Synthetic, isolated lab data",
    "Stable IDs and matched valuation dates",
    "Integer-cent financial source values",
    "Evidence keys retained on every signal",
    "Human review before any action",
  ];
  const avoid = [
    "No actuarial pricing claim",
    "No automated bind / decline / referral",
    "No causal inference from correlated signals",
    "No production security waiver",
    "No unapproved notification or capacity change",
  ];
  s.addShape(pptx.ShapeType.roundRect, {
    x: 0.82, y: 1.62, w: 5.75, h: 4.95, rectRadius: 0.06,
    fill: { color: C.greenLight }, line: { color: C.green }, shadow: makeShadow(),
  });
  s.addText("WHAT WE PROVE", { x: 1.15, y: 2.0, w: 5.1, h: 0.34, fontSize: 15, bold: true, color: C.green, align: "center", margin: 0, charSpacing: 1.4 });
  good.forEach((g, i) => {
    s.addShape(pptx.ShapeType.ellipse, { x: 1.25, y: 2.72 + i * 0.68, w: 0.33, h: 0.33, fill: { color: C.green }, line: { color: C.green } });
    s.addText("OK", { x: 1.25, y: 2.81 + i * 0.68, w: 0.33, h: 0.12, fontSize: 6.5, bold: true, color: C.white, align: "center", margin: 0 });
    s.addText(g, { x: 1.78, y: 2.73 + i * 0.68, w: 4.25, h: 0.26, fontSize: 13, bold: true, color: C.ink, margin: 0 });
  });
  s.addShape(pptx.ShapeType.roundRect, {
    x: 6.88, y: 1.62, w: 5.58, h: 4.95, rectRadius: 0.06,
    fill: { color: C.redLight }, line: { color: C.red }, shadow: makeShadow(),
  });
  s.addText("WHAT WE DO NOT CLAIM", { x: 7.22, y: 2.0, w: 4.9, h: 0.34, fontSize: 15, bold: true, color: C.red, align: "center", margin: 0, charSpacing: 1.1 });
  avoid.forEach((g, i) => {
    s.addShape(pptx.ShapeType.ellipse, { x: 7.3, y: 2.72 + i * 0.68, w: 0.33, h: 0.33, fill: { color: C.red }, line: { color: C.red } });
    s.addText("NO", { x: 7.3, y: 2.81 + i * 0.68, w: 0.33, h: 0.12, fontSize: 6.5, bold: true, color: C.white, align: "center", margin: 0 });
    s.addText(g, { x: 7.83, y: 2.73 + i * 0.68, w: 4.05, h: 0.26, fontSize: 13, bold: true, color: C.ink, margin: 0 });
  });
  addNotes(s, "Pause here for risk, legal, security, and operations stakeholders. The demo is intentionally designed to make boundaries visible. A trustworthy demonstration states what was executed, what was not executed, and what remains subject to production controls.");
}

// 15. Close
{
  const s = pptx.addSlide();
  s.background = { color: C.navy };
  s.addText("One connected renewal story.\nThree customer outcomes.", {
    x: 0.9, y: 0.82, w: 7.6, h: 1.2, fontFace: "Georgia", fontSize: 34,
    bold: true, color: C.white, margin: 0, fit: "shrink",
  });
  const outcomes = [
    ["FASTER", "Prioritize the accounts that changed before renewal."],
    ["CLEARER", "Explain every score through measures and evidence keys."],
    ["SAFER", "Keep pricing, binding, and notification human-governed."],
  ];
  outcomes.forEach((o, i) => {
    const x = 0.95 + i * 4.08;
    s.addShape(pptx.ShapeType.roundRect, {
      x, y: 2.55, w: 3.6, h: 2.35, rectRadius: 0.06,
      fill: { color: i === 1 ? C.copper : C.navy2 },
      line: { color: i === 1 ? C.copper : "4F6C7D" }, shadow: makeShadow(),
    });
    s.addText(o[0], { x: x + 0.25, y: 2.94, w: 3.1, h: 0.38, fontSize: 18, bold: true, color: C.white, align: "center", margin: 0, charSpacing: 1.5 });
    s.addText(o[1], { x: x + 0.42, y: 3.62, w: 2.76, h: 0.72, fontSize: 13.5, color: C.white, align: "center", margin: 0, fit: "shrink" });
  });
  s.addShape(pptx.ShapeType.roundRect, {
    x: 2.3, y: 5.68, w: 8.7, h: 0.72, rectRadius: 0.05,
    fill: { color: C.cream }, line: { color: C.cream },
  });
  s.addText("Recommended next step: run a 60-minute design workshop using one customer renewal journey.", {
    x: 2.65, y: 5.92, w: 8.0, h: 0.24, fontSize: 14.5, bold: true,
    color: C.navy, align: "center", margin: 0, fit: "shrink",
  });
  s.addText("Microsoft Fabric IQ | Commercial Insurance", {
    x: 0.95, y: 6.88, w: 4.5, h: 0.22, fontSize: 11, bold: true,
    color: "C8D8E0", margin: 0,
  });
  addNotes(s, "Close on outcomes and propose a customer-specific design workshop. The workshop should replace the synthetic entities and measures with one real renewal journey, then assess governance, tenant capability, security, and production operating requirements.");
}

(async () => {
  if (process.env.MAX_SLIDES) {
    const start = Math.max(0, Number(process.env.START_SLIDE || 1) - 1);
    pptx._slides = pptx._slides.slice(start, Number(process.env.MAX_SLIDES));
  }
  await pptx.writeFile({
    fileName: process.env.OUTPUT_FILE || "Fabric-IQ-Commercial-Insurance-Customer-Demo.pptx",
  });
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
