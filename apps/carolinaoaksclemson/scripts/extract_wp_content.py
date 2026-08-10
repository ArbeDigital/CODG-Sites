#!/usr/bin/env python3
"""Extract clean content from Clemson WP HTML mirror into Astro data files."""
from __future__ import annotations

import json
import re
from html import unescape
from pathlib import Path
from urllib.parse import unquote

from bs4 import BeautifulSoup, NavigableString, Tag
import html2text

SRC = Path("/workspace/apps/.clemson-wp-src")
OUT_DATA = Path("/workspace/apps/carolinaoaksclemson/src/data")
OUT_BLOG = Path("/workspace/apps/carolinaoaksclemson/src/content/blog")
OUT_DATA.mkdir(parents=True, exist_ok=True)
OUT_BLOG.mkdir(parents=True, exist_ok=True)

assets: set[str] = set()
blog_assets: set[str] = set()

h2t = html2text.HTML2Text()
h2t.body_width = 0
h2t.ignore_images = False
h2t.ignore_links = False
h2t.protect_links = False
h2t.unicode_snob = True
h2t.single_line_break = False


def load(path: Path) -> BeautifulSoup:
    return BeautifulSoup(path.read_text(encoding="utf-8", errors="replace"), "lxml")


def meta(soup: BeautifulSoup, *, name: str | None = None, prop: str | None = None) -> str | None:
    tag = soup.find("meta", attrs={"name": name} if name else {"property": prop})
    if not tag:
        return None
    return unescape(tag.get("content") or "").strip() or None


def normalize_upload_path(url: str | None) -> str | None:
    if not url:
        return None
    url = url.strip().strip('"').strip("'")
    url = re.sub(r"^https?://carolinaoaksclemson\.com/", "", url)
    url = re.sub(r"^(\.\./)+", "", url)
    m = re.search(r"(wp-content/uploads/[^\s?#]+)", url)
    if not m:
        return None
    return unquote(m.group(1))


def track_asset(path: str | None, *, blog: bool = False) -> str | None:
    if not path:
        return None
    path = normalize_upload_path(path) or path
    if not path.startswith("wp-content/uploads/"):
        n = normalize_upload_path(path)
        if not n:
            return path
        path = n
    (blog_assets if blog else assets).add(path)
    return path


def clean_inline_html(el: Tag) -> str:
    clone = BeautifulSoup(str(el), "lxml")
    root = clone.body if clone.body else clone
    for tag in root.find_all(True):
        allowed = {}
        if tag.name == "a" and tag.get("href"):
            allowed["href"] = normalize_internal_href(tag["href"])
            if tag.get("rel"):
                rel = tag.get("rel")
                allowed["rel"] = " ".join(rel) if isinstance(rel, list) else rel
            if tag.get("target"):
                allowed["target"] = tag["target"]
        if tag.name == "img":
            if tag.get("src"):
                allowed["src"] = tag["src"]
            if tag.get("alt") is not None:
                allowed["alt"] = tag["alt"]
        if tag.name == "br":
            tag.attrs = {}
            continue
        tag.attrs = allowed
    for span in root.find_all("span"):
        span.unwrap()
    html = "".join(str(c) for c in root.contents)
    html = re.sub(r"[ \t]+", " ", html)
    html = unescape(html)
    return html.strip()


def normalize_internal_href(href: str) -> str:
    if not href:
        return href
    href = href.strip()
    if href.startswith(("http://", "https://", "mailto:", "tel:", "#")):
        return href
    href = href.replace("index.html", "")
    href = re.sub(r"^(\.\./)+", "/", href)
    if href in ("", "/"):
        return "/"
    if not href.startswith("/"):
        href = "/" + href
    href = re.sub(r"/{2,}", "/", href)
    # keep trailing slash for directory-style paths
    if not Path(href).suffix and not href.endswith("/"):
        href += "/"
    return href


def strip_global_sections(main: Tag) -> None:
    for g in main.select(".nectar-global-section, .before-footer, footer, #footer-outer"):
        g.decompose()


def text_columns(main: Tag) -> list[Tag]:
    return list(main.select(".wpb_text_column > .wpb_wrapper"))


