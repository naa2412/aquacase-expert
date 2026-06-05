import json
from pathlib import Path

KB_PATH = Path(__file__).with_name("knowledge_base.json")
with KB_PATH.open(encoding="utf-8") as f:
    kb = json.load(f)

print("Jumlah ikan:", len(kb["ikan"]))
print("Jumlah penyakit:", len(kb["penyakit"]))
print("Jumlah gejala:", len(kb["gejala"]))
print("Jumlah solusi:", len(kb["solusi"]))
print("Jumlah case base:", len(kb["case_base"]))
print("Jumlah rules:", len(kb["rules"]))
print("Jumlah data uji:", len(kb["data_uji"]))

# Contoh akses rule dan case
print("Contoh rule pertama:", kb["rules"][0])
print("Contoh case pertama:", kb["case_base"][0])
