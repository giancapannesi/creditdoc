# Chain Pass-2 Enrichment — Pilot Diff Report (10 rows)

**Generated:** 2026-04-21 08:28 UTC
**Source:** Google Places API (New) Text Search
**DB writes:** NONE — review-only pilot

## Summary

- Rows queried: 10
- Places found: 10
- Errors: 0
- Avg facts per row: 3.3

## Per-row diff

### 1. `ace-cash-express-alhambra`

- **Brand:** ace-cash-express
- **DB address:** 1700 W Valley Blvd, Alhambra, CA 91803
- **DB phone:** +1 626-289-0152

**Pass 1 (current on creditdoc.co):**
> At 1700 W Valley Blvd, Alhambra, CA 91803, you'll find ACE Cash Express. Contact them at +1 626-289-0152.

**Places API raw (compact):**
```json
{
  "displayName": "ACE Cash Express",
  "formattedAddress": "1700 W Valley Blvd, Alhambra, CA 91803, USA",
  "nationalPhoneNumber": "(626) 289-0152",
  "businessStatus": "OPERATIONAL",
  "rating": 4.9,
  "userRatingCount": 499,
  "primaryTypeDisplayName": "Banking and Finance",
  "regularOpeningHours_weekdayDescriptions": [
    "Monday: 9:00\u202fAM\u2009\u2013\u20097:00\u202fPM",
    "Tuesday: 9:00\u202fAM\u2009\u2013\u20097:00\u202fPM",
    "Wednesday: 9:00\u202fAM\u2009\u2013\u20097:00\u202fPM",
    "Thursday: 9:00\u202fAM\u2009\u2013\u20097:00\u202fPM",
    "Friday: 9:00\u202fAM\u2009\u2013\u20097:00\u202fPM",
    "Saturday: 9:00\u202fAM\u2009\u2013\u20095:00\u202fPM",
    "Sunday: Closed"
  ],
  "location": {
    "latitude": 34.0770577,
    "longitude": -118.14224309999999
  },
  "neighborhood": null
}
```

**Facts usable (3):** hours=Mon-Fri 9:00 AM – 7:00 PM, rating=4.9/499, phone=+1 626-289-0152

**Proposed Pass 2 (173 chars):**
> ACE Cash Express at 1700 W Valley Blvd, Alhambra, CA 91803 is Mon-Fri 9:00 AM – 7:00 PM. Google reviewers rate the branch 4.9 stars across 499 reviews. Call +1 626-289-0152.

**Sanity checks:** phone match: ✓ | street# match: ✓

---

### 2. `advance-america-bakersfield-ca`

- **Brand:** advance-america
- **DB address:** 2600 Oswell St spc c, Bakersfield, CA 93306
- **DB phone:** +1 661-872-0686

**Pass 1 (current on creditdoc.co):**
> At 2600 Oswell St spc c, Bakersfield, CA 93306, you'll find Advance America. Call +1 661-872-0686.

**Places API raw (compact):**
```json
{
  "displayName": "Advance America",
  "formattedAddress": "2600 Oswell St spc c, Bakersfield, CA 93306, USA",
  "nationalPhoneNumber": "(661) 872-0686",
  "businessStatus": "OPERATIONAL",
  "rating": 5,
  "userRatingCount": 1303,
  "primaryTypeDisplayName": "Banking and Finance",
  "regularOpeningHours_weekdayDescriptions": [
    "Monday: 10:00\u202fAM\u2009\u2013\u20096:00\u202fPM",
    "Tuesday: 10:00\u202fAM\u2009\u2013\u20096:00\u202fPM",
    "Wednesday: 10:00\u202fAM\u2009\u2013\u20096:00\u202fPM",
    "Thursday: 10:00\u202fAM\u2009\u2013\u20096:00\u202fPM",
    "Friday: 10:00\u202fAM\u2009\u2013\u20096:00\u202fPM",
    "Saturday: 9:00\u202fAM\u2009\u2013\u20091:00\u202fPM",
    "Sunday: Closed"
  ],
  "location": {
    "latitude": 35.3925419,
    "longitude": -118.9504963
  },
  "neighborhood": null
}
```

**Facts usable (3):** hours=Mon-Fri 10:00 AM – 6:00 PM, rating=5.0/1303, phone=+1 661-872-0686

**Proposed Pass 2 (179 chars):**
> Advance America at 2600 Oswell St spc c, Bakersfield, CA 93306 is Mon-Fri 10:00 AM – 6:00 PM. Google reviewers rate the branch 5.0 stars across 1303 reviews. Call +1 661-872-0686.