def parse_blocks_from_columns(cols: list[Tag]) -> dict:
    paragraphs: list[str] = []
    lists: list[dict] = []
    html_parts: list[str] = []
    for col in cols:
        for child in col.children:
            if not isinstance(child, Tag):
                continue
            if child.name == "h2":
                continue
            if child.name in ("h3", "h4"):
                html_parts.append(clean_inline_html(child))
                continue
            if child.name == "p":
                t = unescape(child.get_text(" ", strip=True))
                if t:
                    paragraphs.append(t)
                html_parts.append(clean_inline_html(child))
            elif child.name in ("ul", "ol"):
                items = [
                    unescape(li.get_text(" ", strip=True))
                    for li in child.find_all("li", recursive=False)
                    if li.get_text(strip=True)
                ]
                if items:
                    lists.append({"ordered": child.name == "ol", "items": items})
                html_parts.append(clean_inline_html(child))
    return {
        "paragraphs": paragraphs,
        "lists": lists,
        "html": "\n".join(html_parts).strip(),
    }


def extract_service(slug: str) -> dict:
    path = SRC / "dental-services" / slug / "index.html"
    soup = load(path)
    main = soup.select_one(".main-content")
    strip_global_sections(main)

    cols = text_columns(main)
    title = None
    intro = None
    # first col with h1
    for col in cols:
        h1 = col.find("h1")
        if h1:
            title = unescape(h1.get_text(strip=True))
            break
    # intro = first p-only column after h1 before first h2
    seen_h1 = False
    for col in cols:
        if col.find("h1"):
            seen_h1 = True
            continue
        if not seen_h1:
            continue
        if col.find("h2"):
            break
        p = col.find("p")
        if p:
            intro = unescape(p.get_text(" ", strip=True))
            break

    description = meta(soup, name="description") or meta(soup, prop="og:description")

    hero_image = None
    for el in main.select("[style*='background-image']"):
        m = re.search(r"url\(([^)]+)\)", el.get("style", ""))
        if m and "uploads" in m.group(1):
            hero_image = track_asset(m.group(1))
            break

    # Group columns into sections by h2
    sections = []
    current = None
    section_cols: list[Tag] = []

    def flush():
        nonlocal current, section_cols
        if not current:
            return
        blocks = parse_blocks_from_columns(section_cols)
        section = {
            "heading": current["heading"],
            "paragraphs": blocks["paragraphs"],
            "lists": blocks["lists"],
            "html": blocks["html"],
        }
        sections.append(section)
        current = None
        section_cols = []

    for col in cols:
        h2 = col.find("h2")
        if h2 and h2.parent is col:
            flush()
            current = {"heading": unescape(h2.get_text(" ", strip=True)), "_h2": h2}
            section_cols = [col]
        elif current is not None:
            section_cols.append(col)

    flush()

    # Page content images (non-decorative), tracked for asset manifest
    page_images = []
    for img in main.find_all("img"):
        src = img.get("src") or ""
        if "uploads" not in src:
            continue
        low = src.lower()
        if any(x in low for x in ("map", "logo", "divider", "shadow-leaves", "acorn", "criss-cross")):
            continue
        src_full = re.sub(r"-\d+x\d+(\.(?:jpg|jpeg|png|webp))$", r"\1", src, flags=re.I)
        p = track_asset(src_full)
        if p:
            page_images.append({"src": p, "alt": img.get("alt") or ""})
    seen = set()
    uniq_imgs = []
    for im in page_images:
        if im["src"] not in seen:
            seen.add(im["src"])
            uniq_imgs.append(im)

    # Attach images to the first section whose heading/alt loosely matches, else first section
    if uniq_imgs and sections:
        for im in uniq_imgs:
            placed = False
            alt = (im.get("alt") or "").lower()
            for sec in sections:
                if alt and alt[:20].lower() in sec["heading"].lower():
                    sec.setdefault("images", []).append(im)
                    placed = True
                    break
            if not placed:
                # put on last content section (typical layout: text then image in body)
                sections[-1].setdefault("images", []).append(im)

    return {
        "slug": slug,
        "title": title,
        "description": description,
        "intro": intro,
        "heroImage": hero_image,
        "sections": sections,
    }


