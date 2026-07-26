"""
Generates data/manuals/sample-refrigerator-manual.pdf — an ORIGINAL, fictional
refrigerator manual used to demo and test the RAG pipeline.

Why this exists instead of a real Panasonic manual:
Real manuals are copyrighted, so this repo doesn't ship one. This sample is
written from scratch to be structurally realistic (safety info, controls,
troubleshooting table, spec sheet) so ingestion/chunking/retrieval can be
tested and demoed end to end. Swap it for your official manual PDF and
re-run ingestion — see README.md.

Run: python make_sample_manual.py   (writes into ./manuals/)
"""

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, ListFlowable, ListItem
)
from reportlab.lib.enums import TA_CENTER

OUT_PATH = "manuals/sample-refrigerator-manual.pdf"

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="ManualTitle", fontSize=22, leading=26, spaceAfter=6, alignment=TA_CENTER))
styles.add(ParagraphStyle(name="ManualSubtitle", fontSize=12, leading=16, spaceAfter=4, alignment=TA_CENTER, textColor=colors.HexColor("#555555")))
styles.add(ParagraphStyle(name="Disclaimer", fontSize=9, leading=13, textColor=colors.HexColor("#8a5a00"), backColor=colors.HexColor("#fff6e0"), borderPadding=8, spaceAfter=14))
styles.add(ParagraphStyle(name="H1", parent=styles["Heading1"], fontSize=15, spaceBefore=14, spaceAfter=8))
styles.add(ParagraphStyle(name="H2", parent=styles["Heading2"], fontSize=12, spaceBefore=10, spaceAfter=6))
styles.add(ParagraphStyle(name="Body", parent=styles["Normal"], fontSize=10, leading=14.5, spaceAfter=6))

story = []

# ---------- Title page ----------
story.append(Spacer(1, 1.2 * inch))
story.append(Paragraph("Refrigerator User Manual", styles["ManualTitle"]))
story.append(Paragraph("Model RF-2200X &nbsp;|&nbsp; French Door Refrigerator with Eco Sensor", styles["ManualSubtitle"]))
story.append(Spacer(1, 0.4 * inch))
story.append(Paragraph(
    "<b>Sample document.</b> This manual was written for a portfolio/demo RAG project and is "
    "not an official Panasonic publication. Model name, error codes, and specifications below "
    "are illustrative, not real product data. Replace this file with an official manual PDF "
    "before using this project for anything real.",
    styles["Disclaimer"]
))
story.append(PageBreak())

# ---------- 1. Safety ----------
story.append(Paragraph("1. Important Safety Information", styles["H1"]))
story.append(Paragraph("Read all instructions before using this appliance. Keep this manual for future reference.", styles["Body"]))
safety_items = [
    "Plug directly into a properly grounded outlet. Do not use an extension cord or a two-prong adapter.",
    "Keep ventilation openings in the appliance enclosure, or in the surrounding cabinetry, clear of obstruction.",
    "Leave at least 5 cm (2 in) of clearance on each side and at the rear, and 30 cm (12 in) above the unit, for airflow around the condenser.",
    "Do not store flammable materials, solvents, or aerosol cans with a flammable propellant in or near the refrigerator.",
    "Disconnect the power supply before cleaning, moving, or servicing the unit.",
    "Keep packaging film and bags away from children and infants to prevent suffocation.",
    "If the power cord is damaged, it must be replaced by the manufacturer, an authorized service agent, or a similarly qualified person.",
    "Do not touch the compressor or rear panel during or shortly after operation; these surfaces can become hot.",
]
story.append(ListFlowable([ListItem(Paragraph(t, styles["Body"])) for t in safety_items], bulletType="bullet"))

# ---------- 2. Parts and Features ----------
story.append(Paragraph("2. Parts and Features", styles["H1"]))
story.append(Paragraph(
    "This model is a French door refrigerator: two side-by-side doors open the upper "
    "refrigerator compartment, with a pull-out freezer drawer below.", styles["Body"]))
