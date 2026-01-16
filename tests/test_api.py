"""
Tests for FastAPI backend
Run with: pytest tests/test_api.py
"""

import pytest
from fastapi.testclient import TestClient
from api_server import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "cache_status" in data


def test_tle_fetch_endpoint():
    """Test TLE fetch endpoint"""
    payload = {
        "norad_ids": [25544, 48274],
        "use_cache": True
    }
    
    response = client.post("/api/tle/fetch", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "success" in data


def test_search_satellites():
    """Test satellite search endpoint"""
    response = client.get("/api/satellites/search?query=ISS&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "success" in data


def test_cache_stats():
    """Test cache stats endpoint"""
    response = client.get("/api/cache/stats")
    assert response.status_code == 200


def test_invalid_endpoint():
    """Test 404 handling"""
    response = client.get("/api/nonexistent")
    assert response.status_code == 404