SERVICE_SLUGS = [
    "bridges",
    "cosmetic-dentistry",
    "dental-crowns",
    "dental-implant-restorations",
    "dental-veneers",
    "dentures",
    "emergency-dentistry",
    "family-dentistry",
    "invisalign-braces",
    "occlusal-guards",
    "partial-dentures",
    "dentistry-for-kids",
    "root-canals",
    "teeth-whitening",
]


def extract_home() -> dict:
    soup = load(SRC / "index.html")
    main = soup.select_one(".main-content")
    strip_global_sections(main)

    hero_headline = unescape(main.find("h1").get_text(strip=True))
    hero_sub = None
    for p in main.find("h1").find_all_next("p"):
        t = p.get_text(" ", strip=True)
        if t:
            hero_sub = unescape(t)
            break
    hero_cta = {"label": "Request An Appointment", "href": "/contact-us/"}
    btn = main.find("a", class_="nectar-button")
    if btn:
        hero_cta = {
            "label": unescape(btn.get_text(" ", strip=True)),
            "href": normalize_internal_href(btn.get("href") or "/contact-us/"),
        }

    hero_image = None
    for el in main.select("[style*='background-image']"):
        m = re.search(r"url\(([^)]+)\)", el.get("style", ""))
        if m and "happy-woman-home-banner" in m.group(1):
            hero_image = track_asset(m.group(1))
            break

    welcome_eyebrow = None
    for p in main.find_all("p"):
        t = p.get_text(strip=True)
        if re.search(r"Carolina Oaks Dental [Cc]are of Clemson", t):
            welcome_eyebrow = unescape(t)
            break

    welcome_heading = None
    welcome_paragraphs = []
    for h2 in main.find_all("h2"):
        if "Full-Service" in h2.get_text():
            welcome_heading = unescape(h2.get_text(strip=True))
            # next substantial paragraph in following text column
            for p in h2.find_all_next("p", limit=5):
                # rebuild text with links preserved as plain
                t = unescape(p.get_text(" ", strip=True))
                t = re.sub(r"\s+,", ",", t)
                t = re.sub(r"\s{2,}", " ", t)
                if len(t) > 40:
                    welcome_paragraphs.append(t)
                    break
            break

    features = []
    for h6 in main.find_all("h6"):
        t = h6.get_text(strip=True)
        if t in ("Expert Care", "Fun, Friendly Atmosphere", "Top-Notch Service"):
            features.append(t)

    doctors = []
    for label, img_pat in [
        ("Parker", re.compile(r"parker", re.I)),
        ("Ross", re.compile(r"kendon|ross", re.I)),
    ]:
        img = None
        for im in main.select("img"):
            if img_pat.search(im.get("src") or "") or img_pat.search(im.get("alt") or ""):
                img = im
                break
        if not img:
            continue
        src = track_asset(img.get("src"))
        name = None
        bios: list[str] = []
        for p in img.find_all_next("p", limit=10):
            st = p.find("strong")
            if st and label in st.get_text():
                name = unescape(st.get_text(strip=True))
                continue
            if not name:
                continue
            if p.find("strong") and "Dr." in p.get_text() and label not in p.get_text():
                break
            t = unescape(p.get_text(" ", strip=True))
            if not t:
                continue
            if "Request An Appointment" in t:
                break
            # stop at generic practice CTA that isn't the personal bio
            if t.startswith("Carolina Oaks Dental Care offers"):
                break
            if t.startswith("Dr.") and label not in t and len(t) < 50:
                break
            bios.append(t)
            break  # personal bio is a single paragraph for both doctors
        if name:
            parts = name.split(",", 1)
            doctors.append(
                {
                    "name": parts[0].strip(),
                    "credentials": parts[1].strip() if len(parts) > 1 else None,
                    "title": name,
                    "image": src,
                    "bio": bios,
                }
            )

    testimonials = []
    for cell in soup.select(".nectar-flickity .cell"):
        bq = cell.find("blockquote")
        if not bq:
            continue
        quote = unescape(bq.get_text(" ", strip=True)).strip(" \"“”")
        texts = [unescape(t.strip()) for t in cell.stripped_strings]
        author = texts[-1] if len(texts) >= 2 else None
        if author and quote.endswith(author):
            quote = quote[: -len(author)].strip().strip(" \"“”")
        testimonials.append({"quote": quote, "author": author})

    # CTA image substitutes (attachment IDs missing from mirror)
    cta_images = {
        "Family Dentistry": "wp-content/uploads/2022/04/banner-family.jpg",
        "Teeth Whitening": "wp-content/uploads/2022/04/banner-cosmetic-dentistry.jpg",
        "Dental Crowns": "wp-content/uploads/2022/04/banner-dental-general.jpg",
        "Complete Dental Care": "wp-content/uploads/2022/04/banner-woman-smiling.jpg",
    }
    service_ctas = []
    for a in main.select("a.column-link"):
        col = a.find_parent(class_=re.compile(r"wpb_column"))
        if not col:
            continue
        h3 = col.find("h3")
        if not h3:
            continue
        title = unescape(h3.get_text(strip=True))
        href = normalize_internal_href(a.get("href") or "")
        image = track_asset(cta_images.get(title))
        blurb = None
        for p in col.find_all("p"):
            t = unescape(p.get_text(" ", strip=True))
            if t and t != title:
                blurb = t
                break
        service_ctas.append({"title": title, "href": href, "image": image, "blurb": blurb})

    cta_banner = None
    for el in main.select("[style*='background-image']"):
        m = re.search(r"url\(([^)]+)\)", el.get("style", ""))
        if m and "happy-woman-home-cta" in m.group(1):
            cta_banner = track_asset(m.group(1))
            break

    for p in [
        "wp-content/uploads/2022/03/acorn-divider-grey.svg",
        "wp-content/uploads/2022/03/shadow-leaves-left.png",
        "wp-content/uploads/2022/03/testimonial-brown-bg.jpg",
        "wp-content/uploads/2022/03/clemson-map-1.jpg",
        "wp-content/uploads/2022/03/criss-cross-brown.png",
        "wp-content/uploads/2022/04/CO_Clemson-logo.png",
        "wp-content/uploads/2022/04/CO_Clemson-logo-large.png",
        "wp-content/uploads/2017/01/CO_Clemson.png",
        "wp-content/uploads/2022/02/cropped-favicon-clemson-32x32.png",
        "wp-content/uploads/2022/02/cropped-favicon-clemson-192x192.png",
        "wp-content/uploads/2022/02/cropped-favicon-clemson-180x180.png",
    ]:
        if (SRC / p).exists():
            track_asset(p)

    return {
        "hero": {
            "headline": hero_headline,
            "subcopy": hero_sub,
            "cta": hero_cta,
            "image": hero_image,
        },
        "welcome": {
            "eyebrow": welcome_eyebrow,
            "heading": welcome_heading,
            "paragraphs": welcome_paragraphs,
            "features": features,
        },
        "doctors": doctors,
        "testimonials": testimonials,
        "serviceCtas": service_ctas,
        "appointmentBanner": {
            "image": cta_banner,
            "cta": {"label": "Request An Appointment", "href": "/contact-us/"},
        },
    }


