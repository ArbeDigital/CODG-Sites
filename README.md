# CODG-Sites

A simple monorepo for static websites managed by ArbeDigital / CODG.

## Structure

Each site lives in its own folder under `apps/`:

| Folder | Site |
|--------|------|
| `apps/carolina-oaks/` | Carolina Oaks |
| `apps/carolinaoaksgreenville/` | Carolina Oaks Greenville |
| `apps/carolinaoakstr.com/` | carolinaoakstr.com |
| `apps/carolinaoaksanderson.com/` | carolinaoaksanderson.com |
| `apps/carolinaoaksclemson.com/` | carolinaoaksclemson.com |
| `apps/oconeedentalassociates/` | Oconee Dental Associates |

## Guidelines

- These are **plain static sites** — no Node.js, no build tooling, no `package.json`.
- Place all HTML, CSS, JavaScript, and asset files for a site directly inside its `apps/<site-name>/` folder.
- Keep each site self-contained; do not share files across site folders.