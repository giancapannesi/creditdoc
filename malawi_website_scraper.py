#!/usr/bin/env python3
"""
Scrape company/NGO websites for contact info (emails, phones).
Uses Google search to find the website, then scrapes contact/about/team pages.
Zero cost — just HTTP requests.
"""

import re, json, os, time, sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# Known company websites (saves Google searches)
KNOWN_SITES = {
    'NBS Bank': 'https://www.nbs.mw',
    'National Bank of Malawi': 'https://www.natbank.co.mw',
    'Standard Bank': 'https://www.standardbank.co.mw',
    'FDH Bank': 'https://www.fdhbank.com',
    'FDH Financial Holdings': 'https://www.fdhbank.com',
    'First Capital Bank': 'https://www.firstcapitalbank.co.mw',
    'CDH Investment Bank': 'https://www.cdh.mw',
    'Reserve Bank of Malawi': 'https://www.rbm.mw',
    'Old Mutual': 'https://www.oldmutual.co.mw',
    'NICO Holdings': 'https://www.nicogroup.mw',
    'Madison Group of Companies': 'https://www.madison.co.mw',
    'Airtel Malawi': 'https://www.airtel.mw',
    'TNM': 'https://www.tnm.co.mw',
    'Telekom Networks Malawi': 'https://www.tnm.co.mw',
    'Telekom Networks Malawi PLC': 'https://www.tnm.co.mw',
    'ESCOM': 'https://www.escom.mw',
    'ESCOM Malawi Limited': 'https://www.escom.mw',
    'ESCOM Malawi': 'https://www.escom.mw',
    'Illovo Sugar Malawi plc': 'https://www.illovosugarafrica.com',
    'Illovo Sugar Malawi': 'https://www.illovosugarafrica.com',
    'Press Corporation': 'https://www.presscorp.com',
    'Puma Energy': 'https://www.pumaenergy.com',
    'JTI': 'https://www.jti.com',
    'Mount Meru Group': 'https://www.mountmerugroup.com',
    'UNICEF': 'https://www.unicef.org/malawi',
    'UNDP': 'https://www.undp.org/malawi',
    'UNHCR': 'https://www.unhcr.org/countries/malawi',
    'WHO': 'https://www.afro.who.int/countries/malawi',
    'World Food Programme': 'https://www.wfp.org/countries/malawi',
    'World Bank': 'https://www.worldbank.org/en/country/malawi',
    'USAID': 'https://www.usaid.gov/malawi',
    'GIZ Malawi': 'https://www.giz.de/en/worldwide/312.html',
    'Save the Children': 'https://malawi.savethechildren.net',
    'ActionAid': 'https://malawi.actionaid.org',
    'World Vision': 'https://www.wvi.org/malawi',
    'Plan International': 'https://plan-international.org/malawi',
    'WaterAid': 'https://www.wateraid.org/mw',
    'Concern Worldwide': 'https://www.concern.net/where-we-work/malawi',
    'AGRA': 'https://agra.org',
    'Malawi Revenue Authority': 'https://www.mra.mw',
    'Malawi University of Science and Technology': 'https://www.must.ac.mw',
    'University of Malawi': 'https://www.unima.mw',
    'MCCCI': 'https://www.mccci.org',
    'Elizabeth Glaser Pediatric AIDS Foundation': 'https://www.pedaids.org',
    'British Council': 'https://www.britishcouncil.mw',
    'Equip Group': 'https://www.equipgroup.org',
    'National Economic Empowerment Fund (NEEF)': 'https://www.neef.mw',
}

# Email regex
EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
# Phone regex (Malawi +265, also international)
PHONE_RE = re.compile(r'(?:\+\d{1,3}[\s.-]?)?\(?\d{2,4}\)?[\s.-]?\d{3,4}[\s.-]?\d{3,4}')


