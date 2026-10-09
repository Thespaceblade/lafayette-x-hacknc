# Vigil design guide

Taken from the pitch slide so the app matches it. Source of truth for the values is `docs/vigil-tokens.css`. Logo file: `docs/vigil-logo.svg`.

Anything marked (suggestion) is not on the slide and is our own extension.

## Theme
Dark "night" theme: deep navy background, warm amber accent, ivory text. One accent color. Amber marks Vigil itself, our numbers and anything that matters most. Muted blue marks the other approach or a baseline. Cards are rounded and flat, with a thin border and no shadows. The tone of the copy is plain and short, with no jargon.

## Font
One typeface: **DM Sans** (Google Fonts), weights 400, 500 and 700. Fallback `Arial, sans-serif`.

```
https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap
```

Weights in use: 700 for the name, headings, big numbers and bar labels, 400 for body text. 500 is loaded and unused.

## Type scale on the slide (1920 by 1080 canvas)
| Use | Size | Weight | Line height | Color |
|---|---|---|---|---|
| Product name | 72px | 700 | 1.1 | ivory |
| Hero numbers ("Seconds", "67%") | 72px | 700 | 1.1 | navy on amber |
| Step titles | 34px | 700 | normal | ivory, step number in amber |
| Strip title | 30px | 700 | normal | amber |
| Bar labels and hero captions | 26px | 700 or 400 | 1.4 | varies |
| Body and small labels | 24px | 400 | 1.4 | mist |

(suggestion) For the app, scale the slide sizes by about 0.5: name 36px, headings 17 to 20px, body 14 to 16px. Keep the 1.1 and 1.4 line heights.

## Colors
| Token | Hex | Used for | Contrast |
|---|---|---|---|
| navy | `#14213D` | page background, text on amber | ivory on navy 14.2, amber on navy 8.9 |
| panel | `#1D2E52` | cards and panels | mist on panel 8.8, amber on panel 7.5 |
| border | `#2E4272` | 1px card border | |
| bar | `#3B4F7F` | neutral bars, the other approach | ivory on bar 7.1 |
| amber | `#F2B84B` | logo, icons, hero panels, our bars and numbers, highlight border | navy on amber 8.9 |
| ivory | `#F4F1EA` | primary text on dark | |
| mist | `#C9D1E3` | secondary text on dark | mist on navy 10.4 |

All text pairs above pass WCAG AA (4.5:1) and most pass AAA (7:1). Contrast ratios were computed from the hex values.

## Shape and spacing
- Cards: radius 24px, 1px solid border, padding 24px (28px on hero and bar panels).
- Highlight card: same, with an amber border.
- Hero panel: solid amber fill, navy text, radius 24px, padding 28px.
- Bars: height 44px, radius 10px. Thin marker bars are 12px wide, radius 6px.
- Gaps: 12px between stacked step cards, 20px between panels, 32px between major columns and sections.
- Slide margins: 112px top and bottom, 128px left and right.

## Icons
Four amber icons at 56px: Chat, Lightning, PaperPlane, Users (from the slide editor's built-in set). (suggestion) In the app, use Lucide equivalents: `message-square`, `zap`, `send`, `users`, stroke in amber.

## Logo
A crescent moon and a small star in navy on an amber rounded square (corner radius about 23% of the width). The file is `docs/vigil-logo.svg`.
- Minimum size 32px.
- Keep clear space of about a quarter of the logo width on every side.
- On dark backgrounds, use the logo as is. The amber square carries it.
- Do not recolor the crescent or change the corner radius.

## Applying it to the supervision screen (suggestion)
Not on the slide. Decision and priority badges can use these, all readable on both navy and panel:
| State | Color |
|---|---|
| Emergency | coral `#FF7A6B` (contrast 6.3 on navy, 5.3 on panel) |
| Urgent | amber `#F2B84B` |
| Routine | mist `#C9D1E3` on a `bar` fill |
| Needs a person | ivory outline, no fill |

Also show the classifier's confidence next to each decision. Anything below the cutoff gets the "Needs a person" badge and the reason on the same card.

## Voice
Short sentences. Plain verbs: arrives, sorted, drafted, approved. Always say a person acts. Numbers that are estimates say "estimate".
