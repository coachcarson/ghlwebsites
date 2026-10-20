# GHL gym landing pages

Single-purpose Google Ads landing pages for gyms, pasted into GoHighLevel (GHL) websites.
Owner: Ryan (gym marketing / coaching). Talk to him like an operator: direct, short, no fluff,
**no em dashes** in anything he will read or paste. Give exact clicks and exact wording.

## Layout (approved, keep it)

Marketer (Brittany) signed off on a minimal page. Do not add sections back without being asked.

1. Top bar: logo + CTA button (jumps to form)
2. Hero: eyebrow (city), headline, short subhead, 3 trust bullets, GHL form in a white card
3. How It Works: 3 steps
4. Final CTA band + small Privacy Policy link (opens in new tab)

No nav, no footer links, no exits. The form is the only action.
Removed on purpose: "More Than a Workout", testimonials, FAQ.

**Thank-you page** (form redirects here on submit), same styling/logo/colors:
logo-only top bar, check + "You're in" + headline + "watch your phone" subhead,
What Happens Next (3 steps), Where To Find Us (address, optional phone) + Privacy link.
Copy defaults live in `DEFAULT_THANK_YOU` in build.py; override per gym with a
`thankYou` object in gym.json (do this when the offer is not a free class).

## Repo map

```
build.py                          builds a gym: python3 build.py gyms/<gym>   (or --all)
template/landing-template.html    the page (CSS + HTML + JS) with {{TOKENS}}
template/thank-you-template.html  thank-you page; build injects the landing page's <style>
template/copy-page-template.html  the copy helper page (both pages)
gyms/<gym>/gym.json               all text, colors, offer, domain, path, SEO, notes
gyms/<gym>/form-embed.html        that gym's GHL inline form embed (iframe + script)
gyms/<gym>/logo.(png|jpg)         logo; build resizes to 120px tall and embeds it
gyms/<gym>/ghl-paste.html         OUTPUT: landing page block for a GHL Custom JS/HTML element
gyms/<gym>/thank-you-paste.html   OUTPUT: thank-you page block
gyms/<gym>/copy-page.html         OUTPUT: published as an Artifact, Copy buttons for both
INTAKE.md                         what Ryan sends per gym
```

Change the layout or styling in `template/landing-template.html`, then `python3 build.py --all`.
Change a gym's words/colors/offer in its `gym.json`, then rebuild that gym.

## New gym, step by step

1. Ryan sends the INTAKE.md answers, logo image, and the GHL form embed code.
2. Make `gyms/<kebab-name>/`: write `gym.json` (copy crossfit-east-coast as the base),
   save `form-embed.html` exactly as pasted, save the logo.
3. Copy rules: headline must match the Google ad ("free class" ad -> headline says free class).
   `*word*` turns a word accent-colored. `{city}` / `{gym}` tokens work in any text.
   Short subhead (1 line). Bullets under ~40 chars. Never invent testimonials, stats or claims;
   only use what Ryan gives. Offer limits ("first 20") only if real.
