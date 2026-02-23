# Frappe Website Theme — Developer & AI Reference Guide

> Use this document when creating, modifying, or troubleshooting Frappe Website Themes. Covers the DocType structure, SCSS compilation pipeline, Bootstrap variable overrides, navbar/footer styling, dark mode, programmatic theme creation, and common pitfalls.

---

## 1. What Is a Website Theme?

**Website Theme** is a core Frappe DocType that controls the look and feel of the public-facing website (portal pages, blog, product catalog, web forms, etc.). It does **not** affect the Frappe Desk (back-office) UI.

### Source Location (in Frappe core)

```
apps/frappe/frappe/website/doctype/website_theme/
├── website_theme.json      # DocType schema (fields, permissions)
├── website_theme.py        # Python controller (SCSS compilation, validation)
├── website_theme.js        # Client-side form logic (app theme selector, preview)
└── test_website_theme.py   # Tests
```

Database table: `tabWebsite Theme`

---

## 2. Theme DocType Fields

| Field               | Fieldtype   | Purpose                                                        |
| ------------------- | ----------- | -------------------------------------------------------------- |
| `theme_name`        | Data        | Unique display name                                            |
| `custom_overrides`  | Code (SCSS) | SCSS variable overrides — included **before** app theme files  |
| `custom_scss`       | Code (SCSS) | Custom styles — included **after** app theme files             |
| `custom_javascript` | Code (JS)   | JavaScript executed when theme is active                       |
| `style_using_css`   | Code (CSS)  | Raw CSS rules applied after all SCSS compilation               |
| `google_font`       | Data        | Google Font name for body text                                 |
| `font_size`         | Data        | Base font size (e.g. `1rem`)                                   |
| `theme_json`        | JSON        | Stores color scheme, font, button style selections from the UI |

### Included App Themes

The form dynamically detects installed apps and shows a checkbox for each one. When checked, the app's `public/scss/website.scss` file is imported into the compiled theme stylesheet.

---

## 3. SCSS Compilation Order

When you save a Website Theme, Frappe compiles CSS in this order:

```
1. custom_overrides     ← SCSS variable overrides ($primary, $font-family-base, etc.)
2. App theme files      ← frappe/public/scss/website.scss, erpnext/public/scss/website.scss, etc.
3. custom_scss          ← Your custom SCSS rules (has access to all variables)
4. style_using_css      ← Raw CSS appended at the end
```

**Key implication:** Set variables in `custom_overrides` (step 1) so they propagate through Bootstrap and app SCSS. Write layout/component overrides in `custom_scss` (step 3) where you can reference those variables.

### Compilation Requirements

- **Node.js must be installed** and accessible in PATH — Frappe uses it for SCSS → CSS compilation.
- On save, the controller's `on_update()` method triggers compilation.
- The generated CSS is stored and served as a `<link>` tag via `base.html`.

---

## 4. Bootstrap 4 Variable Reference

Frappe uses Bootstrap 4. Override these in the **Custom Overrides** field:

### Colors

```scss
$primary:   #007bff;   // Main brand color — buttons, links, active states
$secondary: #6c757d;   // Secondary actions
$success:   #28a745;
$danger:    #dc3545;
$warning:   #ffc107;
$info:      #17a2b8;
$light:     #f8f9fa;
$dark:      #343a40;

$body-bg:    #ffffff;   // Page background
$body-color: #212529;   // Default text color
```

### Typography

```scss
$font-family-base:      -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
$font-family-monospace: SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
$font-size-base:        1rem;      // 16px
$font-weight-base:      400;
$line-height-base:      1.5;
$headings-font-family:  null;      // Falls back to $font-family-base
$headings-font-weight:  500;
```

### Spacing & Layout

```scss
$spacer: 1rem;               // Base spacing unit (margins, paddings)
$border-radius:    0.25rem;
$border-radius-lg: 0.3rem;
$border-radius-sm: 0.2rem;
$border-color:     #dee2e6;
```

### Buttons

```scss
$btn-padding-y:      0.375rem;
$btn-padding-x:      0.75rem;
$btn-border-radius:  0.25rem;
$btn-font-weight:    400;
```

### Grid Breakpoints

```scss
$grid-breakpoints: (
  xs: 0,
  sm: 576px,
  md: 768px,
  lg: 992px,
  xl: 1200px
);
```

> Full list: https://github.com/twbs/bootstrap/blob/v4-dev/scss/_variables.scss

