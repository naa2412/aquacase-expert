"""
schemas.py — Pydantic v2 Models untuk AquaCase Expert API
=========================================================
Mendefinisikan request/response schemas sesuai API.
"""

from pydantic import BaseModel, Field
from typing import Optional


class DiagnoseRequest(BaseModel):
    """Request body untuk POST /api/v1/diagnose"""
    kode_ikan: str = Field(..., description="Kode jenis ikan, misal 'J01'")
    gejala_input: dict[str, float] = Field(
        ...,
        description="Mapping kode_gejala ke nilai keyakinan (0.0-1.0)",
        json_schema_extra={"example": {"G01": 0.8, "G03": 0.6}}
    )


class HealthResponse(BaseModel):
    """Response untuk GET /"""
    status: str
    message: str
    version: str
