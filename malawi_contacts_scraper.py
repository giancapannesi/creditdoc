#!/usr/bin/env python3
"""
Malawi Contacts Scraper
Scrapes government, parliament, and NGO contacts.
Output: malawi_contacts.csv

Sources:
1. malawi.gov.mw — Cabinet ministers
2. parliament.gov.mw — All MPs (paginated, Playwright)
3. CONGOMA — NGOs (when API available)
"""

import os, sys, re, json, time
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(SCRIPT_DIR, 'malawi_contacts.csv')


def clean_phone(phone):
    if not phone: return ''
    return re.sub(r'^tel:', '', str(phone).strip(), flags=re.IGNORECASE).strip()

def clean_email(email):
    if not email: return ''
    return str(email).strip().lower()

def split_name(full_name):
    if not full_name: return '', ''
    name = full_name.strip()
    # Remove honorifics
    name = re.sub(r'^(His Excellency|Right Honourable|Honourable|Hon\.?|Prof\.?|Professor|Dr\.?|Mr\.?|Mrs\.?|Ms\.?)\s+', '', name, flags=re.IGNORECASE)
    # Remove trailing credentials
    name = re.sub(r',?\s*(MP|M\s*P|SC|S\s*C|JA|Rtd|PhD)\.?\s*$', '', name, flags=re.IGNORECASE).strip()
    name = re.sub(r',?\s*(MP|M\s*P|SC|S\s*C|JA|Rtd)\.?\s*$', '', name, flags=re.IGNORECASE).strip()
    parts = name.split()
    if not parts: return '', ''
    if len(parts) == 1: return parts[0], ''
    return parts[0], ' '.join(parts[1:])


def scrape_government_cabinet():
    """Cabinet ministers from malawi.gov.mw — pure requests, no JS."""
    print("\n[1] Government Cabinet (malawi.gov.mw)...")
    records = []
    try:
        r = requests.get('https://www.malawi.gov.mw/index.php/60-executive', headers=HEADERS, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'lxml')
        content = soup.select_one('.item-page, article') or soup.find('body')
        text = content.get_text(separator='\n')
        lines = [l.strip() for l in text.split('\n') if l.strip()]

        in_cabinet = False
        title_line = None
        for line in lines:
            if 'The Cabinet List' in line:
                in_cabinet = True
                continue
            if 'HISTORY OF THE PRESIDENCY' in line:
                break
            if not in_cabinet:
                continue

            if any(kw in line for kw in ['President', 'Minister', 'Vice President', 'Commander']):
                title_line = line
            elif title_line and any(h in line for h in ['Honourable', 'Excellency', 'Right Honourable']):
                first, last = split_name(line)
                records.append({
                    'first_name': first, 'last_name': last,
                    'organization_name': 'Government of Malawi',
                    'position': title_line,
                    'phone': '', 'email': '',
                    'website': 'https://www.malawi.gov.mw',
                    'physical_address': 'Capital Hill, Lilongwe',
                    'city': 'Lilongwe', 'sector': 'Government',
                    'source_url': 'https://www.malawi.gov.mw/index.php/60-executive'
                })
                title_line = None

        print(f"  Found {len(records)} cabinet members")
    except Exception as e:
        print(f"  ERROR: {e}")
    return records


