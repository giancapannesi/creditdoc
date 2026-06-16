import type { Lender } from "./data";

type LenderDestination = Pick<Lender, "slug" | "affiliate_url" | "website_url">;

export function getLenderDestination(lender: LenderDestination): string {
  return lender.affiliate_url?.trim() || lender.website_url?.trim() || "";
}

export function buildLenderGoHref(lender: LenderDestination): string | null {
  return getLenderDestination(lender) ? `/go/${encodeURIComponent(lender.slug)}/` : null;
}

export function normalizeTelHref(phone?: string): string | null {
  if (!phone) return null;
  const cleaned = phone.trim().replace(/[^\d+]/g, "");
  return cleaned ? `tel:${cleaned}` : null;
}
