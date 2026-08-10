# Carolina Oaks Dental Care of Clemson

Location site for Carolina Oaks Dental Care in Clemson, SC — rebuilt from a
static WordPress/Salient export as a clean [Astro](https://astro.build) +
[Tailwind CSS v4](https://tailwindcss.com) site.

## Commands

| Command           | Action                                       |
| ----------------- | -------------------------------------------- |
| `npm install`     | Install dependencies                         |
| `npm run dev`     | Start the dev server at `localhost:4321`     |
| `npm run build`   | Build the production site to `dist/`         |
| `npm run preview` | Preview the production build locally         |

## Notes

- **Tracking** (kept from the original site): GTM `GTM-W5L2WM6`,
  GA4 `G-4WQN0L7MMW`, Facebook domain verification
  `ak644i10xu763vbcvkoyr2ky6rkpvf`. Thank-you page includes the same tracking
  so GTM conversion tags can fire.
- **Contact form** posts to Formspree (`mvzjqdlb`) and redirects to `/thank-you/`.
- **Blog** posts live in `src/content/blog/*.md` and keep their original root URLs.