def extract_contacts_from_html(html, base_url=''):
    """Extract emails and phones from HTML content."""
    emails = set()
    phones = set()

    # Extract from text
    text = BeautifulSoup(html, 'lxml').get_text(separator=' ')

    for m in EMAIL_RE.finditer(text):
        email = m.group().lower().strip('.')
        # Skip common false positives
        if not any(x in email for x in ['example.com', 'sentry.io', 'wixpress', 'w3.org',
                                         'schema.org', 'wordpress', 'jquery', 'google.com',
                                         'facebook.com', 'twitter.com', '.png', '.jpg',
                                         '.gif', '.svg', '.css', '.js', 'noreply']):
            emails.add(email)

    for m in PHONE_RE.finditer(text):
        phone = m.group().strip()
        # Only keep if it has enough digits (at least 7)
        digits = re.sub(r'\D', '', phone)
        if len(digits) >= 7 and len(digits) <= 15:
            phones.add(phone)

    # Also check mailto: links and tel: links
    soup = BeautifulSoup(html, 'lxml')
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith('mailto:'):
            email = href.replace('mailto:', '').split('?')[0].lower().strip()
            if '@' in email:
                emails.add(email)
        elif href.startswith('tel:'):
            phone = href.replace('tel:', '').strip()
            if phone:
                phones.add(phone)

    return list(emails), list(phones)


def find_contact_pages(base_url, html):
    """Find links to contact, about, team pages."""
    soup = BeautifulSoup(html, 'lxml')
    contact_urls = set()

    keywords = ['contact', 'about', 'team', 'staff', 'leadership', 'management',
                'directory', 'people', 'our-team', 'meet-the-team', 'board',
                'executives', 'who-we-are']

    for a in soup.find_all('a', href=True):
        href = a['href'].lower()
        text = a.get_text(strip=True).lower()

        if any(kw in href or kw in text for kw in keywords):
            full_url = urljoin(base_url, a['href'])
            # Only follow links on same domain
            if urlparse(full_url).netloc == urlparse(base_url).netloc:
                contact_urls.add(full_url)

    return list(contact_urls)[:5]  # Max 5 subpages per site


def scrape_company(company_name, url):
    """Scrape a company website for contact info."""
    all_emails = set()
    all_phones = set()

    try:
        # Get homepage
        r = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        if r.status_code != 200:
            return company_name, [], []

        # Extract from homepage
        emails, phones = extract_contacts_from_html(r.text, url)
        all_emails.update(emails)
        all_phones.update(phones)

        # Find and scrape contact/about/team pages
        subpages = find_contact_pages(url, r.text)
        for suburl in subpages:
            try:
                sr = requests.get(suburl, headers=HEADERS, timeout=10)
                if sr.status_code == 200:
                    emails, phones = extract_contacts_from_html(sr.text, suburl)
                    all_emails.update(emails)
                    all_phones.update(phones)
            except:
                pass
            time.sleep(0.5)

    except Exception as e:
        pass

    return company_name, list(all_emails), list(all_phones)


def main():
    print("=" * 60)
    print("MALAWI COMPANY WEBSITE SCRAPER")
    print("=" * 60)

    results = {}
    total = len(KNOWN_SITES)

    print(f"\nScraping {total} company websites for contacts...\n")

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {}
        for company, url in KNOWN_SITES.items():
            f = executor.submit(scrape_company, company, url)
            futures[f] = company

        done = 0
        for future in as_completed(futures):
            done += 1
            company, emails, phones = future.result()
            results[company] = {'emails': emails, 'phones': phones}
            status = ''
            if emails:
                status += f"{len(emails)} emails"
            if phones:
                status += f", {len(phones)} phones" if status else f"{len(phones)} phones"
            if not status:
                status = "nothing found"
            print(f"  [{done}/{total}] {company[:40]:40s} — {status}")

    # Summary
    companies_with_email = sum(1 for r in results.values() if r['emails'])
    companies_with_phone = sum(1 for r in results.values() if r['phones'])
    total_emails = sum(len(r['emails']) for r in results.values())
    total_phones = sum(len(r['phones']) for r in results.values())

    print(f"\n{'=' * 60}")
    print(f"RESULTS")
    print(f"{'=' * 60}")
    print(f"Companies scraped:     {total}")
    print(f"With emails:           {companies_with_email}")
    print(f"With phones:           {companies_with_phone}")
    print(f"Total emails found:    {total_emails}")
    print(f"Total phones found:    {total_phones}")

    # Save results
    output = '/tmp/malawi_website_contacts.json'
    with open(output, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nDetailed results:")
    for company, data in sorted(results.items()):
        if data['emails'] or data['phones']:
            print(f"\n  {company}:")
            for e in data['emails'][:5]:
                print(f"    Email: {e}")
            for p in data['phones'][:3]:
                print(f"    Phone: {p}")

    print(f"\nSaved: {output}")


if __name__ == '__main__':
    main()
