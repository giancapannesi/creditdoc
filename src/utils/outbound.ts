import type { Lender } from "./data";

type LenderDestination = Pick<Lender, "slug" | "affiliate_url" | "website_url">;
type ReviewLinkCandidate = {
  slug?: string;
  category?: string;
  no_index?: boolean;
  processing_status?: string;
  review_status?: string;
};

export function getLenderDestination(lender: LenderDestination): string {
  return lender.affiliate_url?.trim() || lender.website_url?.trim() || "";
}

export function buildLenderGoHref(lender: LenderDestination): string | null {
  return getLenderDestination(lender) ? `/go/${encodeURIComponent(lender.slug)}/` : null;
}

export function isReviewLinkable(lender: ReviewLinkCandidate): boolean {
  if (!lender.slug) return false;
  if (lender.no_index === true) return false;

  if (lender.processing_status) {
    return lender.processing_status === "ready_for_index";
  }

  if (lender.review_status) {
    return lender.review_status === "published";
  }

  return true;
}

export function buildReviewHref(lender: ReviewLinkCandidate): string | null {
  return isReviewLinkable(lender) ? `/review/${encodeURIComponent(lender.slug)}/` : null;
}

const categoryRouteAliases: Record<string, string> = {
  "debt-consolidation": "debt-relief",
  "fix-my-credit": "credit-repair",
  "payday-loans": "payday-alternatives",
};

export function buildCategoryHref(category?: string): string {
  if (!category) return "/categories/credit-repair/";
  const canonicalCategory = categoryRouteAliases[category] || category;
  return `/categories/${encodeURIComponent(canonicalCategory)}/`;
}

export function buildLenderFallbackHref(lender: ReviewLinkCandidate): string {
  return buildCategoryHref(lender.category);
}

export function normalizeTelHref(phone?: string): string | null {
  if (!phone) return null;
  const cleaned = phone.trim().replace(/[^\d+]/g, "");
  return cleaned ? `tel:${cleaned}` : null;
}
