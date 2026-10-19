#!/usr/bin/env python3
"""Build a gym's GHL landing page from its settings.

    python3 build.py gyms/<gym-folder>
    python3 build.py --all

Reads   gyms/<gym>/gym.json, gyms/<gym>/form-embed.html, gyms/<gym>/<logoFile>
Writes  gyms/<gym>/ghl-paste.html   one block for a GHL Custom JS/HTML element
        gyms/<gym>/copy-page.html   "Copy Everything" page, published as an Artifact
"""
import base64
import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "template" / "landing-template.html"
COPY_TEMPLATE = ROOT / "template" / "copy-page-template.html"
LOGO_HEIGHT_PX = 120  # displayed at 44-48px, 2x+ for sharp screens
DEFAULT_FORM_HEIGHT = 420


def js(value):
    return json.dumps(value, ensure_ascii=False)


def config_block(g):
    """The GYM CONFIG block, with comments, as it appears in the pasted code."""
    c = g["colors"]
    bullets = ",\n".join(f"    {js(b)}" for b in g["trustBullets"])
    steps = ",\n".join(
        f"    {{ title: {js(s['title'])}, text: {js(s['text'])} }}" for s in g["steps"]
    )
    return f"""/* ===================================================================
   GYM CONFIG  >>>  EDIT THIS BLOCK FOR EACH GYM  <<<
   =================================================================== */
var CONFIG = {{

  /* ---------- Basics ---------- */
  gymName:  {js(g["gymName"])},
  city:     {js(g["city"])},
  /* Logo shown in the top bar instead of the gym name.
     Leave "" to use the logo embedded in this file.
     Or paste an image URL here (e.g. from the GHL media library). */
  logoUrl:  {js(g.get("logoUrl", ""))},
  /* Privacy policy link at the bottom of the page (opens in a new tab).
     Use the page's path or full URL. Leave "" to hide it. */
  privacyUrl: {js(g.get("privacyUrl", ""))},

  /* ---------- Colors (one accent only) ---------- */
  colors: {{
    accent:     {js(c["accent"])},  // buttons, highlights, step numbers
    accentText: {js(c["accentText"])},  // text that sits on top of the accent color
    dark:       {js(c["dark"])},  // hero + top bar background
    light:      {js(c["light"])},  // light section background
    ink:        {js(c["ink"])}   // main text on light sections
  }},

  /* ---------- Buttons ---------- */
  ctaText:      {js(g["ctaText"])},
  topBarCta:    {js(g["topBarCta"])},

  /* ---------- Hero (match the Google ad's headline) ---------- */
  eyebrow:   {js(g["eyebrow"])},
  headline:  {js(g["headline"])},
  subhead:   {js(g["subhead"])},
  trustBullets: [
{bullets}
  ],
  /* Heading above the form. Leave both "" to hide them
     (use this when the GHL form has its own heading). */
  formHeading: {js(g.get("formHeading", ""))},
  formSubtext: {js(g.get("formSubtext", ""))},

  /* ---------- How it works ---------- */
  stepsHeading: {js(g["stepsHeading"])},
  steps: [
{steps}
  ],

  /* ---------- Final CTA ---------- */
  finalHeadline: {js(g["finalHeadline"])},
  finalSubtext:  {js(g["finalSubtext"])}
}};
/* ===================== END GYM CONFIG ===================== */"""


def logo_src(gym_dir, g):
    """Embed the logo as a data URI, resized so the paste stays small."""
    path = gym_dir / g["logoFile"]
    data = path.read_bytes()
    try:
        from PIL import Image
    except ImportError:
        Image = None
    if Image:
        im = Image.open(io.BytesIO(data))
        if im.height > LOGO_HEIGHT_PX:
            w = round(im.width * LOGO_HEIGHT_PX / im.height)
            im = im.resize((w, LOGO_HEIGHT_PX), Image.LANCZOS)
            buf = io.BytesIO()
            if im.mode in ("RGBA", "LA", "P"):
                im.save(buf, "PNG", optimize=True)
                return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
            im.convert("RGB").save(buf, "JPEG", quality=88, optimize=True)
            return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    ext = path.suffix.lower().lstrip(".")
    mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "svg": "svg+xml", "webp": "webp"}[ext]
    return f"data:image/{mime};base64," + base64.b64encode(data).decode()


def form_embed(gym_dir):
    path = gym_dir / "form-embed.html"
    if not path.exists():
        return '<div class="ghl-placeholder">GHL-FORM-EMBED<br>Paste GoHighLevel form embed code here</div>', DEFAULT_FORM_HEIGHT
    code = path.read_text().strip()
    m = re.search(r'data-height="(\d+)"', code)
    return code, int(m.group(1)) if m else DEFAULT_FORM_HEIGHT


def build(gym_dir):
    gym_dir = Path(gym_dir).resolve()
    g = json.loads((gym_dir / "gym.json").read_text())
    embed, height = form_embed(gym_dir)
    page = TEMPLATE.read_text()
    for token, value in [
        ("{{GYM_NAME}}", g["gymName"]),
        ("{{CONFIG}}", config_block(g)),
        ("{{LOGO_SRC}}", logo_src(gym_dir, g)),
        ("{{FORM_EMBED}}", embed),
        ("{{FORM_HEIGHT}}", str(height)),
    ]:
        assert page.count(token) == 1, f"template token {token} missing or repeated"
        page = page.replace(token, value)
    (gym_dir / "ghl-paste.html").write_text(page)

    payload = json.dumps({"all": page}).replace("</", "<\\/")
    copy = COPY_TEMPLATE.read_text().replace("{{GYM_NAME}}", g["gymName"]).replace("{{PAYLOAD}}", payload)
    (gym_dir / "copy-page.html").write_text(copy)
    print(f"built {gym_dir.name}: ghl-paste.html ({len(page):,} chars), copy-page.html")


if __name__ == "__main__":
    if sys.argv[1:] == ["--all"]:
        for d in sorted((ROOT / "gyms").iterdir()):
            if (d / "gym.json").exists():
                build(d)
    elif len(sys.argv) == 2:
        build(sys.argv[1])
    else:
        sys.exit(__doc__)
