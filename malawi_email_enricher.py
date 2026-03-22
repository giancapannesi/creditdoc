#!/usr/bin/env python3
"""
Malawi Contact Email Enricher
Takes LinkedIn profiles, maps company → domain, generates email patterns,
validates via DNS MX checks. Zero cost.
"""

import json, os, re, csv, dns.resolver
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Known Malawi company → email domain mappings
# These are publicly available from company websites
COMPANY_DOMAINS = {
    # Banks
    'NBS Bank': 'nbs.mw',
    'National Bank of Malawi': 'natbank.co.mw',
    'Standard Bank': 'standardbank.co.mw',
    'FDH Bank': 'fdhbank.com',
    'FDH Financial Holdings': 'fdhbank.com',
    'First Capital Bank': 'firstcapitalbank.co.mw',
    'Ecobank': 'ecobank.com',
    'CDH Investment Bank': 'cdh.mw',
    'Reserve Bank of Malawi': 'rbm.mw',
    'Old Mutual': 'oldmutual.com',
    'NICO Holdings': 'nicogroup.mw',
    'NICO General Insurance': 'nicogroup.mw',
    'Madison Group of Companies': 'madison.co.mw',

    # Telecoms
    'Airtel Malawi': 'airtel.mw',
    'Airtel': 'airtel.mw',
    'TNM': 'tnm.co.mw',
    'Telekom Networks Malawi': 'tnm.co.mw',
    'Telekom Networks Malawi PLC': 'tnm.co.mw',
    'MTL': 'mtl.mw',

    # Energy & Utilities
    'ESCOM': 'escom.mw',
    'ESCOM Malawi Limited': 'escom.mw',
    'ESCOM Malawi': 'escom.mw',
    'Puma Energy': 'pumaenergy.com',
    'Total Energies': 'totalenergies.com',
    'TotalEnergies': 'totalenergies.com',

    # Agriculture & Manufacturing
    'Illovo Sugar Malawi': 'illovo.co.za',
    'Illovo Sugar Malawi plc': 'illovo.co.za',
    'Illovo Sugar': 'illovo.co.za',
    'Press Corporation': 'presscorp.com',
    'Press Corporation Limited': 'presscorp.com',
    'Limbe Leaf Tobacco': 'limbe-leaf.com',
    'Alliance One': 'aointl.com',
    'Alliance One Tobacco (Malawi)': 'aointl.com',
    'JTI': 'jti.com',
    'Sunseed Oil Limited': 'sunseedoil.com',
    'Mount Meru Group': 'mountmerugroup.com',

    # International NGOs
    'UNICEF': 'unicef.org',
    'UNDP': 'undp.org',
    'UNHCR': 'unhcr.org',
    'UNESCO': 'unesco.org',
    'WHO': 'who.int',
    'World Food Programme': 'wfp.org',
    'WFP': 'wfp.org',
    'World Bank': 'worldbank.org',
    'IMF': 'imf.org',
    'USAID': 'usaid.gov',
    'GIZ': 'giz.de',
    'GIZ Malawi': 'giz.de',
    'Deutsche Gesellschaft für Internationale Zusammenarbeit (GIZ) GmbH': 'giz.de',
    'DFID': 'fcdo.gov.uk',
    'British Council': 'britishcouncil.org',
    'Save the Children': 'savethechildren.org',
    'Oxfam': 'oxfam.org',
    'World Vision': 'wvi.org',
    'World Vision International': 'wvi.org',
    'ActionAid': 'actionaid.org',
    'CARE International': 'care.org',
    'Plan International': 'plan-international.org',
    'WaterAid': 'wateraid.org',
    'Habitat for Humanity': 'habitat.org',
    'Red Cross': 'redcross.org',
    'Concern Worldwide': 'concern.net',
    'Médecins Sans Frontières': 'msf.org',
    'MSF': 'msf.org',
    'Clinton Health Access Initiative': 'clintonhealthaccess.org',
    'Elizabeth Glaser Pediatric AIDS Foundation': 'pedaids.org',
    'Mennonite Central Committee': 'mcc.org',
    'AGRA': 'agra.org',
    'African Development Bank': 'afdb.org',
    'EU Delegation': 'eeas.europa.eu',
    'Irish Aid': 'irishaid.ie',
    'JICA': 'jica.go.jp',
    'Norwegian Embassy': 'norway.no',
    'CyberSafe Foundation': 'cybersafefoundation.org',

    # Government
    'ESCOM Malawi Limited': 'escom.mw',
    'Malawi Revenue Authority': 'mra.mw',
    'National Economic Empowerment Fund (NEEF)': 'neef.mw',
    'Malawi Communications Regulatory Authority': 'macra.org.mw',
    'Malawi University of Science and Technology': 'must.ac.mw',
    'University of Malawi': 'unima.mw',
    'Kamuzu University of Health Sciences': 'kuhes.ac.mw',

    # Corporates
    'Abbott': 'abbott.com',
    'Deloitte': 'deloitte.com',
    'KPMG': 'kpmg.com',
    'PwC': 'pwc.com',
    'EY': 'ey.com',
    'Ernst & Young': 'ey.com',
    'Amazon': 'amazon.com',
    'Lotus Resources': 'lotusresources.com.au',
    'Equip Group': 'equipgroup.org',
}


