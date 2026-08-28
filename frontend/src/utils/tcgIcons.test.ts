import { describe, expect, it } from "vitest";

import { DEFAULT_AVATAR_URL, resolveAvatarUrl, tcgIconStem, tcgIconUrl } from "./tcgIcons";

describe("tcgIconStem", () => {
  it("normalizes seeded game names", () => {
    expect(tcgIconStem("Magic: The Gathering")).toBe("magic_the_gathering");
    expect(tcgIconStem("Pokémon TCG")).toBe("pokemon_tcg");
    expect(tcgIconStem("Yu-Gi-Oh!")).toBe("yu_gi_oh");
    expect(tcgIconStem("One Piece CG")).toBe("one_piece_cg");
    expect(tcgIconStem("Digimon CG")).toBe("digimon_cg");
    expect(tcgIconStem("Disney Lorcana")).toBe("disney_lorcana");
    expect(tcgIconStem("Riftbound")).toBe("riftbound");
  });
});

describe("tcgIconUrl", () => {
  it("falls back to other", () => {
    expect(tcgIconUrl(null)).toBe("/tcg-icons/other.png");
    expect(tcgIconUrl("")).toBe("/tcg-icons/other.png");
  });

  it("builds path from name", () => {
    expect(tcgIconUrl("Magic: The Gathering")).toBe("/tcg-icons/magic_the_gathering.png");
  });
});

describe("resolveAvatarUrl", () => {
  it("uses default placeholder", () => {
    expect(resolveAvatarUrl(null)).toBe(DEFAULT_AVATAR_URL);
    expect(resolveAvatarUrl("/api/v1/media/avatars/1")).toBe("/api/v1/media/avatars/1");
  });
});
