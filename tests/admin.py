
import logging
import uuid
import requests
import yaml

log = logging.getLogger(__name__)

# Load configuration
with open('conf.yml') as f:
    config = yaml.safe_load(f)

ADMIN_URL = f"http://{config['admin_host']}:{config['admin_port']}"
TEST_TOKENS = {
    str(uuid.uuid4()): "test_user1",
    str(uuid.uuid4()): "test_user2"
}

def setup_module():
    """Setup module-level test fixtures."""
    # Create test tokens
    token_data = {"tokens": TEST_TOKENS}
    response = requests.post(f'{ADMIN_URL}/tokens', json=token_data)
    log.debug("Setup response: %s", response.text)
    assert response.status_code == 200, "Failed to create test tokens"

def teardown_module():
    """Teardown module-level test fixtures."""
    # Delete test tokens
    token_data = {"tokens": list(TEST_TOKENS.keys())}
    response = requests.delete(f'{ADMIN_URL}/tokens', json=token_data)
    assert response.status_code == 200, "Failed to delete test tokens"

def test_create_tokens():
    """Test creating new tokens."""
    new_token = str(uuid.uuid4())
    token_data = {"tokens": {new_token: "new_user"}}
    
    response = requests.post(f'{ADMIN_URL}/tokens', json=token_data)
    assert response.status_code == 200, "Failed to create new token"
    
    # Verify token was created
    response = requests.get(f'{ADMIN_URL}/tokens')
    assert response.status_code == 200
    tokens = response.json()
    all_tokens = [list(d.keys())[0] for d in tokens]
    assert new_token in all_tokens, "New token not found in token list"

def test_delete_tokens():
    """Test deleting tokens."""
    # Create a token to delete
    temp_token = str(uuid.uuid4())
    requests.post(f'{ADMIN_URL}/tokens', json={"tokens": {temp_token: "temp_user"}})
    
    # Delete the token
    response = requests.delete(f'{ADMIN_URL}/tokens', json={"tokens": [temp_token]})
    assert response.status_code == 200, "Failed to delete token"
    
    # Verify token was deleted
    response = requests.get(f'{ADMIN_URL}/tokens')
    assert response.status_code == 200
    tokens = response.json()
    all_tokens = [list(d.keys())[0] for d in tokens]
    assert temp_token not in all_tokens,  "Token was not deleted"

def test_list_tokens():
    """Test listing all tokens."""
    response = requests.get(f'{ADMIN_URL}/tokens')
    assert response.status_code == 200, "Failed to list tokens"
    
    tokens = response.json()
    assert isinstance(tokens, list), "Tokens should be a list"
    all_tokens = [list(d.keys())[0] for d in tokens]
    assert all(token in all_tokens for token in TEST_TOKENS.keys()), "Test tokens missing from list"

def test_usage_stats():
    """Test retrieving usage statistics."""
    periods = ["minutely", "hourly", "daily", "weekly", "monthly"]
    
    for period in periods:
        response = requests.get(f'{ADMIN_URL}/usage/{period}')
        assert response.status_code == 200, f"Failed to get {period} usage stats"
        
        stats = response.json()
        assert isinstance(stats, list), f"Expected list for {period} stats"
        if stats:  # Stats might be empty
            assert isinstance(stats[0], dict), f"Expected dict items in {period} stats"

def test_invalid_token_operations():
    """Test invalid token operations."""
    # Test creating invalid token
    response = requests.post(f'{ADMIN_URL}/tokens', json={"tokens": {"": "invalid"}})
    assert response.status_code != 200, "Should reject empty token"
    
    # Test token that's too short
    short_token = "a" * 31  # 31 characters
    response = requests.post(f'{ADMIN_URL}/tokens', json={"tokens": {short_token: "short_token_user"}})
    assert response.status_code == 400, "Should reject token shorter than 32 characters"
    assert "Token is too short" in response.text, "Error message should indicate token is too short"
    
    # Test deleting non-existent token
    response = requests.delete(f'{ADMIN_URL}/tokens', json={"tokens": ["non-existent-token"]})
    assert response.status_code == 200, "Deleting non-existent token should succeed"

