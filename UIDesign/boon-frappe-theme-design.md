# boon — Frappe Website Theme UI Design Spec

> Complete field-by-field specification for the Frappe Website Theme DocType, mapped to the boon brand identity. Copy values directly into the Website Theme form.

---

## Theme

**Field:** `theme`

```
boon — Crimson & Charcoal
```

---

## Google Font

**Field:** `google_font`

```
DM Sans
```

> DM Sans is the body font. The display font (Space Grotesk) and mono font (Space Mono) are loaded via `@import` in Custom Overrides since Frappe's built-in field only supports one font.

---

## Font Size

**Field:** `font_size`

```
1rem
```

> Maps to 16px base. Body text renders at 15–16px per brand spec. All other sizes scale relative to this base.

---

## Font Properties

**Field:** `font_properties`

```json
{
  "font_family": "'DM Sans', sans-serif",
  "font_weight": 400,
  "line_height": 1.7
}
```

| Role | Font | Weight | Size | Line Height | Letterspacing |
|------|------|--------|------|-------------|---------------|
| Body text | DM Sans | 400 | 15–16px | 1.7 | 0 |
| Buttons | DM Sans | 500 | 14–16px | 1 | 0 |
| Bold emphasis | DM Sans | 600 | Inherit | Inherit | 0 |
| Headlines | Space Grotesk | 700 | 28–72px | 1.2 | +0.02em |
| Sub-headlines | Space Grotesk | 500 | 20–24px | 1.3 | 0 |
| Nav / UI labels | Space Grotesk | 600 | 14–16px | 1.2 | +0.02em |
| Data / specs | Space Mono | 400 | 12–14px | 1.5 | 0 |
| Tags / labels | Space Mono | 400 | 9–10px | 1.4 | +0.15em (caps) |

---

## Button Rounded Corners

**Field:** `button_rounded_corners`

```
Yes
```

> Radius: `8px` (0.5rem). Matches boon spacing system. Not pill-shaped — intentionally geometric.

---

## Button Shadows

**Field:** `button_shadows`

```
No
```

> boon uses flat, high-contrast design. No box-shadows on buttons. Hover state is a color shift, not an elevation change.

---

## Button Gradients

**Field:** `button_gradients`

```
No
```

> Solid fills only. Crimson `#C8302B` primary, transparent secondary. No gradients anywhere in the brand system.

---

## Primary Color

**Field:** `primary_color`

```
#C8302B
```

> Crimson — the hero accent. Used for: wordmark, primary CTA buttons, active states, key data highlights. Max 10% of any layout.

---

## Text Color

**Field:** `text_color`

```
#1A1A1A
```

> Charcoal — primary text on light backgrounds. Never pure black `#000000`.

---

## Light Color

**Field:** `light_color`

```
#F2EEEA
```

> Cream — the default background canvas. Never pure white `#FFFFFF`. All light-mode pages use this.

---

## Dark Color

**Field:** `dark_color`

```
#0A0A0A
```

> Void Black — for dark-mode hero sections, packaging context, and social media layouts. Not the default; used sparingly.

---

## Background Color

**Field:** `background_color`

```
#F2EEEA
```

> Same as Light Color (Cream). This is the page canvas. Light-first is the boon default.

---

## Custom Overrides

**Field:** `custom_overrides`

> These SCSS variables are compiled **before** app theme files. They override Bootstrap 4 defaults and propagate through all downstream SCSS.

> **Important:** Custom Overrides only accepts bare `$variable: value;` declarations. No `@import`, no comments, no selectors. Google Fonts `@import` goes in Custom SCSS instead.

```scss
$primary: #C8302B;
$secondary: #8A8178;
$success: #2D6A4F;
$danger: #C8302B;
$warning: #B8860B;
$info: #8A8178;
$light: #F2EEEA;
$dark: #0A0A0A;
$body-bg: #F2EEEA;
$body-color: #1A1A1A;
$font-family-base: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif;
$font-family-monospace: 'Space Mono', SFMono-Regular, Menlo, monospace;
$font-size-base: 1rem;
$font-weight-base: 400;
$line-height-base: 1.7;
$headings-font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif;
$headings-font-weight: 700;
$headings-color: #1A1A1A;
$spacer: 1rem;
$border-radius: 0.5rem;
$border-radius-lg: 0.75rem;
$border-radius-sm: 0.25rem;
$border-color: #D8D2CA;
$btn-padding-y: 0.625rem;
$btn-padding-x: 1.5rem;
$btn-border-radius: 0.5rem;
$btn-font-weight: 500;
$link-color: #C8302B;
$link-hover-color: #A52722;
```

