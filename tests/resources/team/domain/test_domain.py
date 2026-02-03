"""
Tests for Domain resources: TeamDomainManager and Domain model.
"""

import pytest
from dataclasses import dataclass
from typing import Any, Optional

from codesphere.resources.team.domain.resources import Domain
from codesphere.resources.team.domain.manager import TeamDomainManager
from codesphere.resources.team.domain.schemas import (
    CustomDomainConfig,
    DomainRouting,
    DomainVerificationStatus,
)


# -----------------------------------------------------------------------------
# Test Cases
# -----------------------------------------------------------------------------


@dataclass
class DomainOperationTestCase:
    """Test case for domain operations."""

    name: str
    operation: str
    input_data: Optional[Any] = None
    mock_response: Optional[Any] = None


# -----------------------------------------------------------------------------
# TeamDomainManager Tests
# -----------------------------------------------------------------------------


class TestTeamDomainManager:
    """Tests for the TeamDomainManager class."""

    @pytest.fixture
    def domain_manager(self, mock_http_client_for_resource, sample_domain_data):
        """Create a TeamDomainManager with mock HTTP client."""
        mock_client = mock_http_client_for_resource([sample_domain_data])
        manager = TeamDomainManager(http_client=mock_client, team_id=12345)
        return manager, mock_client

    @pytest.mark.asyncio
    async def test_list_domains(self, domain_manager, sample_domain_data):
        """List domains should return a list of Domain models."""
        manager, mock_client = domain_manager

        result = await manager.list()

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], Domain)

    @pytest.mark.asyncio
    async def test_get_domain(self, mock_http_client_for_resource, sample_domain_data):
        """Get domain should return a single Domain model."""
        mock_client = mock_http_client_for_resource(sample_domain_data)
        manager = TeamDomainManager(http_client=mock_client, team_id=12345)

        result = await manager.get(name="test.example.com")

        assert isinstance(result, Domain)
        assert result.name == sample_domain_data["name"]

    @pytest.mark.asyncio
    async def test_create_domain(
        self, mock_http_client_for_resource, sample_domain_data
    ):
        """Create domain should return the created Domain model."""
        mock_client = mock_http_client_for_resource(sample_domain_data)
        manager = TeamDomainManager(http_client=mock_client, team_id=12345)

        result = await manager.create(name="new.example.com")

        assert isinstance(result, Domain)
        mock_client.request.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_domain(
        self, mock_http_client_for_resource, sample_domain_data
    ):
        """Update domain should apply config changes."""
        mock_client = mock_http_client_for_resource(sample_domain_data)
        manager = TeamDomainManager(http_client=mock_client, team_id=12345)

        config = CustomDomainConfig(max_body_size_mb=50)
        result = await manager.update(name="test.example.com", config=config)

        assert isinstance(result, Domain)

    @pytest.mark.asyncio
    async def test_update_workspace_connections(
        self, mock_http_client_for_resource, sample_domain_data
    ):
        """Update workspace connections should accept routing configuration."""
        mock_client = mock_http_client_for_resource(sample_domain_data)
        manager = TeamDomainManager(http_client=mock_client, team_id=12345)

        routing = DomainRouting().add("/", [72678]).add("/api", [72679])
        result = await manager.update_workspace_connections(
            name="test.example.com", connections=routing
        )

        assert isinstance(result, Domain)


# -----------------------------------------------------------------------------
# Domain Model Tests
# -----------------------------------------------------------------------------


class TestDomainModel:
    """Tests for the Domain model and its methods."""

    @pytest.mark.asyncio
    async def test_update_domain(self, domain_model_factory, sample_domain_data):
        """Domain.update() should apply configuration changes."""
        domain, mock_client = domain_model_factory(response_data=sample_domain_data)

        config = CustomDomainConfig(max_body_size_mb=100)
        result = await domain.update(data=config)

        mock_client.request.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_domain(self, domain_model_factory):
        """Domain.delete() should call delete operation."""
        domain, mock_client = domain_model_factory()

        await domain.delete()

        mock_client.request.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_verify_status(self, domain_model_factory):
        """Domain.verify_status() should return verification status."""
        verification_response = {"verified": True, "reason": None}
        domain, mock_client = domain_model_factory(response_data=verification_response)

        result = await domain.verify_status()

        assert isinstance(result, DomainVerificationStatus)


# -----------------------------------------------------------------------------
# DomainRouting Tests
# -----------------------------------------------------------------------------


class TestDomainRouting:
    """Tests for the DomainRouting helper class."""

    def test_create_empty_routing(self):
        """DomainRouting should start with empty routing."""
        routing = DomainRouting()
        assert routing.root == {}

    def test_add_single_route(self):
        """DomainRouting.add() should add a route."""
        routing = DomainRouting().add("/", [72678])

        assert "/" in routing.root
        assert routing.root["/"] == [72678]

    def test_add_multiple_routes(self):
        """DomainRouting should support chained .add() calls."""
        routing = (
            DomainRouting()
            .add("/", [72678])
            .add("/api", [72679])
            .add("/admin", [72680, 72681])
        )

        assert len(routing.root) == 3
        assert routing.root["/"] == [72678]
        assert routing.root["/api"] == [72679]
        assert routing.root["/admin"] == [72680, 72681]

    def test_routing_returns_self_for_chaining(self):
        """DomainRouting.add() should return self for method chaining."""
        routing = DomainRouting()
        result = routing.add("/test", [1])

        assert result is routing


# -----------------------------------------------------------------------------
# CustomDomainConfig Tests
# -----------------------------------------------------------------------------


class TestCustomDomainConfig:
    """Tests for the CustomDomainConfig schema."""

    def test_create_with_all_fields(self):
        """CustomDomainConfig should accept all optional fields."""
        config = CustomDomainConfig(
            restricted=True,
            max_body_size_mb=100,
            max_connection_timeout_s=300,
            use_regex=False,
        )

        assert config.restricted is True
        assert config.max_body_size_mb == 100
        assert config.max_connection_timeout_s == 300
        assert config.use_regex is False

    def test_create_with_partial_fields(self):
        """CustomDomainConfig should allow partial field specification."""
        config = CustomDomainConfig(max_body_size_mb=50)

        assert config.max_body_size_mb == 50
        assert config.restricted is None
        assert config.max_connection_timeout_s is None

    def test_dump_excludes_none_values(self):
        """CustomDomainConfig dump should exclude None values when requested."""
        config = CustomDomainConfig(max_body_size_mb=50)
        dumped = config.model_dump(exclude_none=True, by_alias=True)

        assert "maxBodySizeMb" in dumped
        assert "restricted" not in dumped
