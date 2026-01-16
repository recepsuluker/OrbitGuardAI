"""
Unit tests for orbit_agent_async.py
Run with: pytest tests/test_async.py
"""

import pytest
import asyncio
from orbit_agent_async import AsyncOrbitAgent


# Mock credentials for testing
TEST_USERNAME = "test_user"
TEST_PASSWORD = "test_pass"


@pytest.mark.asyncio
async def test_agent_initialization():
    """Test async agent initialization."""
    async with AsyncOrbitAgent(TEST_USERNAME, TEST_PASSWORD) as agent:
        assert agent is not None
        assert agent.session is not None


@pytest.mark.asyncio
async def test_context_manager():
    """Test async context manager."""
    agent = AsyncOrbitAgent(TEST_USERNAME, TEST_PASSWORD)
    
    # Enter context
    await agent.__aenter__()
    assert agent.session is not None
    
    # Exit context
    await agent.__aexit__()
    # Session should be closed (can't easily test this)


def test_sync_wrapper():
    """Test synchronous wrapper function."""
    from orbit_agent_async import run_sync
    
    # This would need real credentials to work
    # Just test that the function exists and can be called
    assert callable(run_sync)


@pytest.mark.asyncio
async def test_concurrent_fetch_structure():
    """Test the structure of concurrent fetch (without real API calls)."""
    # Create agent without actually connecting
    agent = AsyncOrbitAgent(TEST_USERNAME, TEST_PASSWORD, timeout=1)
    
    # Test that methods exist
    assert hasattr(agent, 'fetch_single_tle')
    assert hasattr(agent, 'fetch_batch_tle')
    assert hasattr(agent, 'fetch_batch_with_semaphore')


def test_agent_attributes():
    """Test agent has correct attributes."""
    agent = AsyncOrbitAgent(TEST_USERNAME, TEST_PASSWORD)
    
    assert agent.username == TEST_USERNAME
    assert agent.password == TEST_PASSWORD
    assert agent.base_url == "https://www.space-track.org"
    assert agent.session is None  # Before context entry


# Note: Integration tests with real API would go here
# They would be marked with @pytest.mark.integration
# and only run when explicitly requested
