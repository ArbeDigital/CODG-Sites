# Carolina Oaks Dental Care of Greenville

Location site for Carolina Oaks Dental Care in Greenville, SC — rebuilt from a
static WordPress/Salient export as a clean [Astro](https://astro.build) +
[Tailwind CSS v4](https://tailwindcss.com) site.

## Commands

| Command           | Action                                       |
| ----------------- | -------------------------------------------- |
| `npm install`     | Install dependencies                         |
| `npm run dev`     | Start the dev server at `localhost:4321`     |
| `npm run build`    | Build the production site to `dist/`         |
| `npm run preview` | Preview the production build locally         |

## Notes

- **Tracking** (kept from the original site): GTM `GTM-5HPPJN5`,
  GA4 `G-E76SXNBXZN`, Facebook domain verification
  `zw2z8wphwm6ll6aypqj0829aktu8ov`. Thank-you page includes the same tracking
  so GTM conversion tags can fire.
- **Contact form** posts to Formspree (`mojolrvv`) and redirects to `/thank-you/`.
- **Blog** posts live in `src/content/blog/*.md` and keep their original root URLs.
- **Services** keep the original `/services/[slug]/` paths.
