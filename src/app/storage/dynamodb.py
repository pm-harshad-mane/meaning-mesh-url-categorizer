from __future__ import annotations

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
        self._categorization_table.put_item(Item=record.model_dump())

    def delete_wip(self, url_hash: str) -> None:
        self._wip_table.delete_item(Key={"url_hash": url_hash})
