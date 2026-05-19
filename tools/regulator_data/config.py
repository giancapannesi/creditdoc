import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..', '..'))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')

DB_PATH = os.path.join(DATA_DIR, 'regulator.db')

USER_AGENT = 'Creditdoc/1.0 (contact: gian.eao@gmail.com)'

CFPB_COMPLAINTS_API = 'https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1/'
CFPB_COMPLAINTS_PAGE_SIZE = 10000
CFPB_COMPLAINTS_RATE_LIMIT = 0.5  # seconds between requests

CFPB_ENFORCEMENT_URL = 'https://www.consumerfinance.gov/enforcement/actions/'

SBA_API_BASE = 'https://api.sba.gov/pro/api/v1/7a-504-loans/'

FDIC_INSTITUTIONS_CSV = os.path.join(os.path.dirname(PROJECT_ROOT), 'data', 'fdic', 'institutions.csv')
FDIC_LOCATIONS_CSV = os.path.join(os.path.dirname(PROJECT_ROOT), 'data', 'fdic', 'locations.csv')

LOG_DIR = os.path.join(os.path.dirname(PROJECT_ROOT), 'logs')
