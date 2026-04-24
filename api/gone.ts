export const config = { runtime: 'edge' };

const BODY = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="robots" content="noindex,nofollow">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Listing removed | CreditDoc</title>
<style>
body{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;max-width:640px;margin:10vh auto;padding:2rem;color:#1a1a1a;line-height:1.6}
h1{font-size:1.5rem;margin-bottom:1rem}
a{color:#0b5ed7;text-decoration:none}
a:hover{text-decoration:underline}
.muted{color:#555;font-size:.95rem}
</style>
</head>
<body>
<h1>This listing has been removed</h1>
<p>The page you were looking for is no longer part of CreditDoc. We removed it because it wasn't a lender, bank, or credit organization.</p>
<p class="muted">CreditDoc focuses on banks, credit unions, and lending services.</p>
<p><a href="https://www.creditdoc.co/">Go to CreditDoc home &rarr;</a> &nbsp;&middot;&nbsp; <a href="https://www.creditdoc.co/categories/">Browse categories</a></p>
</body>
</html>`;

export default function handler(_request: Request) {
  return new Response(BODY, {
    status: 410,
    headers: {
      'content-type': 'text/html; charset=utf-8',
      'cache-control': 'public, max-age=3600, s-maxage=86400',
      'x-robots-tag': 'noindex, nofollow',
    },
  });
}
