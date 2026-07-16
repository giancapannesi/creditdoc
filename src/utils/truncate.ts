/**
 * Word-boundary aware truncation for SEO title / meta description output.
 *
 * The naive `text.slice(0, N)` truncation cuts mid-word and can chop off
 * high-value keywords (city/state suffixes especially). These helpers cut at
 * the last whitespace before the limit and add an ellipsis so Google shows
 * the truncation cleanly rather than a mangled fragment.
 *
 * Used from `src/pages/review/[slug].astro`, `src/pages/answers/[slug].astro`,
 * and any other template that assembles SEO fields from long DB strings.
 */

const ELLIPSIS = '…';

/**
 * Word-boundary aware truncation with ellipsis.
 *
 * - If `text` fits in `maxLen`, return as-is.
 * - Otherwise cut at the last whitespace at or before `maxLen - 1` and append
 *   an ellipsis. Total length is `<= maxLen`.
 * - If there is no whitespace inside the limit (single long token) fall back
 *   to a hard slice + ellipsis.
 */
export function truncateSmart(text: string, maxLen: number): string {
  if (!text) return '';
  const clean = text.trim();
  if (clean.length <= maxLen) return clean;

  // Budget one char for the ellipsis.
  const budget = maxLen - 1;
  const window = clean.slice(0, budget);
  const lastSpace = window.lastIndexOf(' ');

  // If we found a word boundary in the last 15 chars of the window use it;
  // otherwise the single-token case, hard-cut.
  const cutAt = lastSpace > budget - 15 ? lastSpace : budget;
  return clean.slice(0, cutAt).replace(/[\s,;:.\-–—]+$/, '') + ELLIPSIS;
}

/**
 * Title-with-suffix truncation. Preserves the high-value suffix (e.g. `in
 * Miami, FL`) by truncating the leading `name` if necessary.
 *
 * Priority when it doesn't all fit:
 *   1. If `suffix` alone is under `maxLen`, keep it in full and shrink `name`.
 *   2. If `suffix` is itself too long, fall back to `truncateSmart(name +
 *      suffix, maxLen)`.
 *   3. If name shrinks to nothing, drop the leading ellipsis to avoid
 *      starting the title with the ellipsis character.
 *
 * The joiner between name and suffix is emitted as-is (typical caller passes
 * `` ` in ${city}, ${state}` `` with a leading space).
 */
export function truncateTitleWithSuffix(
  name: string,
  suffix: string,
  maxLen: number,
): string {
  const full = `${name}${suffix}`.trim();
  if (full.length <= maxLen) return full;

  const cleanSuffix = suffix.trimStart();
  // Reserve space for a single leading space if suffix has one, ellipsis, and
  // the suffix itself.
  const reservedForTail = cleanSuffix.length + 2; // + ' ' + '…'
  if (reservedForTail >= maxLen) {
    // Suffix + tail doesn't leave room for meaningful name; fall back.
    return truncateSmart(full, maxLen);
  }

  const nameBudget = maxLen - reservedForTail;
  const nameTrim = name.trim();
  if (nameTrim.length <= nameBudget) {
    // Name already fits; the whole string was over budget only because of an
    // odd combination. Return it as truncateSmart would.
    return truncateSmart(full, maxLen);
  }

  const nameWindow = nameTrim.slice(0, nameBudget);
  const lastSpace = nameWindow.lastIndexOf(' ');
  const nameCutAt = lastSpace > nameBudget - 15 ? lastSpace : nameBudget;
  const nameOut = nameTrim.slice(0, nameCutAt).replace(/[\s,;:.\-–—]+$/, '');
  if (!nameOut) return truncateSmart(full, maxLen);

  return `${nameOut}${ELLIPSIS} ${cleanSuffix}`;
}