---

## Custom SCSS

**Field:** `custom_scss`

> Compiled **after** app theme files. Has access to all variables defined in Custom Overrides. This is where layout, component, and page-level styles go.

```scss
// ============================================================
// boon — Custom SCSS
// Component overrides, navbar, footer, hero, page-specific
// ============================================================

// --- Google Fonts (3-font system) ---
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=DM+Sans:wght@400;500;600;700&family=Space+Mono:wght@400;700&display=swap');

// --- Global ---
* {
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

::selection {
  background-color: rgba(200, 48, 43, 0.15);  // Crimson tint
  color: #1A1A1A;
}

// --- Headings ---
h1, h2, h3, h4, h5, h6 {
  font-family: 'Space Grotesk', sans-serif;
  font-weight: 700;
  color: #1A1A1A;
}

h1 {
  font-size: 3rem;          // 48px
  letter-spacing: 0.02em;
  line-height: 1.15;
}

h2 {
  font-size: 2rem;          // 32px
  letter-spacing: 0.01em;
  line-height: 1.2;
}

h3 {
  font-size: 1.5rem;        // 24px
  font-weight: 500;
  line-height: 1.3;
}

// --- Wordmark ---
.boon-wordmark,
.navbar-brand {
  font-family: 'Space Grotesk', sans-serif;
  font-weight: 700;
  text-transform: lowercase;
  letter-spacing: 0.15em;
  color: #C8302B !important;  // Crimson always
}

// --- Mono / Data ---
.data-point,
.stat,
code,
pre,
kbd {
  font-family: 'Space Mono', monospace;
}

// --- Primary Buttons ---
.btn-primary {
  background-color: #C8302B;
  border-color: #C8302B;
  color: #F2EEEA;
  font-family: 'DM Sans', sans-serif;
  font-weight: 500;
  border-radius: 8px;
  padding: 0.625rem 1.5rem;
  transition: background-color 0.2s ease, border-color 0.2s ease;

  &:hover,
  &:focus {
    background-color: #A52722;  // Crimson Hover
    border-color: #A52722;
    color: #F2EEEA;
    box-shadow: none;
  }

  &:active {
    background-color: #8C201C;
    border-color: #8C201C;
  }
}

// --- Secondary / Outline Buttons ---
.btn-outline-primary,
.btn-secondary,
.btn-default,
.btn-outline-secondary {
  background-color: transparent;
  color: #1A1A1A;
  border: 1px solid #1A1A1A;
  font-family: 'DM Sans', sans-serif;
  font-weight: 500;
  border-radius: 8px;
  padding: 0.625rem 1.5rem;
  transition: all 0.2s ease;

  &:hover,
  &:focus {
    background-color: #1A1A1A;
    color: #F2EEEA;
    border-color: #1A1A1A;
    box-shadow: none;
  }
}

// --- Ghost / Link Buttons ---
.btn-link {
  color: #C8302B;
  font-weight: 500;
  text-decoration: none;

  &:hover {
    color: #A52722;
    text-decoration: none;
  }
}

// --- Navbar ---
.navbar-main {
  background-color: #F2EEEA;        // Cream (light-first)
  border-bottom: 1px solid #D8D2CA; // Light Border
  padding: 1rem 0;
  box-shadow: none;

  .navbar-brand {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 1.5rem;
    letter-spacing: 0.15em;
    text-transform: lowercase;
    color: #C8302B !important;       // Crimson wordmark
  }

  .nav-link {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    font-size: 0.875rem;             // 14px
    letter-spacing: 0.02em;
    color: #1A1A1A;
    transition: color 0.2s ease;

    &:hover {
      color: #C8302B;               // Crimson on hover
    }

    &.active {
      color: #C8302B;
      font-weight: 700;
    }
  }

  .dropdown-menu {
    background-color: #FFFFFF;
    border: 1px solid #D8D2CA;
    border-radius: 12px;
    box-shadow: 0 4px 16px rgba(26, 26, 26, 0.08);
  }
}

// --- Footer ---
.web-footer {
  background-color: #0A0A0A;        // Void Black
  color: #F2EEEA;                   // Cream text
  padding: 4rem 0 2rem;
  margin-top: 5rem;

  h5, h6 {
    color: #F2EEEA;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    margin-bottom: 1.5rem;
  }

  p, span {
    color: #8A8178;                  // Warm Gray for body
  }

  a {
    color: #F2EEEA;
    text-decoration: none;
    transition: color 0.2s ease;

    &:hover {
      color: #C8302B;               // Crimson on hover
    }
  }

  .footer-brand,
  .boon-wordmark {
    color: #C8302B !important;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: lowercase;
  }
}

// --- Hero Sections (dark context) ---
.hero-section,
.section-dark,
[data-theme="dark"] {
  background-color: #0A0A0A;
  color: #F2EEEA;

  h1, h2, h3, h4, h5, h6 {
    color: #F2EEEA;
  }

  p {
    color: rgba(242, 238, 234, 0.8);
  }

  .btn-primary {
    background-color: #C8302B;
    color: #F2EEEA;
  }

  .btn-outline-primary,
  .btn-secondary {
    border-color: #F2EEEA;
    color: #F2EEEA;

    &:hover {
      background-color: #F2EEEA;
      color: #0A0A0A;
    }
  }
}

// --- Cards ---
.card,
.web-card,
.frappe-card {
  border: 1px solid #D8D2CA;
  border-radius: 12px;
  background-color: #FFFFFF;
  box-shadow: none;
  transition: box-shadow 0.2s ease;

  &:hover {
    box-shadow: 0 4px 16px rgba(26, 26, 26, 0.06);
  }
}

// --- Tags / Badges ---
.badge,
.tag {
  font-family: 'Space Mono', monospace;
  font-size: 0.625rem;              // 10px
  font-weight: 400;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  border-radius: 4px;
  padding: 0.25rem 0.5rem;
}

.badge-primary,
.tag-primary {
  background-color: rgba(200, 48, 43, 0.08);  // Crimson Tint
  color: #C8302B;
}

// --- Forms / Inputs ---
.form-control,
input[type="text"],
input[type="email"],
input[type="password"],
input[type="search"],
textarea,
select {
  border: 1px solid #D8D2CA;
  border-radius: 8px;
  background-color: #FFFFFF;
  color: #1A1A1A;
  font-family: 'DM Sans', sans-serif;
  font-size: 0.9375rem;
  padding: 0.625rem 1rem;
  transition: border-color 0.2s ease;

  &:focus {
    border-color: #C8302B;
    box-shadow: 0 0 0 3px rgba(200, 48, 43, 0.08);
    outline: none;
  }

  &::placeholder {
    color: #8A8178;                  // Warm Gray
  }
}

// --- Tables ---
.table,
.frappe-list {
  th {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    font-size: 0.75rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: #8A8178;                  // Warm Gray headers
    border-bottom: 2px solid #D8D2CA;
  }

  td {
    color: #1A1A1A;
    border-bottom: 1px solid #D8D2CA;
  }
}

// --- Breadcrumbs ---
.breadcrumb {
  background-color: transparent;
  font-family: 'Space Grotesk', sans-serif;
  font-size: 0.8125rem;
  font-weight: 500;

  .breadcrumb-item {
    color: #8A8178;

    a {
      color: #8A8178;
      &:hover { color: #C8302B; }
    }

    &.active {
      color: #1A1A1A;
    }
  }
}

// --- Blog / Content Pages ---
.blog-page,
.product-page,
.web-page {
  .page-header h1 {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    letter-spacing: 0.02em;
  }

  .page-content {
    font-family: 'DM Sans', sans-serif;
    font-size: 1rem;
    line-height: 1.7;
    color: #1A1A1A;
  }
}

// --- Login Page ---
.login-page {
  background-color: #F2EEEA;

  .form-signin {
    max-width: 420px;
    background-color: #FFFFFF;
    border: 1px solid #D8D2CA;
    border-radius: 12px;
    padding: 2rem;
  }
}

// --- Scroll Bar (Webkit) ---
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: #F2EEEA;
}

::-webkit-scrollbar-thumb {
  background: #D8D2CA;
  border-radius: 999px;

  &:hover {
    background: #8A8178;
  }
}

// --- Hide "Powered by ERPNext" ---
.web-footer .footer-powered {
  display: none !important;
}

// --- Utility Classes ---
.text-crimson   { color: #C8302B !important; }
.text-charcoal  { color: #1A1A1A !important; }
.text-warm-gray { color: #8A8178 !important; }
.bg-cream       { background-color: #F2EEEA !important; }
.bg-void        { background-color: #0A0A0A !important; }
.border-light   { border-color: #D8D2CA !important; }
.font-display   { font-family: 'Space Grotesk', sans-serif !important; }
.font-mono      { font-family: 'Space Mono', monospace !important; }
```