def scrape_parliament():
    """All MPs from parliament.gov.mw — JS pagination via click-through."""
    print("\n[2] Parliament MPs (parliament.gov.mw)...")
    records = []
    known_parties = ['UDF', 'DPP', 'MCP', 'UTM', 'AFORD', 'PP', 'Independent']

    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_extra_http_headers(HEADERS)

            page.goto('https://parliament.gov.mw/members/all', timeout=30000)
            page.wait_for_timeout(5000)

            seen_hrefs = set()
            page_num = 0

            while True:
                page_num += 1
                content = page.content()
                soup = BeautifulSoup(content, 'lxml')

                found = 0
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if '/members/' in href and '/member' in href and 'all' not in href and 'presiding' not in href:
                        lt = a.get_text(strip=True)
                        # Skip empty links (image wrappers) — only use the text link
                        if not lt:
                            continue
                        if href in seen_hrefs:
                            continue
                        seen_hrefs.add(href)
                        found += 1
                        full_url = f'https://parliament.gov.mw{href}' if href.startswith('/') else href

                        name = lt
                        party = ''
                        constituency = ''

                        for pt in known_parties:
                            if pt in lt:
                                idx = lt.index(pt)
                                name = lt[:idx].strip()
                                remaining = lt[idx + len(pt):]
                                party = pt
                                cohort_idx = remaining.find('Cohort')
                                if cohort_idx > 0:
                                    constituency = remaining[:cohort_idx].strip()
                                elif remaining:
                                    constituency = remaining.strip()
                                break

                        first, last = split_name(name)
                        position = 'Member of Parliament'
                        if constituency:
                            position = f'MP — {constituency}'
                        if party:
                            position += f' ({party})'

                        records.append({
                            'first_name': first, 'last_name': last,
                            'organization_name': 'National Assembly of Malawi',
                            'position': position,
                            'phone': '', 'email': '',
                            'website': full_url,
                            'physical_address': 'Parliament Building, Lilongwe',
                            'city': 'Lilongwe', 'sector': 'Parliament',
                            'source_url': full_url
                        })

                print(f"  Page {page_num}: {found} new MPs (total: {len(records)})")

                if found == 0 and page_num > 1:
                    break

                # Click Next button (JS pagination, no URL change)
                try:
                    next_btn = page.locator('a:has-text("Next"), a:has-text("»")').first
                    if next_btn.count() == 0:
                        break
                    next_btn.click()
                    page.wait_for_timeout(3000)
                except:
                    break

                if page_num >= 50:  # safety
                    break

            browser.close()
        print(f"  Total: {len(records)} MPs")
    except Exception as e:
        print(f"  ERROR: {e}")
    return records


def scrape_mccci():
    """MCCCI member directory — Playwright."""
    print("\n[3] MCCCI Directory (mccci.org)...")
    records = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_extra_http_headers(HEADERS)
            page.goto('https://www.mccci.org/directory-members', timeout=30000)
            page.wait_for_timeout(8000)

            for _ in range(10):
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                page.wait_for_timeout(800)

            content = page.content()
            soup = BeautifulSoup(content, 'lxml')

            # Find member post items
            posts = soup.select('.uc_post_list_box')
            for post in posts:
                title_el = post.select_one('h2, h3, .uc_post_title, a')
                name = title_el.get_text(strip=True) if title_el else ''
                link = ''
                a_tag = post.select_one('a[href]')
                if a_tag:
                    href = a_tag.get('href', '')
                    link = href if href.startswith('http') else f'https://www.mccci.org{href}'

                desc = ''
                desc_el = post.select_one('.uc_post_desc, p, .excerpt')
                if desc_el:
                    desc = desc_el.get_text(strip=True)[:200]

                if name and name not in ['Read More', 'Contact us', 'Menu']:
                    records.append({
                        'first_name': '', 'last_name': '',
                        'organization_name': name,
                        'position': 'MCCCI Member',
                        'phone': '', 'email': '',
                        'website': link or 'https://www.mccci.org',
                        'physical_address': '', 'city': '',
                        'sector': 'Corporate',
                        'source_url': 'https://www.mccci.org/directory-members'
                    })

            browser.close()
        print(f"  Found {len(records)} MCCCI members")
    except Exception as e:
        print(f"  ERROR: {e}")
    return records


