from typing import List, Protocol

from .models import Domain

from ...core import APIOperation, ResourceBase


class ListDomainsCallable(Protocol):
    async def __call__(self, *, team_id: int) -> List[Domain]: ...


class GetDomainCallable(Protocol):
    async def __call__(self, *, team_id: int, domain_name: str) -> Domain: ...


class CreateDomainCallable(Protocol):
    async def __call__(self, *, team_id: int, domain_name: str) -> Domain: ...


class DomainsResource(ResourceBase):
    list: ListDomainsCallable
    list = APIOperation(
        method="GET",
        endpoint_template="/domains/team/{team_id}",
        response_model=List[Domain],
    )

    get: GetDomainCallable
    get = APIOperation(
        method="GET",
        endpoint_template="/domains/team/{team_id}/domain/{domain_name}",
        response_model=Domain,
    )

    create: CreateDomainCallable
    create = APIOperation(
        method="POST",
        endpoint_template="/domains/team/{team_id}/domain/{domain_name}",
        response_model=Domain,
    )