---

## JavaScript

**Field:** `custom_javascript`

```javascript
// ============================================================
// boon — Custom JavaScript
// Runs when the boon Website Theme is active
// ============================================================

document.addEventListener('DOMContentLoaded', function() {

  // --- Force wordmark lowercase ---
  // Find any element with class .boon-wordmark or .navbar-brand
  // and ensure the text content is always lowercase "boon"
  document.querySelectorAll('.boon-wordmark, .navbar-brand').forEach(function(el) {
    if (el.textContent.trim().toLowerCase() === 'boon') {
      el.textContent = 'boon';
    }
  });

  // --- Smooth scroll for anchor links ---
  document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
    anchor.addEventListener('click', function(e) {
      var target = document.querySelector(this.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  // --- Add data attributes for dark sections ---
  document.querySelectorAll('.hero-section, .section-dark').forEach(function(section) {
    section.setAttribute('data-theme', 'dark');
  });

});
```

---

## Quick Reference — All Field Values

| Frappe Field | boon Value |
|---|---|
| **Theme** | `boon — Crimson & Charcoal` |
| **Google Font** | `DM Sans` |
| **Font Size** | `1rem` |
| **Font Properties** | DM Sans 400, line-height 1.7 |
| **Button Rounded Corners** | `Yes` |
| **Button Shadows** | `No` |
| **Button Gradients** | `No` |
| **Primary Color** | `#C8302B` (Crimson) |
| **Text Color** | `#1A1A1A` (Charcoal) |
| **Light Color** | `#F2EEEA` (Cream) |
| **Dark Color** | `#0A0A0A` (Void Black) |
| **Background Color** | `#F2EEEA` (Cream) |
| **Custom Overrides** | See SCSS block above |
| **Custom SCSS** | See SCSS block above |
| **JavaScript** | See JS block above |