**Sanity checks:** phone match: ✓ | street# match: ✓

---

### 3. `bank-of-america-financial-center-atlanta`

- **Brand:** bank-of-america-financial-center
- **DB address:** 3495 Cascade Rd, Atlanta, GA 30311
- **DB phone:** +1 404-699-3140

**Pass 1 (current on creditdoc.co):**
> At 3495 Cascade Rd, Atlanta, GA 30311, Bank of America Financial Center can be reached at +1 404-699-3140.

**Places API raw (compact):**
```json
{
  "displayName": "Bank of America Financial Center",
  "formattedAddress": "3495 Cascade Rd, Atlanta, GA 30311, USA",
  "nationalPhoneNumber": "(404) 699-3140",
  "businessStatus": "OPERATIONAL",
  "rating": 2.2,
  "userRatingCount": 38,
  "primaryTypeDisplayName": "Bank",
  "regularOpeningHours_weekdayDescriptions": [
    "Monday: 9:00\u202fAM\u2009\u2013\u20094:00\u202fPM",
    "Tuesday: 9:00\u202fAM\u2009\u2013\u20094:00\u202fPM",
    "Wednesday: 9:00\u202fAM\u2009\u2013\u20094:00\u202fPM",
    "Thursday: 9:00\u202fAM\u2009\u2013\u20094:00\u202fPM",
    "Friday: 9:00\u202fAM\u2009\u2013\u20094:00\u202fPM",
    "Saturday: Closed",
    "Sunday: Closed"
  ],
  "location": {
    "latitude": 33.723442,
    "longitude": -84.5003011
  },
  "neighborhood": null
}
```

**Facts usable (3):** hours=Mon-Fri 9:00 AM – 4:00 PM, rating=2.2/38, phone=+1 404-699-3140

**Proposed Pass 2 (184 chars):**
> Bank of America Financial Center at 3495 Cascade Rd, Atlanta, GA 30311 is Mon-Fri 9:00 AM – 4:00 PM. Google reviewers rate the branch 2.2 stars across 38 reviews. Call +1 404-699-3140.

**Sanity checks:** phone match: ✓ | street# match: ✓

---

### 4. `cash-america-pawn-apopka`

- **Brand:** cash-america-pawn
- **DB address:** 399 E Main St, Apopka, FL 32703
- **DB phone:** +1 407-886-6969

**Pass 1 (current on creditdoc.co):**
> At 399 E Main St, Apopka, FL 32703, you can reach Cash America Pawn at +1 407-886-6969.

**Places API raw (compact):**
```json
{
  "displayName": "Cash America Pawn",
  "formattedAddress": "399 E Main St, Apopka, FL 32703, USA",
  "nationalPhoneNumber": "(407) 886-6969",
  "businessStatus": "OPERATIONAL",
  "rating": 4.5,
  "userRatingCount": 137,
  "primaryTypeDisplayName": "Services",
  "regularOpeningHours_weekdayDescriptions": [
    "Monday: 9:00\u202fAM\u2009\u2013\u20096:00\u202fPM",
    "Tuesday: 9:00\u202fAM\u2009\u2013\u20096:00\u202fPM",
    "Wednesday: 9:00\u202fAM\u2009\u2013\u20096:00\u202fPM",
    "Thursday: 9:00\u202fAM\u2009\u2013\u20096:00\u202fPM",
    "Friday: 9:00\u202fAM\u2009\u2013\u20096:00\u202fPM",
    "Saturday: 9:00\u202fAM\u2009\u2013\u20096:00\u202fPM",
    "Sunday: 12:00\u2009\u2013\u20095:00\u202fPM"
  ],
  "location": {
    "latitude": 28.673292099999998,
    "longitude": -81.5029234
  },
  "neighborhood": null
}
```

**Facts usable (3):** hours=Mon-Fri 9:00 AM – 6:00 PM, rating=4.5/137, phone=+1 407-886-6969

**Proposed Pass 2 (167 chars):**
> Cash America Pawn at 399 E Main St, Apopka, FL 32703 is Mon-Fri 9:00 AM – 6:00 PM. Google reviewers rate the branch 4.5 stars across 137 reviews. Call +1 407-886-6969.

**Sanity checks:** phone match: ✓ | street# match: ✓

---

### 5. `chase-bank-brooklyn-ny`

