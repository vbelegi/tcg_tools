/** Map TCG display names to public icon paths. */

const OTHER = "/tcg-icons/other.png";

export function tcgIconStem(name: string): string {
  return name
    .normalize("NFD")
    .replace(/\p{M}/gu, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
}

export function tcgIconUrl(name: string | null | undefined): string {
  if (!name?.trim()) return OTHER;
  const stem = tcgIconStem(name);
  if (!stem) return OTHER;
  return `/tcg-icons/${stem}.png`;
}

export const DEFAULT_AVATAR_URL = "/avatars/default.png";

export function resolveAvatarUrl(avatarUrl: string | null | undefined): string {
  return avatarUrl?.trim() || DEFAULT_AVATAR_URL;
}
