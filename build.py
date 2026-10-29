#!/usr/bin/env python3
"""Build a gym's GHL landing page from its settings.

    python3 build.py gyms/<gym-folder>
    python3 build.py --all

Reads   gyms/<gym>/gym.json, gyms/<gym>/form-embed.html, gyms/<gym>/<logoFile>
Writes  gyms/<gym>/ghl-paste.html        landing page block for a GHL Custom JS/HTML element
        gyms/<gym>/thank-you-paste.html  thank-you page block (form redirects here)
        gyms/<gym>/copy-page.html        "Copy" page for both, published as an Artifact
"""
import base64
import io
import json
import re
import sys
from urllib.parse import quote
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "template" / "landing-template.html"
COPY_TEMPLATE = ROOT / "template" / "copy-page-template.html"
THANKS_TEMPLATE = ROOT / "template" / "thank-you-template.html"
LOGO_HEIGHT_PX = 120  # displayed at 44-48px, 2x+ for sharp screens
DEFAULT_FORM_HEIGHT = 420

# Thank-you page copy. Override any key with a "thankYou" object in gym.json
# (e.g. a different headline when the offer isn't a free class).
DEFAULT_THANK_YOU = {
    "eyebrow": "You're in",
    "headline": "Your *Free Class* Is Claimed",
    "subhead": "Keep an eye on your phone. A coach from {gym} will text you shortly to pick your class time.",
    "stepsHeading": "What Happens Next",
    "steps": [
        {"title": "Watch for our text", "text": "A coach will text you to find a class time that fits your schedule."},
        {"title": "Pick your time", "text": "Reply with the day and time that work best. That locks in your spot."},
        {"title": "Show up ready", "text": "Wear comfortable workout clothes and sneakers, bring water, and get there a few minutes early to meet your coach."},
    ],
    "locationHeading": "Where To Find Us",
}


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;").replace("'", "&#39;"))


def text(s, g):
    """Escape, then swap {gym} / {city} for the gym's name and city."""
    return esc(s).replace("{gym}", esc(g["gymName"])).replace("{city}", esc(g["city"]))


def accent(s, g):
    """Like text(), plus *word* -> accent-colored span."""
    return re.sub(r"\*(.+?)\*", r'<span class="accent">\1</span>', text(s, g))


def font_link(g):
    """Google Fonts stylesheet, in the HTML so it starts loading right away."""
    f = g.get("fonts", {})
    fams = []
    if f.get("display"):
        fams.append(f"family={f['display'].replace(' ', '+')}:wght@{f.get('displayWeights', '700;800;900')}")
    if f.get("body"):
        fams.append(f"family={f['body'].replace(' ', '+')}:wght@{f.get('bodyWeights', '400;700')}")
    if not fams:
        return ""
    return f'<link rel="stylesheet" href="https://fonts.googleapis.com/css2?{"&amp;".join(fams)}&amp;display=swap">'


def gym_css(g):
    """This gym's colors, fonts and sizes as CSS, appended to the stylesheet."""
    c, f = g["colors"], g.get("fonts", {})
    v = {
        "--accent": c["accent"], "--accent-text": c["accentText"],
        "--dark": c["dark"], "--light": c["light"], "--ink": c["ink"],
    }
    if c.get("accent2"):
        v["--accent2"] = c["accent2"]
    if g.get("headlineSize"):
        v["--h1-desk"] = f"{g['headlineSize']}px"
    if c.get("stepNum"):
        v["--step-num"] = c["stepNum"]
    if c.get("checkInk"):
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{c["checkInk"]}" '
               'stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>')
        v["--check-img"] = f'url("data:image/svg+xml,{quote(svg, safe="")}")'
    if c.get("band"):
        v["--band"] = c["band"]
        v["--band-ink"] = v["--band-bar"] = c.get("bandInk") or c["ink"]
    if f.get("display"):
        first = f'"{f["displayFirst"]}", ' if f.get("displayFirst") else ""
        v["--font-display"] = f'{first}"{f["display"]}", var(--font-base)'
    if f.get("body"):
        v["--font"] = f'"{f["body"]}", var(--font-base)'
    if g.get("topBarStripe"):
        v["--topbar-stripe"] = g["topBarStripe"]
    crop = g.get("formCrop", {})
    if any(crop.get(k) for k in ("top", "bottom", "sides")):
        v["--crop-top"] = f"{crop.get('top', 0)}px"
        v["--crop-bottom"] = f"{crop.get('bottom', 0)}px"
        v["--crop-x"] = f"{crop.get('sides', 0)}px"
    if f.get("headingWeight"):
        v["--display-weight"] = v["--btn-weight"] = f["headingWeight"]
    css = "#fcl {\n" + "".join(f"  {k}: {val};\n" for k, val in v.items()) + "}"
    if g.get("logoHeight"):
        # Tall logos: grow the bar so the logo (and the optional stripe) never clip
        css += (f"\n#fcl .brand-logo {{ height: {g['logoHeight']}px; }}"
                f"\n#fcl .topbar .wrap {{ height: {g['logoHeight'] + 18}px; }}")
    return css


def fcl_classes(g):
    f = g.get("fonts", {})
    return " ".join(cls for cls, on in [
        ("topbar-light", g.get("topBar") == "light"),
        ("light-theme", g.get("theme") == "light"),
        ("condensed", f.get("condensed")),
        ("form-crop", any(g.get("formCrop", {}).get(k) for k in ("top", "bottom", "sides"))),
    ] if on)


def steps_html(steps, g):
    return "".join(f'<div class="step"><div class="num">0{n}</div><h3>{text(s["title"], g)}</h3>'
                   f'<p>{text(s["text"], g)}</p></div>' for n, s in enumerate(steps, 1))