- **Brand:** chase-bank
- **DB address:** 177 Montague St, Brooklyn, NY 11201
- **DB phone:** +1 718-330-1356

**Pass 1 (current on creditdoc.co):**
> At 177 Montague St, Brooklyn, NY 11201, Chase Bank can be reached at +1 718-330-1356.

**Places API raw (compact):**
```json
{
  "displayName": "Chase Bank",
  "formattedAddress": "177 Montague St, Brooklyn, NY 11201, USA",
  "nationalPhoneNumber": "(718) 330-1356",
  "businessStatus": "OPERATIONAL",
  "rating": 3.2,
  "userRatingCount": 43,
  "primaryTypeDisplayName": "Bank",
  "regularOpeningHours_weekdayDescriptions": [
    "Monday: 9:00\u202fAM\u2009\u2013\u20095:00\u202fPM",
    "Tuesday: 9:00\u202fAM\u2009\u2013\u20095:00\u202fPM",
    "Wednesday: 9:00\u202fAM\u2009\u2013\u20095:00\u202fPM",
    "Thursday: 9:00\u202fAM\u2009\u2013\u20095:00\u202fPM",
    "Friday: 9:00\u202fAM\u2009\u2013\u20095:00\u202fPM",
    "Saturday: 9:00\u202fAM\u2009\u2013\u20092:00\u202fPM",
    "Sunday: Closed"
  ],
  "location": {
    "latitude": 40.694373,
    "longitude": -73.992183
  },
  "neighborhood": "Brooklyn Heights"
}
```

**Facts usable (4):** neighborhood=Brooklyn Heights, hours=Mon-Fri 9:00 AM – 5:00 PM, rating=3.2/43, phone=+1 718-330-1356

**Proposed Pass 2 (200 chars):**
> Chase Bank at 177 Montague St, Brooklyn, NY 11201 in the Brooklyn Heights neighborhood is Mon-Fri 9:00 AM – 5:00 PM. Google reviewers rate the branch 3.2 stars across 43 reviews. Call +1 718-330-1356.

**Sanity checks:** phone match: ✓ | street# match: ✓

---

### 6. `check-into-cash-bullhead-city`

- **Brand:** check-into-cash
- **DB address:** 1751 AZ-95 Suite 203, Bullhead City, AZ 86442
- **DB phone:** +1 928-704-1108

**Pass 1 (current on creditdoc.co):**
> At 1751 AZ-95 Suite 203, Bullhead City, AZ 86442, Check Into Cash can be reached at +1 928-704-1108.

**Places API raw (compact):**
```json
{
  "displayName": "Check Into Cash",
  "formattedAddress": "1751 AZ-95 Suite 203, Bullhead City, AZ 86442, USA",
  "nationalPhoneNumber": "(928) 704-1108",
  "businessStatus": "OPERATIONAL",
  "rating": 4.9,
  "userRatingCount": 402,
  "primaryTypeDisplayName": "Banking and Finance",
  "regularOpeningHours_weekdayDescriptions": [
    "Monday: 9:00\u202fAM\u2009\u2013\u20097:00\u202fPM",
    "Tuesday: 9:00\u202fAM\u2009\u2013\u20096:00\u202fPM",
    "Wednesday: 9:00\u202fAM\u2009\u2013\u20096:00\u202fPM",
    "Thursday: 9:00\u202fAM\u2009\u2013\u20096:00\u202fPM",
    "Friday: 9:00\u202fAM\u2009\u2013\u20097:00\u202fPM",
    "Saturday: 10:00\u202fAM\u2009\u2013\u20094:00\u202fPM",
    "Sunday: Closed"
  ],
  "location": {
    "latitude": 35.122113399999996,
    "longitude": -114.58739609999999
  },
  "neighborhood": null
}
```

**Facts usable (2):** rating=4.9/402, phone=+1 928-704-1108

**Proposed Pass 2 (161 chars):**
> Check Into Cash is located at 1751 AZ-95 Suite 203, Bullhead City, AZ 86442. Google reviewers rate the branch 4.9 stars across 402 reviews. Call +1 928-704-1108.

**Sanity checks:** phone match: ✓ | street# match: ✓

---

### 7. `ezpawn-austin`

- **Brand:** ezpawn
- **DB address:** 5203 Cameron Rd Unit A, Austin, TX 78723
- **DB phone:** +1 512-451-4021

**Pass 1 (current on creditdoc.co):**
> At 5203 Cameron Rd Unit A, Austin, TX 78723, EZPAWN can be reached at +1 512-451-4021.

