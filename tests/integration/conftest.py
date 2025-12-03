"""Integration test configuration."""


def pytest_configure(config):
    """Register integration marker."""
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