---

## 5. How Themes Are Applied

1. **Website Settings** has a `website_theme` Link field pointing to a Website Theme document.
2. On page load, Frappe reads the active theme from Website Settings.
3. `base.html` (the root Jinja2 template for all portal pages) injects the compiled CSS as a `<link>` tag.
4. The `<html>` element receives a `data-theme="Theme Name"` attribute — useful for theme-specific CSS selectors.

### Setting the Active Theme

**Via UI:** Website Settings → Website Theme dropdown → select your theme → Save.

**Via code:**
```python
frappe.db.set_value("Website Settings", "Website Settings", "website_theme", "My Custom Theme")
```

**Via bench console:**
```bash
bench --site mysite.localhost console
>>> frappe.db.set_value("Website Settings", "Website Settings", "website_theme", "My Custom Theme")
>>> frappe.db.commit()
```

---

## 6. Google Fonts Integration

### Method 1: Built-in Field

Set the `google_font` field in the Website Theme form to a Google Font name (e.g., `Inter`, `Poppins`). Frappe auto-generates the `<link>` tag and sets `$font-family-base`.

### Method 2: Manual @import in Custom SCSS

```scss
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@700&display=swap');
```

Then in **Custom Overrides**:
```scss
$font-family-base: 'Inter', sans-serif;
$headings-font-family: 'Playfair Display', serif;
```

> **Tip:** Only load the weights you actually use — each weight adds ~20 KB.

---

## 7. Navbar & Footer Styling

### Navbar

CSS class: `.navbar-main`

```scss
// In Custom SCSS
.navbar-main {
    background-color: $dark;
    padding: 1rem 0;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);

    .navbar-brand {
        font-size: 1.5rem;
        font-weight: 700;
        color: white;
    }

    .nav-link {
        color: rgba(255, 255, 255, 0.7);
        transition: color 0.2s;

        &:hover { color: white; }
        &.active { color: $primary; font-weight: 600; }
    }

    .dropdown-menu {
        background-color: darken($dark, 5%);
        border: none;
    }
}
```

### Footer

CSS class: `.web-footer`

```scss
.web-footer {
    background-color: $secondary;
    color: white;
    padding: 3rem 0 1rem;
    margin-top: 5rem;

    h5 {
        color: white;
        font-weight: 600;
        margin-bottom: 1.5rem;
    }

    a {
        color: rgba(255, 255, 255, 0.7);
        text-decoration: none;
        &:hover { color: $primary; }
    }
}
```

### Managing Nav Items

Website Settings → **Top Bar** section → add/edit navigation items. Supports hierarchical parent-child menus.

### Custom Navbar/Footer Templates

For full control, create a **Web Template** DocType record with `template_type` set to `"Navbar"` or `"Footer"`, then reference it in Website Settings.

---

## 8. Dark Mode

### Approach A: Separate Dark Theme

Create a second Website Theme with dark colors:

```scss
// Custom Overrides
$primary:    #BB86FC;
$body-bg:    #121212;
$body-color: #E0E0E0;
$dark:       #1E1E1E;
$light:      #2C2C2C;
$border-color: #383838;
```

Switch themes in Website Settings, or let users toggle via a custom widget.

### Approach B: CSS Custom Properties + prefers-color-scheme

In **Custom SCSS**:

```scss
:root {
    --bg-color: #ffffff;
    --text-color: #212529;
    --primary-color: #{$primary};
}

@media (prefers-color-scheme: dark) {
    :root {
        --bg-color: #121212;
        --text-color: #E0E0E0;
        --primary-color: #BB86FC;
    }
}

body {
    background-color: var(--bg-color);
    color: var(--text-color);
}
```

### Approach C: Frappe ThemeSwitcher

In **Custom JavaScript**:

```javascript
// Adds a theme toggle to the page
new frappe.ui.ThemeSwitcher().show();
```

---

## 9. Creating Themes via a Custom App

### Export an Existing Theme as a Fixture

```bash
# 1. Create your theme via the UI
# 2. Add to hooks.py:
```

```python
# my_app/hooks.py
fixtures = [
    {
        "dt": "Website Theme",
        "filters": [["name", "=", "My Custom Theme"]]
    },
]
```

```bash
# 3. Export
bench --site mysite export-fixtures

# Creates: apps/my_app/my_app/fixtures/website_theme.json
# Commit this file to version control
```

### Create Theme Programmatically