4. Colors: `accent` = buttons and form card edge. Optional `accent2` = highlight words, eyebrow,
   hero check marks, step numbers, stripes; use it when the brand has two colors
   (RAW: green accent + blue accent2). Blank accent2 = one-color look.
   Optional `band` + `bandInk`: solid color behind How It Works / What Happens Next and the
   heading color on it (RAW: band #00AFEE, bandInk #000000). Use when the owner wants more brand color.
   accentText must be readable on accent (white on bright green/blue fails; use black/dark).
   dark = hero/top bar/final band, light = section bg when no band.
   Per-gym look options in gym.json (all optional, defaults = CrossFit East Coast look):
   - `fonts`: {display, displayWeights, body, bodyWeights, headingWeight} Google Fonts names.
     Heavy display faces (Kanit) look best with headingWeight "800", not 900.
   - `topBar`: "light" for logos made for white backgrounds (keeps the dark hero).
   - `logoHeight`: px, for wide logos (RAW = 52).
   Thank-you page hides "Where To Find Us" when `address` is "".
5. `python3 build.py gyms/<gym>`, render-check it (see Testing), then publish
   `gyms/<gym>/copy-page.html` with the Artifact tool (new artifact per gym) and save the
   URL to `copyPageUrl` in gym.json. Commit + push.
6. Send Ryan the copy page link + the GHL steps below + the gym's SEO title/description.

## GHL paste steps (what Ryan does)

1. New page on the gym's GHL website (not over the home page). One section, one 1-column row,
   one **Custom JS/HTML** element. Section/row/column padding and margin 0.
2. Open the element's code editor, Ctrl/Cmd+A, delete, paste Copy Everything. Save element AND page.
3. Delete template header/footer sections from this page only (global sections: "this page only").
4. Page settings: path (e.g. `braintree-free-class`), SEO title + meta description.
5. Thank-you page: second page on the same website (path like `free-class-thank-you`), same
   one-element setup, paste Copy Thank You Page. Then in the GHL form: On Submit > Redirect to
   URL > the full thank-you URL. Put the Google Ads conversion on the thank-you page load.
6. Preview (the builder canvas may look blank, that is normal), then Publish, then test on a phone:
   submit the form and confirm it lands on the thank-you page.
Nothing goes in GHL's Custom CSS box; the block carries its own CSS.

## GHL lessons learned (do not relearn these)

- **Embedded forms stack one field per row.** The inline embed renders in an iframe and uses its
  *mobile* layout at card width (~530-580px). Desktop "Two Column" does not apply and GHL forms
  only have Desktop/Mobile column settings (no tablet). The built-in Form element (used on other
  pages) is two-column because it sees the full window, but it cannot live inside the code block.
  Fix = shorter form, not wider card: First Name, Phone, Email, SMS consent, button.
- **Form height:** `data-height` in the embed sets the iframe's min-height in our CSS. If Ryan
  shortens the form, take the new embed (new data-height) and rebuild, or there is white space.
- **`data-height="undefined"`** sometimes comes in the embed. GHL's script still resizes the
  form live; set `formHeight` in gym.json (estimate ~85px per stacked field + consent + button)
  so the card is not cut off before it does.
- **Form has its own heading?** Set `formHeading`/`formSubtext` to "" so the page's heading hides
  and the card drops its padding (no double heading, no double padding).
- **Form edits in GHL show up live**; only re-paste when the embed code itself changes.
- **Paths:** GHL appends numbers (`free-class-1`) when a path is taken anywhere on the domain,
  including other funnels/websites/old cloned pages. Pick a unique path like `<city>-free-class`.
- **Cloned pages** get paths like `home-380940`; always set the path.
- **Template SEO** often still says "Fitness Classes in CITY, STATE | GYM NAME". Fix home + page.
- **Privacy policy is required** (A2P 10DLC texting registration + Google Ads). Must include:
  "No mobile information will be shared with third parties or affiliates for marketing or
  promotional purposes. Text messaging originator opt-in data and consent will not be shared with
  any third parties." Form needs an SMS consent checkbox. Link lives at `privacyUrl`.
- The pasted block scopes all CSS under `#fcl` and breaks out to full width (100vw), so GHL theme
  styles do not leak in. If the top bar will not stick, a parent section has overflow hidden.
- Earlier attempt with separate Custom CSS box + HTML element failed (CSS did not apply).
  One all-in-one block is the method.

## Testing

- `python3 build.py gyms/<gym>` asserts every template token is filled.
- Render with Playwright: `NODE_PATH=$(npm root -g) node script.js`, wrap ghl-paste.html in a
  basic page, check no page errors, no horizontal scroll at 390px and 1280px, screenshot.
- GHL form URLs are blocked from this sandbox, so the form card renders empty in tests.
  Ryan's GHL Preview is the real check for the form.

## Gyms

| Gym | Folder | Domain | Copy page |
|---|---|---|---|
| CrossFit East Coast (Braintree, MA) | gyms/crossfit-east-coast | crossfit-eastcoast.com/free-crossfit-class | https://claude.ai/artifact/1pCLeFwRrKSbY543f9pq9C |
| RAW Fitness (Washington Township, MI) | gyms/raw-fitness | madeatrawfitness.com (draft, no form yet) | https://claude.ai/artifact/CQhQzEn3KVdLURxpw7Uvf7 |
