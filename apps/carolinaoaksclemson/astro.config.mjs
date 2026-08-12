// @ts-check
import { defineConfig } from "astro/config";
import sitemap from "@astrojs/sitemap";
import tailwindcss from "@tailwindcss/vite";
import { copyFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

/** Official sitemap writes sitemap-0.xml; also expose /sitemap.xml for crawlers. */
function sitemapXmlAlias() {
  return {
    name: "sitemap-xml-alias",
    hooks: {
      "astro:build:done": async ({ dir }) => {
        const outDir = fileURLToPath(dir);
        await copyFile(`${outDir}/sitemap-0.xml`, `${outDir}/sitemap.xml`);
      },
    },
  };
}

export default defineConfig({
  site: "https://carolinaoaksclemson.com",
  trailingSlash: "ignore",
  integrations: [
    sitemap({
      filter: (page) => !page.includes("/thank-you"),
      namespaces: {
        news: false,
        xhtml: false,
        image: false,
        video: false,
      },
    }),
    sitemapXmlAlias(),
  ],
  vite: {
    plugins: [tailwindcss()],
  },
});
