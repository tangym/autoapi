import pytest
import requests

def test_root_404():
    r = requests.get('http://localhost:5000')
    assert r.status_code == 404

def test_root():
    params = {'name': 'foo', 'age': 2}
    r = requests.get('http://localhost:5000', params=params)
    ids = [item['id'] for item in r.json()].sort()
    assert ids == [1, 2, 3]
