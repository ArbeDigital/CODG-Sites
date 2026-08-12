/** Map WP upload paths from extracted JSON to public/images URLs. */
export function publicImage(src: string | undefined | null): string {
  if (!src) return "";
  if (src.startsWith("/")) return src;
  const name = src.split("/").pop() ?? src;
  return `/images/${name}`;
}

export function blogImage(src: string | undefined | null): string {
  if (!src) return "";
  if (src.startsWith("/")) return src;
  const name = src.split("/").pop() ?? src;
  return `/images/blog/${name}`;
}