def extract_site() -> dict:
    index_html = (SRC / "index.html").read_text(encoding="utf-8", errors="replace")
    contact = load(SRC / "contact-us/index.html")
    gtm = re.search(r"GTM-[A-Z0-9]+", index_html)
    ga4 = re.search(r"gtag/js\?id=(G-[A-Z0-9]+)", index_html)
    fb = meta(load(SRC / "index.html"), name="facebook-domain-verification")
    form = re.search(r'action="(https://formspree\.io/f/[^"]+)"', (SRC / "contact-us/index.html").read_text(encoding="utf-8", errors="replace"))
    iframe = contact.select_one("iframe[src*='google.com/maps']")
    return {
        "name": "Carolina Oaks Dental Care",
        "locationName": "Carolina Oaks Dental Care of Clemson",
        "phone": "(864) 654-6700",
        "phoneTel": "864-654-6700",
        "address": {
            "street": "1000 College Avenue",
            "city": "Clemson",
            "region": "SC",
            "postal": "29631",
            "lines": ["1000 College Avenue", "Clemson, SC 29631"],
            "note": "The Carolina Oaks Clemson, SC is across from the 12 Mile Recreation Park",
        },
        "hours": [
            {"days": "Mon", "hours": "8:30am – 5:00pm", "note": "Closed for Lunch 12:30pm – 2:00pm"},
            {"days": "Tue, Wed, Thur", "hours": "8:30am – 3:30pm"},
        ],
        "mapEmbedUrl": iframe.get("src") if iframe else None,
        "formspreeEndpoint": form.group(1) if form else None,
        "analytics": {
            "gtm": gtm.group(0) if gtm else None,
            "ga4": ga4.group(1) if ga4 else None,
            "facebookDomainVerification": fb,
        },
        "sisterLocations": [
            {"name": "Anderson", "url": "https://carolinaoaksanderson.com/"},
            {"name": "Greenville", "url": "https://carolinaoaksgreenville.com/"},
            {"name": "Travelers Rest", "url": "https://carolinaoakstr.com/"},
        ],
    }