def test_static_assets():
    """Test serving of static assets."""
    # Test index.html
    response = requests.get(f'{ADMIN_URL}/')
    assert response.status_code == 200
    assert 'text/html' in response.headers['Content-Type']
    assert '<title>Burgonet Gateway</title>' in response.text
    
    # Test logo.png
    response = requests.get(f'{ADMIN_URL}/logo.png')
    assert response.status_code == 200
    assert 'image/png' in response.headers['Content-Type']
    assert len(response.content) > 0

def test_invalid_routes():
    """Test handling of invalid routes."""
    # Test non-existent route
    response = requests.get(f'{ADMIN_URL}/nonexistent')
    assert response.status_code == 404
    assert response.json()['error'] == 'Not Found'
    
    # Test invalid method
    response = requests.post(f'{ADMIN_URL}/usage')
    assert response.status_code == 404

def test_invalid_json():
    """Test handling of invalid JSON requests."""
    # Test malformed JSON
    response = requests.post(
        f'{ADMIN_URL}/tokens',
        data='{"invalid": json}',
        headers={'Content-Type': 'application/json'}
    )
    assert response.status_code == 400
    assert 'Invalid JSON' in response.text

def test_usage_stats_edge_cases():
    """Test edge cases for usage statistics."""
    # Test empty usage stats
    response = requests.get(f'{ADMIN_URL}/usage')
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    
    # Test invalid period
    response = requests.get(f'{ADMIN_URL}/usage/invalid')
    assert response.status_code == 404


# TODO: Uncomment this test after implementing request timeout handling in the server deal with ServerApp
#  HTTPServerApp read_request_body to understand the issue
#
# def test_timeout_handling():
#     """Test request timeout handling."""
#     # Create a large payload that would timeout
#
#     large_payload = {"tokens": {str(uuid.uuid4()): "user" for _ in range(100)}}
#     print(large_payload)
#
#     #ADMIN_URL = "http://127.0.0.1:6190"
#     try:
#         response = requests.post(
#             f'{ADMIN_URL}/tokens',
#             json=large_payload,
#             timeout=0.1,  # Set very short timeout
#             stream=False
#
#         )
#         print(response.text)
#         assert response.status_code == 408  # Request Timeout
#     except requests.exceptions.Timeout:
#         pass  # Expected behavior
#
# [2025-01-23T12:06:36Z ERROR pingora_core::apps::http_app] HTTP server fails to read from downstream:  InvalidHTTPHeader context: buf: : \"user\", \"4a6ded51-06ae-45e6-b5d7-185364ea71c1\": \"user\", \"0c3f6e51-dab6-433a-8e39-0117876fa5a1\": \"user\", \"e9de0ff1-1359-44d9-95fe-454acd02f6cc\": \"user\", \"3d9a7f01-ca08-4fc5-b247-f3fee7dca23d\": \"user\", \"2aba677b-84d3-49f6-b581-b7f6050fd0c0\": \"user\", \"ba06d8e4-cc1b-4247-8e7d-d7fe3f361c8c\": \"user\", \"ad6e9d66-8522-4449-8f78-cdcdb993a86f\": \"user\", \"67fd8f87-8c16-4a0f-a91f-90f409f607cb\": \"user\", \"7fa84435-b2e7-4b6d-8757-8eb127614e62\": \"user\", \"4bfefe96-12a2-419a-9ab1-1874101d757b\": \"user\", \"bfadbdb0-f848-46f4-b16b-6a22c563add7\": \"user\", \"d00202c3-f84b-4546-b342-d6ae895c64b2\": \"user\", \"60c736ab-fd2f-44e7-8375-9af3186e0bd3\": \"user\", \"7a840fc7-62f9-4ebf-829c-306add182861\": \"user\", \"916a4fe3-dc49-431d-a32f-1a83d7b870df\": \"user\", \"70afd305-0194-4976-ade6-7e1b16b6410c\": \"user\", \"9b494da0-7b1c-4fbf-864c-bfd3a0880d56\": \"user\", \"faec0859-1f65-4836-981e-3f42e9fe249b\": \"user\", \"eac0833b-a2a1-441e-9531-4ffc2fb909a6\": \"user\"}} cause: invalid HTTP version