parts = [
    "Digital control panel with temperature display (top-right interior wall)",
    "Adjustable tempered-glass shelves",
    "Two humidity-controlled crisper drawers",
    "Gallon-size door bins with a dedicated dairy compartment",
    "Interior LED lighting (top and side panels)",
    "Pull-out freezer drawer with a divider basket",
    "Rear-mounted condenser coil and eco sensor module",
]
story.append(ListFlowable([ListItem(Paragraph(t, styles["Body"])) for t in parts], bulletType="bullet"))

# ---------- 3. Installation ----------
story.append(Paragraph("3. Installation and Setup", styles["H1"]))
story.append(Paragraph("<b>Placement.</b> Choose a level, stable floor location away from direct sunlight, ovens, dishwashers, or radiators. Extreme heat nearby forces the compressor to work harder and increases energy use.", styles["Body"]))
story.append(Paragraph("<b>Letting it settle.</b> If the unit was transported on its side, stand it upright and wait at least 4 hours before plugging it in. This allows refrigerant oil to settle back into the compressor.", styles["Body"]))
story.append(Paragraph("<b>First power-on.</b> Allow 2 to 3 hours for the unit to reach its set temperature before loading food. Running it empty for this period also lets you confirm the door seals and leveling feet are adjusted correctly.", styles["Body"]))
story.append(Paragraph("<b>Leveling.</b> Use the adjustable front feet so the unit tilts back very slightly (about 6 mm / 1/4 in higher at the front). This helps the doors swing shut on their own.", styles["Body"]))

story.append(PageBreak())

# ---------- 4. Control panel ----------
story.append(Paragraph("4. Using the Control Panel", styles["H1"]))
story.append(Paragraph("The control panel has five buttons: Power, Fridge Temp (+/-), Freezer Temp (+/-), and Mode.", styles["Body"]))
story.append(Paragraph("<b>Recommended temperatures:</b> Refrigerator compartment 3-4°C (37-39°F); freezer compartment -18°C (0°F). Colder settings use more energy without meaningfully improving food safety.", styles["Body"]))
story.append(Paragraph("<b>Mode button</b> cycles between four modes:", styles["Body"]))
modes = [
    "<b>Normal</b> — standard day-to-day operation.",
    "<b>Quick Cool</b> — runs the refrigerator compartment compressor at maximum for up to 6 hours, useful right after loading a large amount of warm food. Reverts to Normal automatically.",
    "<b>Quick Freeze</b> — maximizes freezer compartment cooling for up to 24 hours, recommended before adding a large batch of food to freeze. Reverts to Normal automatically.",
    "<b>Vacation</b> — raises the fridge setpoint slightly and reduces defrost frequency to save energy while the unit is used infrequently. The freezer setpoint is not affected.",
]
story.append(ListFlowable([ListItem(Paragraph(t, styles["Body"])) for t in modes], bulletType="bullet"))
story.append(Paragraph("Press and hold Power for 3 seconds to turn cooling off (for cleaning or moving). Press and hold again to resume.", styles["Body"]))

# ---------- 5. Eco sensor ----------
story.append(Paragraph("5. Eco Sensor and Energy Saving", styles["H1"]))
story.append(Paragraph(
    "This model includes an eco sensor module that monitors ambient light and door-usage "
    "frequency. When the room is dark and the unit hasn't been opened for a while (for "
    "example, overnight), it automatically shifts to a lower-power cooling cycle and dims "
    "interior lighting, then returns to normal operation once activity resumes.", styles["Body"]))