def has_mx_record(domain):
    """Check if a domain has MX records (can receive email)."""
    try:
        dns.resolver.resolve(domain, 'MX')
        return True
    except:
        return False


def generate_email_patterns(first_name, last_name, domain):
    """Generate common business email patterns."""
    f = first_name.lower().strip().split()[0] if first_name else ''  # First word only

    # Clean last name: remove credentials, titles, brackets
    l_raw = last_name or ''
    l_raw = re.sub(r'\(.*?\)', '', l_raw)  # Remove (MBA), (ACIM), etc.
    l_raw = re.sub(r',.*$', '', l_raw)     # Remove everything after comma
    l_raw = l_raw.strip()
    l = l_raw.lower().split()[-1] if l_raw else ''  # Last word

    if not f or not l or not domain:
        return []

    # Remove special chars
    f = re.sub(r'[^a-z]', '', f)
    l = re.sub(r'[^a-z]', '', l)

    # Skip if name part is a credential
    creds = {'mba', 'phd', 'msc', 'bsc', 'acim', 'fcca', 'cam', 'capm', 'pcc', 'cbmba', 'jnr', 'sr', 'jr'}
    if f in creds or l in creds:
        return []

    if not f or not l:
        return []

    patterns = [
        f'{f}.{l}@{domain}',        # john.smith@company.com (most common)
        f'{f}{l}@{domain}',          # johnsmith@company.com
        f'{f[0]}{l}@{domain}',       # jsmith@company.com
        f'{f}@{domain}',             # john@company.com
        f'{f[0]}.{l}@{domain}',      # j.smith@company.com
        f'{l}.{f}@{domain}',         # smith.john@company.com
    ]
    return patterns


def match_company_domain(company_name):
    """Try to match company name to a known domain."""
    if not company_name:
        return None

    # Exact match
    if company_name in COMPANY_DOMAINS:
        return COMPANY_DOMAINS[company_name]

    # Case-insensitive match
    lower = company_name.lower().strip()
    for k, v in COMPANY_DOMAINS.items():
        if k.lower() == lower:
            return v

    # Partial match (company name contains key or key contains company name)
    for k, v in COMPANY_DOMAINS.items():
        if k.lower() in lower or lower in k.lower():
            return v

    return None