def decode_cf_email(encoded: str) -> str:
    r = int(encoded[:2], 16)
    return "".join(chr(int(encoded[i : i + 2], 16) ^ r) for i in range(2, len(encoded), 2))


def extract_legal(slug: str, outfile: str) -> None:
    soup = load(SRC / slug / "index.html")
    main = soup.select_one(".main-content")
    strip_global_sections(main)
    text_col = None
    for div in main.select(".wpb_text_column .wpb_wrapper"):
        if div.find("h1"):
            text_col = div
            break
    parts = []
    if text_col:
        for child in text_col.children:
            if isinstance(child, Tag) and child.name in ("h1", "h2", "h3", "h4", "p", "ul", "ol"):
                parts.append(clean_inline_html(child))
    html = "\n\n".join(parts)

    def replace_cf(match):
        try:
            email = decode_cf_email(match.group(1))
            return f'<a href="mailto:{email}">{email}</a>'
        except Exception:
            return '<a href="mailto:info@carolinaoaksclemson.com">info@carolinaoaksclemson.com</a>'

    html = re.sub(
        r'<a[^>]*class="__cf_email__"[^>]*data-cfemail="([0-9a-fA-F]+)"[^>]*>[^<]*</a>',
        replace_cf,
        html,
    )
    html = re.sub(
        r'<a href="[^"]*cdn-cgi/l/email-protection"[^>]*>\[email\s*protected\]</a>',
        '<a href="mailto:info@carolinaoaksclemson.com">info@carolinaoaksclemson.com</a>',
        html,
        flags=re.I,
    )
    (OUT_DATA / outfile).write_text(html.strip() + "\n", encoding="utf-8")


def yaml_escape(s: str | None) -> str:
    if s is None:
        return '""'
    return json.dumps(s, ensure_ascii=False)


def html_to_markdown(content_el: Tag) -> str:
    clone = BeautifulSoup(str(content_el), "lxml")
    root = clone.body if clone.body else clone
    for junk in root.select("script, style, .sharing, .nectar-social, .meta-comment-count"):
        junk.decompose()
    for span in root.find_all("span"):
        span.unwrap()
    for em in root.find_all(["em", "i"]):
        # keep italics
        pass
    for a in root.find_all("a"):
        href = a.get("href")
        if href:
            a.attrs = {"href": normalize_internal_href(href)}
        else:
            a.unwrap()
    for img in root.find_all("img"):
        src = img.get("src")
        if src and "uploads" in src:
            p = track_asset(src, blog=True)
            filename = Path(p).name if p else Path(src).name
            img.attrs = {"src": f"/images/blog/{filename}", "alt": img.get("alt") or ""}
    md = h2t.handle(str(root)).strip() + "\n"
    md = re.sub(r"\n{3,}", "\n\n", md)
    # fix empty-ish home links that html2text may mangle
    md = md.replace("](/)", "](/)")
    return md


BLOG_SLUGS = [
    "5-ways-a-custom-occlusal-guard-can-protect-your-teeth-while-you-sleep",
    "elite-athletes-are-more-likely-to-have-poor-oral-health",
    "whats-the-best-way-to-whiten-teeth",
    "link-between-gum-disease-and-your-overall-health",
    "top-5-benefits-dental-implants",
    "dental-exams-important",
    "consider-cosmetic-dentistry",
    "choosing-clemson-sc-dentist",
    "faqs-dental-insurance",
]