---

## Color Token Map

| Brand Token | Hex | Bootstrap Variable | CSS Usage |
|---|---|---|---|
| Cream | `#F2EEEA` | `$light`, `$body-bg` | Page background, light surfaces |
| Charcoal | `#1A1A1A` | `$body-color` | Primary text |
| Crimson | `#C8302B` | `$primary`, `$danger` | CTAs, wordmark, links, accents |
| Crimson Hover | `#A52722` | `$link-hover-color` | Hover states |
| Crimson Tint | `rgba(200,48,43,0.08)` | — | Tags, tinted backgrounds |
| Void Black | `#0A0A0A` | `$dark` | Footer, hero sections, dark mode |
| Warm Gray | `#8A8178` | `$secondary`, `$info` | Secondary text, labels, captions |
| Light Border | `#D8D2CA` | `$border-color` | Dividers, input borders, card borders |
| Mid Gray | `#555555` | — | Tertiary text, disabled states |
| Dark Border | `#2A2A2A` | — | Borders on dark backgrounds |

---

## Font Loading Summary

| Font | Weights Loaded | Role | Google Fonts URL |
|---|---|---|---|
| DM Sans | 400, 500, 600, 700 | Body, buttons, UI text | `family=DM+Sans:wght@400;500;600;700` |
| Space Grotesk | 500, 600, 700 | Headlines, wordmark, nav | `family=Space+Grotesk:wght@500;600;700` |
| Space Mono | 400, 700 | Data, specs, tags, code | `family=Space+Mono:wght@400;700` |

Combined `@import`:
```
https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=DM+Sans:wght@400;500;600;700&family=Space+Mono:wght@400;700&display=swap
```

---

## After Applying

```bash
bench --site {site} clear-cache
```

Then verify on: homepage, blog, product page, web form, login page, and footer.
