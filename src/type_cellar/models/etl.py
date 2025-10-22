"""Common types used when writing data pipelines"""

from __future__ import annotations

import attr


@attr.define
class BigQueryTableInfo:
    """Type for a table in BigQuery"""

    project_id: str
    dataset_id: str
    table_id: str

    @property
    def full_table_id(self) -> str:
        return f"{self.project_id}.{self.dataset_id}.{self.table_id}"
