import pytest
import time

from codesphere import CodesphereSDK
from codesphere.resources.team.domain.resources import Domain


pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

TEST_DOMAIN_PREFIX = "sdk-test"


@pytest.fixture
async def test_domain_name(test_team_id: int) -> str:
    """Generate a unique test domain name."""
    unique_suffix = int(time.time())
    return f"{TEST_DOMAIN_PREFIX}-{unique_suffix}.example.com"


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

        domain = await team.domains.create(name=test_domain_name)

        try:
            assert isinstance(domain, Domain)
            assert domain.name == test_domain_name
        finally:
            await domain.delete()

    async def test_get_domain(
        self,
        sdk_client: CodesphereSDK,
        test_team_id: int,
        test_domain_name: str,
    ):
        """Should retrieve a specific domain by name."""
        team = await sdk_client.teams.get(team_id=test_team_id)

        created_domain = await team.domains.create(name=test_domain_name)

        try:
            domain = await team.domains.get(name=test_domain_name)

            assert isinstance(domain, Domain)
            assert domain.name == test_domain_name
        finally:
            await created_domain.delete()

    async def test_domain_verify_status(
        self,
        sdk_client: CodesphereSDK,
        test_team_id: int,
        test_domain_name: str,
    ):
        """Should check domain verification status."""
        team = await sdk_client.teams.get(team_id=test_team_id)

        domain = await team.domains.create(name=test_domain_name)

        try:
            status = await domain.verify_status()

            assert status is not None
        finally:
            await domain.delete()

    async def test_delete_domain(
        self,
        sdk_client: CodesphereSDK,
        test_team_id: int,
        test_domain_name: str,
    ):
        """Should delete a custom domain."""
        team = await sdk_client.teams.get(team_id=test_team_id)

        domain = await team.domains.create(name=test_domain_name)

        await domain.delete()

        domains = await team.domains.list()
        domain_names = [d.name for d in domains]

        assert test_domain_name not in domain_names