def main():
    print("=" * 60)
    print("MALAWI CONTACT EMAIL ENRICHER")
    print("=" * 60)

    # Load all LinkedIn profiles
    all_profiles = []
    datasets = ['3VBmsBfMNAG0OD861', '9KMu0svsSfj8MYOlH', 'cJm8ynQcqGDyCMiOJ',
                'qQp1bJYjq9DEuhoBb', 'tbWSFDXqm5gaY9x3A', 'Ruxbx6X936qfdA6rE',
                'pw1lSwrsMlZZpjyR8', 'qB2hXQ0v4MQofrlHZ', '57SU8iMdbUi5Ns1bP',
                'dGhTJTSNfdDmXwS6x', 'ORRVN7v2PMp7KZHOR']

    for ds in datasets:
        f = f'/tmp/linkedin_{ds}.json'
        if os.path.exists(f):
            with open(f) as fh:
                all_profiles.extend(json.load(fh))

    # Deduplicate
    seen = set()
    unique = []
    for p in all_profiles:
        url = p.get('linkedinUrl', '')
        if url and url not in seen:
            seen.add(url)
            unique.append(p)

    print(f"\nLinkedIn profiles: {len(unique)}")

    # Check which company domains have valid MX records
    print("\nChecking company email domains...")
    valid_domains = {}
    checked = set()
    for domain in set(COMPANY_DOMAINS.values()):
        if domain not in checked:
            checked.add(domain)
            if has_mx_record(domain):
                valid_domains[domain] = True
            else:
                print(f"  WARNING: No MX for {domain}")

    print(f"  {len(valid_domains)}/{len(checked)} domains have valid MX records")

    # Enrich profiles
    enriched = 0
    no_domain = 0

    ngo_kw = ['ngo', 'non-profit', 'nonprofit', 'charity', 'foundation', 'humanitarian',
               'development', 'relief', 'welfare', 'unicef', 'usaid', 'undp', 'unfpa',
               'who', 'world bank', 'giz', 'dfid', 'jica', 'actionaid',
               'care international', 'save the children', 'oxfam', 'world vision',
               'mennonite', 'peace corps', 'red cross', 'plan international', 'wateraid',
               'embassy', 'british council', 'european union', 'afdb']

    gov_kw = ['government', 'ministry', 'council', 'parliament', 'judiciary', 'police',
               'army', 'defence', 'immigration', 'revenue', 'reserve bank', 'public service',
               'escom', 'water board', 'university']

    records = []
    for p in unique:
        first = p.get('firstName', '')
        last = p.get('lastName', '')
        headline = p.get('headline', '')

        company = ''
        title = ''
        cp = p.get('currentPosition', [])
        if isinstance(cp, list) and cp:
            company = cp[0].get('companyName', '')
            title = cp[0].get('title', '')

        if not company or not title:
            exp = p.get('experience', [])
            if isinstance(exp, list) and exp:
                if not company:
                    company = exp[0].get('companyName', exp[0].get('company', ''))
                if not title:
                    title = exp[0].get('title', '')

        if not title:
            title = headline.split('|')[0].split(' at ')[0].strip()[:80] if headline else ''
        if not company and headline and ' at ' in headline:
            company = headline.split(' at ')[-1].split('|')[0].strip()[:80]

        loc = p.get('location', {})
        city = loc.get('linkedinText', '')
        linkedin = p.get('linkedinUrl', '')

        # Find email domain
        domain = match_company_domain(company)
        email = ''
        if domain and domain in valid_domains:
            patterns = generate_email_patterns(first, last, domain)
            if patterns:
                email = patterns[0]  # Use most common pattern: first.last@domain
                enriched += 1
        else:
            no_domain += 1

        # Sector
        check_text = (str(company) + ' ' + str(title) + ' ' + str(headline)).lower()
        sector = 'Corporate'
        if any(kw in check_text for kw in ngo_kw):
            sector = 'NGO / Development'
        elif any(kw in check_text for kw in gov_kw):
            sector = 'Government'

        if first or last:
            records.append({
                'first_name': first,
                'last_name': last,
                'organization_name': company or '',
                'position': title or '',
                'phone': '',
                'email': email,
                'website': linkedin,
                'physical_address': '',
                'city': city,
                'sector': sector,
                'source_url': 'linkedin:apify'
            })

    # Load and append government/parliament data
    csv_path = os.path.join(SCRIPT_DIR, 'malawi_contacts.csv')
    existing = pd.read_csv(csv_path)
    gov_parl = existing[existing['sector'].isin(['Government', 'Parliament'])]

    linkedin_df = pd.DataFrame(records)
    combined = pd.concat([gov_parl, linkedin_df], ignore_index=True)

    # Deduplicate by name
    combined['_key'] = combined.apply(
        lambda r: f"{str(r['first_name']).lower().strip()}|{str(r['last_name']).lower().strip()}", axis=1
    )
    combined = combined.drop_duplicates(subset='_key', keep='first').drop(columns=['_key'])
    combined = combined.sort_values(['sector', 'organization_name', 'last_name'])

    combined.to_csv(csv_path, index=False, encoding='utf-8-sig')

    # Stats
    total_emails = combined['email'].fillna('').astype(str).str.strip().ne('').sum()

    print(f"\n{'=' * 60}")
    print(f"RESULTS")
    print(f"{'=' * 60}")
    print(f"Total contacts: {len(combined)}")
    print(f"\nBy sector:")
    for s, c in combined['sector'].value_counts().items():
        print(f"  {s:20s}: {c}")
    print(f"\nEmail enrichment:")
    print(f"  Matched to domain:  {enriched}/{len(unique)} ({enriched/len(unique)*100:.0f}%)")
    print(f"  No domain found:    {no_domain}/{len(unique)}")
    print(f"  Total with email:   {total_emails}/{len(combined)} ({total_emails/len(combined)*100:.0f}%)")

    # Show contacts WITH emails
    with_email = combined[combined['email'].fillna('').astype(str).str.strip().ne('')]
    print(f"\nContacts with emails ({len(with_email)}):")
    for _, r in with_email.iterrows():
        print(f"  {r['first_name']:15s} {r['last_name']:20s} | {str(r['organization_name'])[:25]:25s} | {r['email']}")

    print(f"\nSaved: {csv_path}")


if __name__ == '__main__':
    main()
