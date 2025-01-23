import logging
import uuid

import requests
import yaml

log = logging.getLogger(__name__)
# Load configuration
with open('conf.yml') as f:
    config = yaml.safe_load(f)

# Test configuration
ADMIN_URL = f"http://{config['admin_host']}:{config['admin_port']}"
API_URL = f"http://{config['host']}:{config['port']}/ollama/gemma2/2b/"
TEST_TOKEN = str(uuid.uuid4())
HEADERS = {
    'Authorization': f'Bearer {TEST_TOKEN}',
}

log.info(f"Admin URL: {ADMIN_URL}")
log.info(f"API URL: {API_URL}")
log.info(f"Test token: {TEST_TOKEN}")
log.info(f"Headers: {HEADERS}")

data = {
    "model": "gemma2:2b-instruct-q6_K",
    "messages": [
        {
            "role": "user",
            "content": "Hi"
        }
    ],
    "stream": False
}
def setup_module():
    """Setup module-level test fixtures.
    
    Creates a test token that will be used by all test functions.
    This runs once before any tests in this module are executed.
    """
    token_data = {
        "tokens": {TEST_TOKEN : "test_user"}
    }
    response = requests.post(f'{ADMIN_URL}/tokens', json=token_data)
    log.debug("Response setup test token: %s", response.text)
    assert response.status_code == 200, "Failed to create test token"

def teardown_module():
    """Teardown module-level test fixtures.
    
    Deletes the test token created during setup.
    This runs once after all tests in this module have completed.
    """
    token_data = {
        "tokens": [TEST_TOKEN]
    }
    response = requests.delete(f'{ADMIN_URL}/tokens', json=token_data)
    assert response.status_code == 200, "Failed to delete test token"

def test_invalid_token():
    """Test authentication with an invalid token.
    
    Verifies that the API rejects requests with invalid tokens
    by returning a 401 Unauthorized status code.
    """
    log.info("test_invalid_token: Testing invalid token")
    headers = {
        'Authorization': 'Bearer invalid-token',
    }
    log.debug(f"Request headers: {headers}")
    log.debug(f"Request data: {data}")
    response = requests.post(API_URL, headers=headers, json=data)
    log.debug(f"Response status: {response.status_code}")
    log.debug(f"Response text: {response.text}")
    assert response.status_code == 401, response.text
    log.info("test_invalid_token: Invalid token test passed")

def test_valid_token():
    """Test authentication with a valid token.
    
    Verifies that the API accepts requests with valid tokens
    by returning a 200 OK status code and a valid response.
    """
    log.info("test_valid_token: Testing valid token")
    log.debug(f"Request headers: {HEADERS}")
    log.debug(f"Request data: {data}")
    response = requests.post(API_URL, headers=HEADERS, json=data)
    log.debug(f"Response status: {response.status_code}")
    log.debug(f"Response text: {response.text}")
    assert response.status_code == 200, response.text
    log.info("test_valid_token: Valid token test passed")
    print(response.json())

def test_pii_protection():
    """Test PII (Personally Identifiable Information) protection.
    
    Verifies that the API detects and rejects requests containing
    PII by returning a 403 Forbidden status code.
    """
    log.info("test_pii_protection: Testing PII protection")

    pii_data = {
        "model": "gemma2:2b-instruct-q6_K",
        "messages": [
            {
                "role": "user",
                "content": "Hi my name is Jean Claude Duss"
            }
        ],
        "stream": False
    }
    
    log.debug(f"Request headers: {HEADERS}")
    log.debug(f"Request data: {pii_data}")
    response = requests.post(API_URL, headers=HEADERS, json=pii_data)
    log.debug(f"Response status: {response.status_code}")
    log.debug(f"Response text: {response.text}")
    
    # Expecting a 429 error for PII violation
    assert response.status_code == 403, "Expected PII protection to reject the request"
    log.info("test_pii_protection: PII protection test passed")

