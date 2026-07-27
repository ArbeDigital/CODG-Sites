# Carolina Oaks Dental Care

Marketing hub site for the four Carolina Oaks Dental Care locations
(Greenville, Clemson, Travelers Rest, Anderson), rebuilt from a static
WordPress/Salient export as a clean [Astro](https://astro.build) +
[Tailwind CSS v4](https://tailwindcss.com) site.

## Commands

| Command           | Action                                       |
| ----------------- | -------------------------------------------- |
| `npm install`     | Install dependencies                         |
| `npm run dev`     | Start the dev server at `localhost:4321`     |
| `npm run build`   | Build the production site to `dist/`         |
| `npm run preview` | Preview the production build locally         |

## Structure

```
public/
├── images/                  # logos, hero/testimonial backgrounds, decorations
└── favicon-*.png
src/
├── styles/global.css        # Tailwind + design tokens (colors, fonts, type scale)
├── layouts/
│   ├── BaseLayout.astro     # <head> (SEO/OG, fonts, tracking), Header, Footer
│   └── LegalLayout.astro    # prose wrapper for the legal pages
├── components/
│   ├── Tracking.astro       # GTM, GA4, Meta Pixel, Trade Desk pixels
│   ├── Header.astro         # centered logo nav, mobile menu, scroll behavior
│   ├── Footer.astro
│   ├── Hero.astro
│   ├── AppointmentForm.astro  # Formspree form + phone mask
│   ├── ValueProps.astro
│   ├── Services.astro
│   ├── Locations.astro        # 4 office cards with Google Maps embeds
│   └── Testimonials.astro     # autorotating review slider
└── pages/
    ├── index.astro
    ├── thank-you.astro           # standalone, noindex
    ├── privacy-policy.astro
    └── accessibility-statement.astro
```

## Notes

- **Design tokens** live in `src/styles/global.css` under `@theme`:
  brand green `#498868`, accent teal `#49c5b1`, forest `#2a4e3c`,
  ink `#292e2d`, gold `#e8bf3a`. Fonts: Lora (headings), Poppins (body),
  Baskervville (accents), loaded from Google Fonts.
- **Appointment form** posts to Formspree (`meebavon`); the success
  redirect to `/thank-you/` is configured in the Formspree dashboard.
- **Tracking** (kept from the original site): GTM `GTM-NZVQ83P`,
  GA4 `G-TNNX5TMEYC`, Meta Pixel `772151824852850`, The Trade Desk
  `ay9pui6`/`kwdgx4j`, plus the Facebook domain verification meta tag.
- The original WordPress export was deleted after the conversion; it is
  recoverable from git history if ever needed.