**Places API raw (compact):**
```json
{
  "displayName": "EZPAWN",
  "formattedAddress": "5203 Cameron Rd Unit A, Austin, TX 78723, USA",
  "nationalPhoneNumber": "(512) 451-4021",
  "businessStatus": "OPERATIONAL",
  "rating": 4.7,
  "userRatingCount": 458,
  "primaryTypeDisplayName": "Services",
  "regularOpeningHours_weekdayDescriptions": [
    "Monday: 9:00\u202fAM\u2009\u2013\u20097:00\u202fPM",
    "Tuesday: 9:00\u202fAM\u2009\u2013\u20097:00\u202fPM",
    "Wednesday: 9:00\u202fAM\u2009\u2013\u20097:00\u202fPM",
    "Thursday: 9:00\u202fAM\u2009\u2013\u20097:00\u202fPM",
    "Friday: 9:00\u202fAM\u2009\u2013\u20097:00\u202fPM",
    "Saturday: 9:00\u202fAM\u2009\u2013\u20096:00\u202fPM",
    "Sunday: 12:00\u2009\u2013\u20095:00\u202fPM"
  ],
  "location": {
    "latitude": 30.310278900000004,
    "longitude": -97.708187
  },
  "neighborhood": "Windsor Park"
}
```

**Facts usable (4):** neighborhood=Windsor Park, hours=Mon-Fri 9:00 AM – 7:00 PM, rating=4.7/458, phone=+1 512-451-4021

**Proposed Pass 2 (198 chars):**
> EZPAWN at 5203 Cameron Rd Unit A, Austin, TX 78723 in the Windsor Park neighborhood is Mon-Fri 9:00 AM – 7:00 PM. Google reviewers rate the branch 4.7 stars across 458 reviews. Call +1 512-451-4021.

**Sanity checks:** phone match: ✓ | street# match: ✓

---

### 8. `moneygram-albuquerque-nm`

- **Brand:** moneygram
- **DB address:** 1820 Unser Blvd NW, Albuquerque, NM 87120
- **DB phone:** +1 505-600-4293

**Pass 1 (current on creditdoc.co):**
> At 1820 Unser Blvd NW, Albuquerque, NM 87120, MoneyGram can be reached at +1 505-600-4293.

**Places API raw (compact):**
```json
{
  "displayName": "Walmart Neighborhood Market",
  "formattedAddress": "1820 Unser Blvd NW, Albuquerque, NM 87120, USA",
  "nationalPhoneNumber": "(505) 600-4293",
  "businessStatus": "OPERATIONAL",
  "rating": 4,
  "userRatingCount": 2080,
  "primaryTypeDisplayName": "Grocery Store",
  "regularOpeningHours_weekdayDescriptions": [
    "Monday: 6:00\u202fAM\u2009\u2013\u200911:00\u202fPM",
    "Tuesday: 6:00\u202fAM\u2009\u2013\u200911:00\u202fPM",
    "Wednesday: 6:00\u202fAM\u2009\u2013\u200911:00\u202fPM",
    "Thursday: 6:00\u202fAM\u2009\u2013\u200911:00\u202fPM",
    "Friday: 6:00\u202fAM\u2009\u2013\u200911:00\u202fPM",
    "Saturday: 6:00\u202fAM\u2009\u2013\u200911:00\u202fPM",
    "Sunday: 6:00\u202fAM\u2009\u2013\u200911:00\u202fPM"
  ],
  "location": {
    "latitude": 35.103050599999996,
    "longitude": -106.7283702
  },
  "neighborhood": "Laurelwoods"
}
```

**Facts usable (4):** neighborhood=Laurelwoods, hours=open 6:00 AM – 11:00 PM daily, rating=4.0/2080, phone=+1 505-600-4293

**Proposed Pass 2 (206 chars):**
> MoneyGram at 1820 Unser Blvd NW, Albuquerque, NM 87120 in the Laurelwoods neighborhood is open 6:00 AM – 11:00 PM daily. Google reviewers rate the branch 4.0 stars across 2080 reviews. Call +1 505-600-4293.

**Sanity checks:** phone match: ✓ | street# match: ✓

---

### 9. `titlemax-title-loans-arlington-tx`

- **Brand:** titlemax-title-loans
- **DB address:** 1112 N Collins St, Arlington, TX 76011
- **DB phone:** +1 817-460-1433