story.append(Paragraph("<b>Door-open alarm.</b> A chime sounds if any door is left ajar for more than 60 seconds, repeating every 30 seconds until the door is closed.", styles["Body"]))
story.append(Paragraph("<b>Tips to reduce energy use:</b>", styles["Body"]))
tips = [
    "Keep the fridge about three-quarters full — food adds thermal mass that helps hold temperature steady.",
    "Let hot leftovers cool on the counter for up to 30 minutes before storing.",
    "Check door gaskets periodically; a weak seal is one of the most common causes of higher energy use.",
    "Group items so doors are open for shorter periods.",
]
story.append(ListFlowable([ListItem(Paragraph(t, styles["Body"])) for t in tips], bulletType="bullet"))

story.append(PageBreak())

# ---------- 6. Food storage ----------
story.append(Paragraph("6. Food Storage Guidelines", styles["H1"]))
story.append(Paragraph("Store raw meat, poultry, and fish on the lowest shelf in a covered container so drips can't contaminate other food.", styles["Body"]))
story.append(Paragraph("Use the crisper drawers for fruits and vegetables. Where possible, keep ethylene-producing fruit (apples, bananas, avocados) separate from ethylene-sensitive vegetables (leafy greens, broccoli), since ethylene speeds up spoilage.", styles["Body"]))
story.append(Paragraph("Store dairy and eggs on an interior shelf rather than the door — the door experiences more temperature swings every time it opens.", styles["Body"]))
story.append(Paragraph("The dedicated dairy compartment in the door is designed for butter and spreads, which are less temperature-sensitive than milk or eggs.", styles["Body"]))

# ---------- 7. Cleaning ----------
story.append(Paragraph("7. Cleaning and Maintenance", styles["H1"]))
clean_items = [
    "Wipe interior surfaces with a solution of mild soap and warm water. Avoid abrasive pads or solvent-based cleaners, which can dull the interior finish.",
    "Clean door gaskets with a damp cloth every one to two months; food residue can prevent a full seal.",
    "This model is frost-free and does not require manual defrosting.",
    "Vacuum the condenser coil (accessed from the rear, lower panel) roughly every six months. A dusty coil makes the compressor run longer to reach the same temperature.",
    "If your model has a water filter, replace it every six months or when the filter-status light turns amber.",
]
story.append(ListFlowable([ListItem(Paragraph(t, styles["Body"])) for t in clean_items], bulletType="bullet"))

story.append(PageBreak())

# ---------- 8. Troubleshooting ----------
story.append(Paragraph("8. Troubleshooting", styles["H1"]))
story.append(Paragraph("Try these steps before contacting service.", styles["Body"]))

trouble_data = [
    ["Symptom", "Possible cause", "Suggested action"],
    ["Fridge isn't cooling", "Not fully plugged in; tripped breaker; temperature set too warm", "Check the outlet and breaker; confirm the setpoint; allow up to 24 hours after any change"],
    ["Unusual noise", "Normal compressor/fan operation; or unit not level", "Some humming and clicking is normal. If it's a loud rattle, check the leveling feet and surrounding items touching the cabinet"],
    ["Water pooling inside the fridge", "Drain channel at the back of the interior is blocked", "Clear the drain channel with a pipe cleaner or a mixture of warm water and baking soda"],
    ["Frost buildup in the freezer drawer", "Door not sealing fully, or opened very frequently", "Check the gasket for gaps; minimize how long the drawer stays open"],
    ["Interior light doesn't turn on", "Eco sensor in low-power mode; bulb fault", "Open and close the door fully to wake the sensor; if it still doesn't light, contact service"],
]
t = Table(trouble_data, colWidths=[1.5 * inch, 2.1 * inch, 2.6 * inch])
t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2b3a4a")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f6f8")]),
    ("TOPPADDING", (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ("LEFTPADDING", (0, 0), (-1, -1), 5),
]))
story.append(t)
story.append(Spacer(1, 12))

story.append(Paragraph("<b>Control panel error codes</b>", styles["H2"]))
story.append(Paragraph(
    "Note: these codes are illustrative, written for this sample document only. They do not "
    "correspond to any real Panasonic product. For a real appliance, always use the error "
    "codes listed in its official manual.", styles["Disclaimer"]))