```python
import frappe

def after_install():
    if not frappe.db.exists("Website Theme", "My Custom Theme"):
        theme = frappe.get_doc({
            "doctype": "Website Theme",
            "theme_name": "My Custom Theme",
            "custom_overrides": "$primary: #FF6B35;\n$secondary: #004E89;",
            "custom_scss": ".navbar-main { background-color: #004E89; color: white; }",
            "google_font": "Inter",
        })
        theme.insert(ignore_permissions=True)

    frappe.db.set_value(
        "Website Settings", "Website Settings",
        "website_theme", "My Custom Theme"
    )
    frappe.db.commit()
```

### Include Extra CSS/JS via hooks.py

```python
# For portal/website pages:
web_include_css = ["/assets/my_app/css/custom_website.css"]
web_include_js  = ["/assets/my_app/js/custom_website.js"]
```

Place files in `my_app/public/css/` and `my_app/public/js/`.

> **Note:** `web_include_css` loads on portal pages. `app_include_css` loads on Desk pages. They are separate.

---

## 10. Common Gotchas

| Issue | Cause | Fix |
| ----- | ----- | --- |
| `FileNotFoundError: 'node'` on save | Node.js not installed or not in PATH | Install Node.js, verify with `node --version` |
| Theme saved but no visual change | Browser/Frappe cache | `bench --site mysite clear-cache` + hard refresh (Ctrl+Shift+R) |
| Product/blog/login pages unstyled | Those pages may not fully inherit theme CSS | Add explicit CSS rules for `.product-page`, `.blog-page`, `.login-page` in Custom SCSS |
| Custom SCSS variables not taking effect | Variables defined in `custom_scss` instead of `custom_overrides` | Move `$variable` definitions to **Custom Overrides** (compiled first) |
| `@import` of frappe internal SCSS fails | Internal SCSS paths not resolvable from theme context | Avoid `@import` of framework files; use Custom Overrides for variables instead |
| `web_include_css` not loading with theme | Known conflict between theme CSS and hook CSS | Use both `web_include_css` (portal) and check load order; or put styles in Custom SCSS |
| CSS overridden by app styles | Specificity too low | Increase selector specificity or use `!important` sparingly |
| Google Fonts not loading | Offline mode or CSP headers blocking | Use full `@import url('https://...')` in Custom SCSS; check Content-Security-Policy |

---

## 11. Best Practices

1. **Use variables, not hardcoded colors.** Set everything in `custom_overrides` so changes propagate automatically.
2. **Mobile-first.** Use Bootstrap's responsive grid and test on small screens.
3. **Version control your theme.** Export as a fixture in your custom app and commit to git.
4. **Minimize `!important`.** If you need it, your selector specificity is wrong.
5. **Load only needed font weights.** Each Google Font weight adds ~20 KB of network overhead.
6. **Clear cache during development.** Run `bench --site mysite clear-cache` after every theme change.
7. **Test on multiple page types.** Homepage, blog, product page, web form, login — each may need targeted CSS.
8. **Don't edit core themes.** Create a new theme or clone an existing one.
9. **Use `data-theme` attribute** for theme-specific selectors: `[data-theme="My Theme"] .some-class { ... }`.
10. **Document your variables.** Add SCSS comments in Custom Overrides for future maintainers (and AI).

---

## 12. Quick CLI Reference

```bash
# Clear cache after theme changes
bench --site mysite clear-cache

# Rebuild all frontend assets
bench build

# Rebuild specific app assets
bench build --app erpnext

# Open console to set theme programmatically
bench --site mysite console

# Export theme fixture
bench --site mysite export-fixtures

# Run theme-related tests
bench --site mysite run-tests --doctype "Website Theme"
```

---

## 13. Useful Links

- Frappe Website Theme Docs: https://docs.frappe.io/erpnext/user/manual/en/website-theme
- Bootstrap 4 SCSS Variables: https://github.com/twbs/bootstrap/blob/v4-dev/scss/_variables.scss
- Bootstrap 4 Theming Guide: https://getbootstrap.com/docs/4.1/getting-started/theming/
- Frappe Hooks Reference: https://docs.frappe.io/framework/user/en/python-api/hooks
- Frappe Forum (Theme Discussions): https://discuss.frappe.io/search?q=website%20theme
- Frappe GitHub (Website Theme Source): https://github.com/frappe/frappe/tree/develop/frappe/website/doctype/website_theme