**Pass 1 (current on creditdoc.co):**
> At 1112 N Collins St, Arlington, TX 76011, TitleMax Title Loans can be reached at +1 817-460-1433.

**Places API raw (compact):**
```json
{
  "displayName": "TitleMax Title Loans",
  "formattedAddress": "1112 N Collins St, Arlington, TX 76011, USA",
  "nationalPhoneNumber": "(817) 460-1433",
  "businessStatus": "OPERATIONAL",
  "rating": 4.9,
  "userRatingCount": 1193,
  "primaryTypeDisplayName": "Banking and Finance",
  "regularOpeningHours_weekdayDescriptions": [
    "Monday: 10:00\u202fAM\u2009\u2013\u20097:00\u202fPM",
    "Tuesday: 10:00\u202fAM\u2009\u2013\u20097:00\u202fPM",
    "Wednesday: 10:00\u202fAM\u2009\u2013\u20097:00\u202fPM",
    "Thursday: 10:00\u202fAM\u2009\u2013\u20097:00\u202fPM",
    "Friday: 10:00\u202fAM\u2009\u2013\u20097:00\u202fPM",
    "Saturday: 10:00\u202fAM\u2009\u2013\u20094:00\u202fPM",
    "Sunday: Closed"
  ],
  "location": {
    "latitude": 32.7526114,
    "longitude": -97.09769050000001
  },
  "neighborhood": "Central Arlington"
}
```

**Facts usable (4):** neighborhood=Central Arlington, hours=Mon-Fri 10:00 AM – 7:00 PM, rating=4.9/1193, phone=+1 817-460-1433

**Proposed Pass 2 (217 chars):**
> TitleMax Title Loans at 1112 N Collins St, Arlington, TX 76011 in the Central Arlington neighborhood is Mon-Fri 10:00 AM – 7:00 PM. Google reviewers rate the branch 4.9 stars across 1193 reviews. Call +1 817-460-1433.

**Sanity checks:** phone match: ✓ | street# match: ✓

---

### 10. `western-union-albuquerque-nm`

- **Brand:** western-union
- **DB address:** 3701 Constitution Ave NE, Albuquerque, NM 87110
- **DB phone:** +1 505-256-9423

**Pass 1 (current on creditdoc.co):**
> At 3701 Constitution Ave NE, Albuquerque, NM 87110, Western Union offers check cashing and money transfer services. Call +1 505-256-9423.

**Places API raw (compact):**
```json
{
  "displayName": "Western Union",
  "formattedAddress": "3701 Constitution Ave NE, Albuquerque, NM 87110, USA",
  "nationalPhoneNumber": "(505) 256-9423",
  "businessStatus": "OPERATIONAL",
  "rating": 5,
  "userRatingCount": 1,
  "primaryTypeDisplayName": "Banking and Finance",
  "regularOpeningHours_weekdayDescriptions": [
    "Monday: 6:00\u202fAM\u2009\u2013\u200910:00\u202fPM",
    "Tuesday: 6:00\u202fAM\u2009\u2013\u200910:00\u202fPM",
    "Wednesday: 6:00\u202fAM\u2009\u2013\u200910:00\u202fPM",
    "Thursday: 6:00\u202fAM\u2009\u2013\u200910:00\u202fPM",
    "Friday: 6:00\u202fAM\u2009\u2013\u200910:00\u202fPM",
    "Saturday: 6:00\u202fAM\u2009\u2013\u200910:00\u202fPM",
    "Sunday: 6:00\u202fAM\u2009\u2013\u200910:00\u202fPM"
  ],
  "location": {
    "latitude": 35.095349299999995,
    "longitude": -106.60269849999999
  },
  "neighborhood": "Altura Addition"
}
```

**Facts usable (3):** neighborhood=Altura Addition, hours=open 6:00 AM – 10:00 PM daily, phone=+1 505-256-9423

**Proposed Pass 2 (156 chars):**
> Western Union at 3701 Constitution Ave NE, Albuquerque, NM 87110 in the Altura Addition neighborhood is open 6:00 AM – 10:00 PM daily. Call +1 505-256-9423.

**Sanity checks:** phone match: ✓ | street# match: ✓

---

## What this pilot does NOT do

- No DB writes
- No JSON rewrites
- No commits
- No deploys

## If Jammi approves

Next step: batch-100 writer with DB update via `creditdoc_db.update_lender(force=True, updated_by='chain_enricher_pass2')`, 
check-in after every 100, halt on >15% phone mismatch / street# mismatch / <2 facts per row.
