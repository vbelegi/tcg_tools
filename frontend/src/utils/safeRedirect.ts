/**
 * Allow only same-origin relative paths for post-login redirects.
 * Rejects protocol-relative URLs, absolute URLs, and backslashes.
 */
export function safeRedirectPath(next: string | null | undefined): string | null {
  if (!next) return null;
  const trimmed = next.trim();
  if (!trimmed.startsWith("/") || trimmed.startsWith("//")) return null;
  if (trimmed.includes("\\") || /^https?:/i.test(trimmed)) return null;
  return trimmed;
}