def test_blacklisted_word():
    """Test blacklisted word protection.
    
    Verifies that the API detects and rejects requests containing
    blacklisted words by returning a 403 Forbidden status code.
    """
    log.info("test_blacklisted_word: Testing blacklisted word protection")

    blacklisted_data = {
        "model": "gemma2:2b-instruct-q6_K",
        "messages": [
            {
                "role": "user",
                "content": "Data report Confidential-UnitFinance"
            }
        ],
        "stream": False
    }
    
    log.debug(f"Request headers: {HEADERS}")
    log.debug(f"Request data: {blacklisted_data}")
    response = requests.post(API_URL, headers=HEADERS, json=blacklisted_data)
    log.debug(f"Response status: {response.status_code}")
    log.debug(f"Response text: {response.text}")
    
    # Expecting a 429 error for blacklisted word violation
    assert response.status_code == 403, "Expected blacklist protection to reject the request"
    log.info("test_blacklisted_word: Blacklisted word test passed")

def test_pii_protection_long_text():
    """Test PII protection with long input text.
    
    Verifies that the API can detect PII even in very long text
    inputs by returning a 403 Forbidden status code when PII is present.
    """
    log.info("test_pii_protection_long_text: Testing PII protection with long text")

    long_text = LOREM * 100
    long_text += """ But seriously, my name is Jean Claude Duss and I live at 123 Main Street."""
    log.info(f"Long text length: {len(long_text)} characters, so around {len(long_text) / 3,000} A4 pages")
    
    pii_data = {
        "model": "gemma2:2b-instruct-q6_K",
        "messages": [
            {
                "role": "user",
                "content": long_text
            }
        ],
        "stream": False
    }
    
    log.debug(f"Request headers: {HEADERS}")
    log.debug(f"Request data length: {len(long_text)} characters")
    response = requests.post(API_URL, headers=HEADERS, json=pii_data)
    log.debug(f"Response status: {response.status_code}")
    log.debug(f"Response text: {response.text}")
    
    # Expecting a 403 error for PII violation
    assert response.status_code == 403, "Expected PII protection to reject the request with long text"
    log.info("test_pii_protection_long_text: PII protection with long text test passed")

def test_long_text_without_pii():
    """Test handling of long text without PII.
    
    Verifies that the API can successfully process very long text
    inputs when they don't contain PII by returning a 200 OK status code.
    """
    log.info("test_long_text_without_pii: Testing long text without PII")

    long_text = LOREM * 100
    log.info(f"Long text length: {len(long_text)} characters, so around {len(long_text) / 3,000} A4 pages")
    
    long_text_data = {
        "model": "gemma2:2b-instruct-q6_K",
        "messages": [
            {
                "role": "user",
                "content": long_text
            }
        ],
        "stream": False
    }
    
    log.debug(f"Request headers: {HEADERS}")
    log.debug(f"Request data length: {len(long_text)} characters")
    response = requests.post(API_URL, headers=HEADERS, json=long_text_data)
    log.debug(f"Response status: {response.status_code}")
    log.debug(f"Response text: {response.text}")
    
    # Expecting a 200 success since there's no PII
    assert response.status_code == 200, "Expected successful response for long text without PII"
    log.info("test_long_text_without_pii: Long text without PII test passed")


LOREM = """
    Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. 
    Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. 
    Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. 
    Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
    Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, 
    eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo. 
    Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt. 
    Neque porro quisquam est, qui dolorem ipsum quia dolor sit amet, consectetur, adipisci velit, sed quia non numquam eius modi tempora incidunt ut labore et dolore magnam aliquam quaerat voluptatem. 
    Ut enim ad minima veniam, quis nostrum exercitationem ullam corporis suscipit laboriosam, nisi ut aliquid ex ea commodi consequatur? 
    Quis autem vel eum iure reprehenderit qui in ea voluptate velit esse quam nihil molestiae consequatur, vel illum qui dolorem eum fugiat quo voluptas nulla pariatur?
    """