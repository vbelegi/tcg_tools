import QRCode from "qrcode";

export function enrollHref(token: { path: string; url: string | null }): string {
  if (token.url) return token.url;
  if (typeof window === "undefined") return token.path;
  return `${window.location.origin}${token.path}`;
}

export async function qrSvg(text: string): Promise<string> {
  return QRCode.toString(text, {
    type: "svg",
    margin: 1,
    width: 240,
    errorCorrectionLevel: "M",
    color: { dark: "#12081a", light: "#ffffff" },
  });
}