def extract_blogs() -> None:
    for slug in BLOG_SLUGS:
        path = SRC / slug / "index.html"
        soup = load(path)
        title = meta(soup, prop="og:title") or soup.title.get_text(strip=True)
        title = re.sub(r"\s*[-|]\s*Carolina Oaks Dental Care\s*$", "", title).strip()
        title = title.replace("\ufffc", "").strip()
        description = meta(soup, name="description") or ""
        pub = meta(soup, prop="article:published_time")
        updated = meta(soup, prop="article:modified_time")
        image_alt = meta(soup, prop="og:image:alt") or ""

        image_src = None
        for el in soup.select(".page-header-bg-image, #page-header-bg [style*='background-image']"):
            m = re.search(r"url\(([^)]+)\)", el.get("style", ""))
            if m:
                image_src = m.group(1)
                break
        if not image_src:
            image_src = meta(soup, prop="og:image")
        upload_path = track_asset(image_src, blog=True)
        image_public = f"/images/blog/{Path(upload_path).name}" if upload_path else ""

        content_el = soup.select_one(".post-content .content-inner") or soup.select_one(".post-content")
        body_md = html_to_markdown(content_el) if content_el else ""

        lines = [
            "---",
            f"title: {yaml_escape(title)}",
            f"description: {yaml_escape(description)}",
            f"pubDate: {yaml_escape(pub)}",
        ]
        if updated and updated != pub:
            lines.append(f"updatedDate: {yaml_escape(updated)}")
        lines.append(f"image: {yaml_escape(image_public)}")
        lines.append(f"imageAlt: {yaml_escape(image_alt)}")
        lines.append("---")
        lines.append("")
        lines.append(body_md)
        (OUT_BLOG / f"{slug}.md").write_text("\n".join(lines), encoding="utf-8")
        print(f"Wrote blog/{slug}.md")


def write_manifest() -> None:
    lines = [
        "# Asset manifest for carolinaoaksclemson Astro conversion",
        "# Copy from apps/.clemson-wp-src/<path> → apps/carolinaoaksclemson/public/<dest>",
        "",
        "## Site / page images → public/images/",
    ]
    for p in sorted(assets):
        lines.append(f"{p}\t→\tpublic/images/{Path(p).name}")
    lines.append("")
    lines.append("## Blog images → public/images/blog/")
    for p in sorted(blog_assets):
        lines.append(f"{p}\t→\tpublic/images/blog/{Path(p).name}")
    lines += [
        "",
        "## Notes",
        "- Home treatment CTA column backgrounds used WP attachment IDs 107/108/103/104 which are missing from the HTML mirror and 404 on the live media API.",
        "  Substituted service banner images (banner-family, banner-cosmetic-dentistry, banner-dental-general, banner-woman-smiling) for serviceCtas[].image.",
        "- Prefer full-size uploads over -NNxNN resized variants when copying.",
        "- Logo/favicon paths included for site chrome.",
        "",
    ]
    (OUT_DATA / "asset-manifest.txt").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    services = [extract_service(s) for s in SERVICE_SLUGS]
    (OUT_DATA / "services.json").write_text(
        json.dumps(services, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Wrote services.json ({len(services)} services)")

    home = extract_home()
    (OUT_DATA / "home.json").write_text(json.dumps(home, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"Wrote home.json (doctors={len(home['doctors'])}, testimonials={len(home['testimonials'])}, ctas={len(home['serviceCtas'])})"
    )

    site = extract_site()
    (OUT_DATA / "site.json").write_text(json.dumps(site, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Wrote site.json")

    extract_legal("privacy-policy", "privacy.html")
    print("Wrote privacy.html")
    extract_legal("accessibility-statement", "accessibility.html")
    print("Wrote accessibility.html")

    extract_blogs()
    write_manifest()
    print(f"Wrote asset-manifest.txt ({len(assets)} site, {len(blog_assets)} blog)")

    # validation summary
    empty = [s["slug"] for s in services if any(not sec["paragraphs"] and not sec["lists"] and not sec["html"] for sec in s["sections"])]
    print("services with empty sections:", empty or "none")
    for s in services:
        print(f"  {s['slug']}: {[ (sec['heading'][:40], len(sec['paragraphs']), len(sec.get('html',''))) for sec in s['sections']]}")


if __name__ == "__main__":
    main()