def render(page, g, slots, lists):
    """Write every text slot into the HTML, so the page arrives complete (no script needed)."""
    def slot(m):
        tag, attrs, key, acc = m.groups()
        val = slots[key]
        return f"<{tag}{attrs}>{accent(val, g) if acc else text(val, g)}</{tag}>"
    page = re.sub(r'<(\w+)([^>]*?) data-c="(\w+)"( data-accent)?></\1>', slot, page)
    assert "data-c=" not in page, "unfilled text slot"
    for el_id, html in lists.items():
        page = re.sub(rf'(id="{el_id}"[^>]*>)(</)', lambda m: m.group(1) + html + m.group(2), page, count=1)
    page = page.replace('<div id="fcl">', f'<div id="fcl" class="{fcl_classes(g)}">' if fcl_classes(g) else '<div id="fcl">', 1)
    page = page.replace('alt=""', f'alt="{esc(g["gymName"])} logo"', 1)
    if g.get("logoUrl"):
        page = re.sub(r'(id="logo"[^>]*?src=")[^"]*', lambda m: m.group(1) + esc(g["logoUrl"]), page, count=1)
    if g.get("privacyUrl"):
        page = page.replace('href="/privacy-policy"', f'href="{esc(g["privacyUrl"])}"', 1)
    else:
        page = page.replace('<p class="legal"><a id="privacy-link"', '<p class="legal" hidden><a id="privacy-link"', 1)
    return page


def strip_comments(page):
    """Drop HTML and CSS comments: shorter paste, and nothing for scanners to flag."""
    page = re.sub(r"<!--.*?-->", "", page, flags=re.S)
    page = re.sub(r"(<style>)(.*?)(</style>)",
                  lambda m: m.group(1) + re.sub(r"/\*.*?\*/", "", m.group(2), flags=re.S) + m.group(3),
                  page, flags=re.S)
    page = re.sub(r"[ \t]+\n", "\n", page)
    return re.sub(r"\n{2,}", "\n", page).strip() + "\n"


def fill_tokens(page, pairs):
    for token, value in pairs:
        assert page.count(token) == 1, f"template token {token} missing or repeated"
        page = page.replace(token, value)
    return page


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
    height = g.get("formHeight") or height  # override when the embed has no usable data-height
    logo = logo_src(gym_dir, g)
    fonts, css = font_link(g), gym_css(g)
    landing = fill_tokens(TEMPLATE.read_text(), [
        ("{{FONT_LINK}}", fonts),
        ("{{FORM_HEIGHT}}", str(height)),
        ("{{LOGO_SRC}}", logo),
    ])
    # Thank-you page reuses the landing page's stylesheet so the two always match
    style = re.search(r"<style>\n(.*?)\n\{\{GYM_CSS\}\}", landing, re.S).group(1)
    landing = fill_tokens(landing, [("{{GYM_CSS}}", css)])
    keys = ["topBarCta", "eyebrow", "headline", "subhead", "formHeading", "formSubtext",
            "stepsHeading", "finalHeadline", "finalSubtext", "ctaText"]
    page = render(landing, g, {k: g.get(k, "") for k in keys}, {
        "trust": "".join(f"<li>{text(b, g)}</li>" for b in g["trustBullets"]),
        "steps": steps_html(g["steps"], g),
    })
    # The form embed goes in last, untouched (it is GHL's code, not ours)
    page = fill_tokens(strip_comments(page), [("{{FORM_EMBED}}", embed)])
    (gym_dir / "ghl-paste.html").write_text(page)

    t = {**DEFAULT_THANK_YOU, **g.get("thankYou", {})}
    thanks = fill_tokens(THANKS_TEMPLATE.read_text(), [
        ("{{FONT_LINK}}", fonts),
        ("{{STYLE}}", style),
        ("{{GYM_CSS}}", css),
        ("{{LOGO_SRC}}", logo),
    ])
    slots = {k: t[k] for k in ["eyebrow", "headline", "subhead", "stepsHeading", "locationHeading"]}
    slots["address"] = g.get("address", "")
    contact = ""
    if g.get("phone"):
        # Plain number, tap to call on phones
        contact = (f'Questions? Call or text <a href="tel:{esc(re.sub(r"[^0-9+]", "", g["phone"]))}">'
                   f'{esc(g["phone"])}</a>')
    thanks = render(thanks, g, slots, {"steps": steps_html(t["steps"], g), "contact": contact})
    if not g.get("address"):
        thanks = thanks.replace('<section class="final">', '<section class="final" hidden>', 1)  # no location band
    thanks = strip_comments(thanks)
    assert "{{" not in page.replace(embed, "") and "{{" not in thanks, "unfilled template token"
    (gym_dir / "thank-you-paste.html").write_text(thanks)

    payload = json.dumps({"all": page, "thanks": thanks}).replace("</", "<\\/")
    copy = (COPY_TEMPLATE.read_text().replace("{{GYM_NAME}}", g["gymName"])
            .replace("{{THANKS_PATH}}", g.get("thankYouPath", "free-class-thank-you"))
            .replace("{{PAYLOAD}}", payload))
    (gym_dir / "copy-page.html").write_text(copy)
    print(f"built {gym_dir.name}: ghl-paste.html ({len(page):,} chars), "
          f"thank-you-paste.html ({len(thanks):,} chars), copy-page.html")


if __name__ == "__main__":
    if sys.argv[1:] == ["--all"]:
        for d in sorted((ROOT / "gyms").iterdir()):
            if (d / "gym.json").exists():
                build(d)
    elif len(sys.argv) == 2:
        build(sys.argv[1])
    else:
        sys.exit(__doc__)