def scrape_apify_leads(queries, max_results=500):
    """Use Apify leads-finder to get people contacts from Apollo-like data.
    Returns actual people with names, titles, emails, companies.
    Cost: ~$1.50 per 1K results.
    """
    print("\n[4] Apify Leads Finder (corporates & NGOs)...")
    records = []

    try:
        token = open('/srv/BusinessOps/tools/.apify-api-key').read().strip()
        actor_id = 'code_crafter~leads-finder'

        for query in queries:
            print(f"\n  Query: '{query}' (max {max_results})...")

            run_input = {
                'searchQuery': query,
                'maxResults': max_results,
                'includeEmails': True,
            }

            resp = requests.post(
                f'https://api.apify.com/v2/acts/{actor_id}/runs?token={token}',
                json=run_input, timeout=30
            )

            if resp.status_code in (402, 403):
                print(f"  Credits issue ({resp.status_code}). Skipping remaining queries.")
                break

            resp.raise_for_status()
            run_data = resp.json().get('data', {})
            run_id = run_data.get('id')
            dataset_id = run_data.get('defaultDatasetId')
            print(f"  Run ID: {run_id}")

            # Poll for completion (max 10 min)
            status = ''
            for attempt in range(120):
                time.sleep(5)
                sr = requests.get(
                    f'https://api.apify.com/v2/actor-runs/{run_id}?token={token}', timeout=15
                )
                status = sr.json().get('data', {}).get('status', '')

                if status == 'SUCCEEDED':
                    print(f"  Completed!")
                    break
                elif status in ('FAILED', 'ABORTED', 'TIMED-OUT'):
                    print(f"  {status}")
                    break
                if attempt % 12 == 11:
                    print(f"    Running... ({attempt * 5}s)")

            if status != 'SUCCEEDED':
                continue

            # Get dataset
            if not dataset_id:
                rd = requests.get(
                    f'https://api.apify.com/v2/actor-runs/{run_id}?token={token}', timeout=15
                ).json().get('data', {})
                dataset_id = rd.get('defaultDatasetId')

            items = []
            if dataset_id:
                ir = requests.get(
                    f'https://api.apify.com/v2/datasets/{dataset_id}/items?token={token}&format=json',
                    timeout=60
                )
                items = ir.json() if ir.ok else []

            print(f"  Results: {len(items)}")

            for item in items:
                first = item.get('firstName', item.get('first_name', ''))
                last = item.get('lastName', item.get('last_name', ''))
                full = item.get('name', item.get('fullName', ''))
                if not first and not last and full:
                    first, last = split_name(full)

                org = item.get('organization', item.get('company', item.get('companyName', '')))
                if isinstance(org, dict):
                    org = org.get('name', '')

                title = item.get('title', item.get('jobTitle', item.get('position', '')))

                email = item.get('email', item.get('emailAddress', ''))
                if isinstance(email, list):
                    email = email[0] if email else ''

                phone = item.get('phone', item.get('phoneNumber', ''))
                if isinstance(phone, list):
                    phone = phone[0] if phone else ''

                website = item.get('website', item.get('websiteUrl', item.get('companyUrl', '')))
                city = item.get('city', item.get('location', ''))
                address = item.get('address', '')

                sector = 'Corporate'
                ngo_kw = ['ngo', 'non-profit', 'nonprofit', 'charity', 'foundation', 'humanitarian', 'development', 'relief', 'welfare', 'un ', 'unicef', 'usaid']
                if any(kw in (str(org) + ' ' + str(title)).lower() for kw in ngo_kw):
                    sector = 'NGO'

                if first or last or org:
                    records.append({
                        'first_name': first or '',
                        'last_name': last or '',
                        'organization_name': org or '',
                        'position': title or '',
                        'phone': clean_phone(phone),
                        'email': clean_email(email),
                        'website': website or '',
                        'physical_address': address or '',
                        'city': city or '',
                        'sector': sector,
                        'source_url': f'apify:leads-finder'
                    })

            time.sleep(2)

    except Exception as e:
        print(f"  ERROR: {e}")

    print(f"\n  Total leads: {len(records)}")
    return records


def main():
    print("=" * 60)
    print("MALAWI CONTACTS SCRAPER")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    all_records = []
    source_counts = {}

    cabinet = scrape_government_cabinet()
    all_records.extend(cabinet)
    source_counts['Government Cabinet'] = len(cabinet)

    mps = scrape_parliament()
    all_records.extend(mps)
    source_counts['Parliament MPs'] = len(mps)

    # MCCCI and Apify disabled — MCCCI shows 0 members, Apify returns zero Malawi data
    # mccci = scrape_mccci()
    # all_records.extend(mccci)
    # source_counts['MCCCI Members'] = len(mccci)

    # Build DataFrame
    if not all_records:
        print("\nNo records found!")
        return

    df = pd.DataFrame(all_records)
    total_raw = len(df)

    # Deduplicate — use name+org+position to avoid collapsing different MPs
    df['_key'] = df.apply(lambda r: f"{r['first_name'].lower()}|{r['last_name'].lower()}|{r['organization_name'].lower()}|{r['position'].lower()}", axis=1)
    df = df.drop_duplicates(subset='_key', keep='first').drop(columns=['_key'])

    # Reorder columns
    cols = ['first_name', 'last_name', 'organization_name', 'position',
            'phone', 'email', 'website', 'physical_address', 'city',
            'sector', 'source_url']
    df = df[cols].sort_values(['sector', 'organization_name', 'last_name'])

    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for source, count in source_counts.items():
        print(f"  {source:25s}: {count:>5}")
    print(f"  {'Total raw':25s}: {total_raw:>5}")
    print(f"  {'After dedup':25s}: {len(df):>5}")
    print(f"\nBy sector:")
    for s, c in df['sector'].value_counts().items():
        print(f"  {s}: {c}")
    print(f"\nSaved: {OUTPUT_FILE}")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()
