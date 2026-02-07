import pytest
from dataclasses import dataclass
from typing import Optional, Type

from pydantic import BaseModel

from codesphere.core.operations import APIOperation


class SampleInputModel(BaseModel):
    """Sample input model for testing."""

    name: str
    value: int


class SampleResponseModel(BaseModel):
    """Sample response model for testing."""

    id: int
    status: str


@dataclass
class APIOperationTestCase:
    """Test case for APIOperation creation."""

    name: str
    method: str
    endpoint_template: str
    response_model: Type
    input_model: Optional[Type] = None


api_operation_test_cases = [
    APIOperationTestCase(
        name="GET operation without input model",
        method="GET",
        endpoint_template="/resources/{resource_id}",
        response_model=SampleResponseModel,
        input_model=None,
    ),
    APIOperationTestCase(
        name="POST operation with input model",
        method="POST",
        endpoint_template="/resources",
        response_model=SampleResponseModel,
        input_model=SampleInputModel,
    ),
    APIOperationTestCase(
        name="DELETE operation returning None",
        method="DELETE",
        endpoint_template="/resources/{id}",
        response_model=type(None),
        input_model=None,
    ),
    APIOperationTestCase(
        name="PATCH operation with input and response",
        method="PATCH",
        endpoint_template="/resources/{id}",
        response_model=SampleResponseModel,
        input_model=SampleInputModel,
    ),
]


class TestAPIOperation:
    @pytest.mark.parametrize(
        "case", api_operation_test_cases, ids=[c.name for c in api_operation_test_cases]
    )
    def test_create_operation(self, case: APIOperationTestCase):
        """Test APIOperation can be created with various configurations."""
        operation = APIOperation(
            method=case.method,
            endpoint_template=case.endpoint_template,
            response_model=case.response_model,
            input_model=case.input_model,
        )

        assert operation.method == case.method
        assert operation.endpoint_template == case.endpoint_template
        assert operation.response_model == case.response_model
        assert operation.input_model == case.input_model

    def test_operation_is_pydantic_model(self):
        """APIOperation should be a Pydantic BaseModel."""
        assert issubclass(APIOperation, BaseModel)

    def test_operation_model_copy(self):
        """APIOperation should support model_copy for creating variants."""
        original = APIOperation(
            method="GET",
            endpoint_template="/test",
            response_model=SampleResponseModel,
        )

        copied = original.model_copy(update={"method": "POST"})

        assert copied.method == "POST"
        assert copied.endpoint_template == original.endpoint_template
        assert copied.response_model == original.response_model
        assert original.method == "GET"

    def test_operation_with_path_parameters(self):
        """Test endpoint_template with multiple path parameters."""
        operation = APIOperation(
            method="GET",
            endpoint_template="/teams/{team_id}/domains/{domain_name}",
            response_model=SampleResponseModel,
        )

        assert "{team_id}" in operation.endpoint_template
        assert "{domain_name}" in operation.endpoint_template

    def test_default_input_model_is_none(self):
        """input_model should default to None."""
        operation = APIOperation(
            method="GET",
            endpoint_template="/test",
            response_model=SampleResponseModel,
        )

        assert operation.input_model is None
