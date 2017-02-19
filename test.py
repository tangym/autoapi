import pytest
import requests

def test_url():
    r = requests.get('http://localhost:5000')
    assert r.status_code == 200 