err_data = [
    ["Code", "Meaning", "What to do"],
    ["E1", "Refrigerator compartment temperature sensor fault", "Unplug for 60 seconds, plug back in. If it recurs, contact service."],
    ["E2", "Freezer compartment temperature sensor fault", "Unplug for 60 seconds, plug back in. If it recurs, contact service."],
    ["E3", "Defrost sensor fault", "Contact service; do not attempt to repair the sensor yourself."],
    ["E4", "Communication error between the control board and display", "Power-cycle the unit. If the code returns, contact service."],
    ["E5", "A door has been open for an extended period", "Close the door fully; check that nothing is blocking it."],
]
t2 = Table(err_data, colWidths=[0.7 * inch, 2.7 * inch, 2.8 * inch])
t2.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2b3a4a")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f6f8")]),
    ("TOPPADDING", (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ("LEFTPADDING", (0, 0), (-1, -1), 5),
]))
story.append(t2)

story.append(PageBreak())

# ---------- 9. FAQ ----------
story.append(Paragraph("9. Frequently Asked Questions", styles["H1"]))
faqs = [
    ("Why is my fridge making a clicking noise?",
     "A single click every so often is usually the thermostat or defrost timer switching states, which is normal. Repeated rapid clicking without the compressor starting can mean the compressor is struggling to start and may need service."),
    ("Can I turn off the door-open alarm?",
     "Press and hold the Mode button for 5 seconds to mute the alarm. The chime will re-enable automatically after 24 hours."),
    ("How long can the unit stay unplugged when I'm moving?",
     "Empty and defrosted, it can sit unplugged indefinitely. With food still inside, plan for no more than 4 hours to keep everything at a safe temperature."),
    ("Is it normal for the back or sides of the fridge to feel warm?",
     "Yes. The condenser coil releases heat as part of the cooling cycle, so the rear panel and sometimes the side walls near it will feel warm to the touch. This is expected and not a fault."),
    ("Why did the interior light dim on its own?",
     "That's the eco sensor lowering interior lighting during long periods of inactivity, typically overnight, to save energy. It returns to full brightness as soon as a door opens."),
]
for q, a in faqs:
    story.append(Paragraph(f"<b>Q: {q}</b>", styles["Body"]))
    story.append(Paragraph(f"A: {a}", styles["Body"]))
    story.append(Spacer(1, 4))

story.append(PageBreak())

# ---------- 10. Specs ----------
story.append(Paragraph("10. Specifications", styles["H1"]))
story.append(Paragraph("Illustrative specifications for this sample document (Model RF-2200X):", styles["Body"]))
spec_data = [
    ["Property", "Value"],
    ["Total capacity", "510 liters (18.0 cu ft)"],
    ["Refrigerator compartment", "360 liters (12.7 cu ft)"],
    ["Freezer compartment", "150 liters (5.3 cu ft)"],
    ["Dimensions (H x W x D)", "179 x 90 x 74 cm (70.5 x 35.4 x 29.1 in)"],
    ["Rated voltage / frequency", "220-240V ~ 50 Hz"],
    ["Climate class", "SN-T (10°C to 43°C ambient)"],
    ["Noise level", "39 dB(A)"],
    ["Net weight", "98 kg (216 lb)"],
]
t3 = Table(spec_data, colWidths=[2.6 * inch, 3.6 * inch])
t3.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2b3a4a")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTSIZE", (0, 0), (-1, -1), 9),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f6f8")]),
    ("TOPPADDING", (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ("LEFTPADDING", (0, 0), (-1, -1), 5),
]))
story.append(t3)

doc = SimpleDocTemplate(OUT_PATH, pagesize=LETTER, topMargin=0.75*inch, bottomMargin=0.75*inch,
                         leftMargin=0.75*inch, rightMargin=0.75*inch, title="Refrigerator User Manual (Sample)")
doc.build(story)
print(f"Wrote {OUT_PATH}")
