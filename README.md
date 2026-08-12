# CODG-Sites

A simple monorepo for static websites managed by ArbeDigital / CODG.

## Structure

Each site lives in its own folder under `apps/`:

| Folder | Site |
|--------|------|
| `apps/carolina-oaks/` | Carolina Oaks hub (Astro) |
| `apps/carolinaoaksgreenville/` | Carolina Oaks Greenville |
| `apps/carolinaoakstr.com/` | carolinaoakstr.com |
| `apps/carolinaoaksanderson.com/` | carolinaoaksanderson.com |
| `apps/carolinaoaksclemson/` | Carolina Oaks Clemson (Astro) |
| `apps/oconeedentalassociates/` | Oconee Dental Associates |

## Guidelines

- Each site is self-contained under `apps/<site-name>/`.
- Converted sites (`carolina-oaks`, `carolinaoaksclemson`) use Astro + Tailwind; remaining sites may still be plain static HTML mirrors.
- Do not share files across site folders.