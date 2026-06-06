"""
main.py — FastAPI Backend 
================================================
Menyediakan REST API yang menghubungkan engine diagnosis
(RBR + CBR + Hybrid Fusion) dengan frontend React.

ENDPOINTS:
    GET  /                    — health check
    GET  /api/v1/ikan         — daftar jenis ikan
    GET  /api/v1/gejala       — daftar gejala (opsional filter kode_ikan)
    POST /api/v1/diagnose     — jalankan diagnosis hybrid
    GET  /api/v1/kasus        — data case base CBR
    GET  /api/v1/aturan       — data rule base RBR
    GET  /api/v1/penyakit     — data penyakit
"""

import json
import os
import sys
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

# Tambahkan path ke engine, backend, dan data
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
ENGINE_DIR = os.path.join(PROJECT_DIR, "engine")
DATA_DIR = os.path.join(PROJECT_DIR, "data")

sys.path.insert(0, ENGINE_DIR)
sys.path.insert(0, BASE_DIR)

from schemas import DiagnoseRequest, HealthResponse
from rbr import RuleBasedReasoning
from cbr import CaseBasedReasoning
from hybrid_fusion import HybridFusionEngine

# ===========================================================
# INISIALISASI APP + ENGINE
# ===========================================================

app = FastAPI(
    title="AquaCase Expert API",
    description="Sistem Pakar Diagnosis Penyakit Ikan Air Tawar — Hybrid CBR + RBR",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load engines saat startup
rbr_engine = RuleBasedReasoning()
rbr_engine.load_knowledge_base(DATA_DIR)

cbr_engine = CaseBasedReasoning(
    path_case_base=os.path.join(DATA_DIR, "case_base.json"),
    path_penyakit=os.path.join(DATA_DIR, "penyakit.json"),
    path_gejala=os.path.join(DATA_DIR, "gejala.json"),
    path_solusi=os.path.join(DATA_DIR, "solusi.json"),
    threshold=0.0
)

hybrid_engine = HybridFusionEngine(
    rbr_engine=rbr_engine,
    cbr_engine=cbr_engine,
    w_rbr=0.45,
    w_cbr=0.35,
    w_agreement=0.20,
    threshold=0.6
)


# ===========================================================
# HELPER — Load JSON
# ===========================================================

def load_json(filename: str) -> list | dict:
    """Load file JSON dari folder data."""
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# Pre-load data statis
_ikan_data = load_json("ikan.json")
_gejala_data = load_json("gejala.json")
_penyakit_data = load_json("penyakit.json")
_gejala_penyakit_data = load_json("gejala_penyakit.json")
_solusi_data = load_json("solusi.json")
_rules_data = load_json("rules.json")
_case_base_data = load_json("case_base.json")


# ===========================================================
# ENDPOINTS
# ===========================================================

@app.get("/", response_model=HealthResponse)
def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        message="AquaCase Expert API berjalan dengan baik",
        version="1.0.0"
    )


@app.get("/api/v1/ikan")
def get_ikan():
    """
    Mengembalikan daftar jenis ikan yang didukung sistem.
    Data dari ikan.json.
    """
    return _ikan_data


@app.get("/api/v1/gejala")
def get_gejala(kode_ikan: Optional[str] = Query(None, description="Filter gejala berdasarkan kode ikan")):
    """
    Mengembalikan daftar gejala.
    Jika kode_ikan diberikan, filter relevan (saat ini return semua
    karena gejala tidak di-mapping per ikan, melainkan per penyakit).
    """
    # Return semua gejala — di frontend, filtering per ikan tidak diperlukan
    # karena gejala terkait penyakit, bukan jenis ikan
    return _gejala_data


@app.get("/api/v1/penyakit")
def get_penyakit():
    """Mengembalikan daftar penyakit beserta detailnya."""
    # Gabungkan data penyakit dengan solusi
    result = []
    solusi_map = {s["kode_penyakit"]: s for s in _solusi_data}

    for p in _penyakit_data:
        kode = p["kode_penyakit"]
        solusi = solusi_map.get(kode, {})
        # Ambil gejala terkait
        gejala_terkait = [
            gp for gp in _gejala_penyakit_data
            if gp["kode_penyakit"] == kode
        ]
        result.append({
            **p,
            "pengobatan": solusi.get("pengobatan", ""),
            "pengendalian": solusi.get("pengendalian", ""),
            "gejala_terkait": gejala_terkait
        })

    return result


@app.post("/api/v1/diagnose")
def diagnose(req: DiagnoseRequest):
    """
    Menjalankan diagnosis hybrid (RBR + CBR + Fusion).

    Request body:
        {
            "kode_ikan": "J01",
            "gejala_input": {"G01": 0.8, "G03": 0.6}
        }

    Response normal: is_conflict=false → diagnosis_akhir + explanation
    Response konflik: is_conflict=true → diagnosis_akhir=null, kandidat_konflik=[...]
    """
    # Validasi: minimal 1 gejala
    if not req.gejala_input:
        raise HTTPException(
            status_code=422,
            detail="Pilih minimal satu gejala untuk memulai diagnosis"
        )

    # Validasi: kode_ikan ada di database
    valid_ikan = {i["kode_ikan"] for i in _ikan_data}
    if req.kode_ikan not in valid_ikan:
        raise HTTPException(
            status_code=404,
            detail=f"Kode ikan '{req.kode_ikan}' tidak ditemukan"
        )

    # Validasi: semua kode gejala valid
    valid_gejala = {g["kode_gejala"] for g in _gejala_data}
    invalid_gejala = [g for g in req.gejala_input.keys() if g not in valid_gejala]
    if invalid_gejala:
        raise HTTPException(
            status_code=422,
            detail=f"Kode gejala tidak valid: {', '.join(invalid_gejala)}"
        )

    # Validasi: nilai CF dalam range [0.0, 1.0]
    for kode, cf in req.gejala_input.items():
        if not (0.0 <= cf <= 1.0):
            raise HTTPException(
                status_code=422,
                detail=f"Nilai keyakinan untuk {kode} harus antara 0.0 dan 1.0"
            )

    # Jalankan hybrid diagnosis
    try:
        result = hybrid_engine.diagnose(
            kode_ikan=req.kode_ikan,
            gejala_input=req.gejala_input
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Terjadi kesalahan saat memproses diagnosis: {str(e)}"
        )


@app.get("/api/v1/kasus")
def get_kasus():
    """
    Mengembalikan data case base CBR.
    Masing-masing kasus berisi info ikan, penyakit, gejala, dan bobot.
    """
    # Enrichment: tambah nama penyakit
    penyakit_map = {p["kode_penyakit"]: p["nama_penyakit"] for p in _penyakit_data}
    gejala_map = {g["kode_gejala"]: g["nama_gejala"] for g in _gejala_data}

    result = []
    for case in _case_base_data:
        enriched_gejala = []
        for g in case.get("gejala", []):
            enriched_gejala.append({
                **g,
                "nama_gejala": gejala_map.get(g["kode_gejala"], g["kode_gejala"])
            })

        result.append({
            **case,
            "nama_penyakit": penyakit_map.get(
                case["kode_penyakit"], case["kode_penyakit"]
            ),
            "gejala": enriched_gejala
        })

    return result


@app.get("/api/v1/aturan")
def get_aturan():
    """
    Mengembalikan data rule base RBR.
    Setiap rule berisi premis, konklusi, CF pakar, dan teks rule.
    """
    return _rules_data


# ===========================================================
# MAIN — Jalankan dengan: uvicorn main:app --reload
# ===========================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
