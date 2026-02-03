"""
Integration tests for Team Domains.

These tests verify CRUD operations for custom domains on teams.
Note: Domain verification tests may be limited as they require DNS configuration.
"""

import pytest
import time

from codesphere import CodesphereSDK
from codesphere.resources.team.domain.resources import Domain


pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

# Test domain name - use a subdomain format that's clearly for testing
TEST_DOMAIN_PREFIX = "sdk-test"


@pytest.fixture
async def test_domain_name(test_team_id: int) -> str:
    """Generate a unique test domain name."""
    timestamp = int(time.time())
    return f"{TEST_DOMAIN_PREFIX}-{timestamp}.example.com"


class TestDomainsIntegration:
    """Integration tests for team domain endpoints."""

    async def test_list_domains(
        self,
        sdk_client: CodesphereSDK,
        test_team_id: int,
    ):
        """Should retrieve a list of domains for a team."""
        team = await sdk_client.teams.get(team_id=test_team_id)
        domains = await team.domains.list()

        assert isinstance(domains, list)
        assert all(isinstance(d, Domain) for d in domains)

    async def test_create_domain(
        self,
        sdk_client: CodesphereSDK,
        test_team_id: int,
        test_domain_name: str,
    ):
        """Should create a new custom domain."""
        team = await sdk_client.teams.get(team_id=test_team_id)

        # Create domain
        domain = await team.domains.create(name=test_domain_name)

        try:
            assert isinstance(domain, Domain)
            assert domain.name == test_domain_name
        finally:
            # Cleanup
            await domain.delete()

    async def test_get_domain(
        self,
        sdk_client: CodesphereSDK,
        test_team_id: int,
        test_domain_name: str,
    ):
        """Should retrieve a specific domain by name."""
        team = await sdk_client.teams.get(team_id=test_team_id)

        # Create domain first
        created_domain = await team.domains.create(name=test_domain_name)

        try:
            # Get the domain
            domain = await team.domains.get(name=test_domain_name)

            assert isinstance(domain, Domain)
            assert domain.name == test_domain_name
        finally:
            # Cleanup
            await created_domain.delete()

    async def test_domain_verify_status(
        self,
        sdk_client: CodesphereSDK,
        test_team_id: int,
        test_domain_name: str,
    ):
        """Should check domain verification status."""
        team = await sdk_client.teams.get(team_id=test_team_id)

        # Create domain first
        domain = await team.domains.create(name=test_domain_name)

        try:
            # Check verification status (will likely be unverified without DNS setup)
            status = await domain.verify_status()

            # Status should have verification info
            assert status is not None
        finally:
            # Cleanup
            await domain.delete()

    async def test_delete_domain(
        self,
        sdk_client: CodesphereSDK,
        test_team_id: int,
        test_domain_name: str,
    ):
        """Should delete a custom domain."""
        team = await sdk_client.teams.get(team_id=test_team_id)

        # Create domain
        domain = await team.domains.create(name=test_domain_name)

        # Delete it
        await domain.delete()

        # Verify it's gone by listing domains
        domains = await team.domains.list()
        domain_names = [d.name for d in domains]

        assert test_domain_name not in domain_names
