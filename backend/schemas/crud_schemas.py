from pydantic import BaseModel
from typing import Dict, Any, Optional


class ReadRequest(BaseModel):
    table_name: str
    columns: str = "*"
    filters: Optional[Dict[str, Any]] = None
    limit: Optional[int] = None
    order_by: Optional[str] = None
    ascending: bool = True


class CreateRequest(BaseModel):
    table_name: str
    data: Dict[str, Any]


class UpdateRequest(BaseModel):
    table_name: str
    data: Dict[str, Any]
    filters: Dict[str, Any]


class DeleteRequest(BaseModel):
    table_name: str
    filters: Dict[str, Any]


class CountRequest(BaseModel):
    table_name: str
    filters: Optional[Dict[str, Any]] = None
