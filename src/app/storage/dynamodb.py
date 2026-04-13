from __future__ import annotations

from decimal import Decimal

import boto3

from app.models import CategorizationRecord


class DynamoStorage:
    def __init__(
        self,
        categorization_table_name: str,
        wip_table_name: str,
        *,
        region_name: str,
    ) -> None:
        dynamodb = boto3.resource("dynamodb", region_name=region_name)
        self._categorization_table = dynamodb.Table(categorization_table_name)
        self._wip_table = dynamodb.Table(wip_table_name)

    def put_categorization(self, record: CategorizationRecord) -> None:
        self._categorization_table.put_item(
            Item=_to_dynamodb_value(record.model_dump())
        )

    def delete_wip(self, url_hash: str) -> None:
        self._wip_table.delete_item(Key={"url_hash": url_hash})


def _to_dynamodb_value(value):
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, list):
        return [_to_dynamodb_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_dynamodb_value(item) for key, item in value.items()}
    return value
