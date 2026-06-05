import urllib.request
import json

payload = json.dumps({
    "kode_ikan": "J01",
    "gejala_input": {"G01": 0.8, "G03": 0.6}
}).encode('utf-8')

req = urllib.request.Request(
    'http://127.0.0.1:8000/api/v1/diagnose',
    data=payload,
    headers={'Content-Type': 'application/json'}
)

resp = urllib.request.urlopen(req)
data = json.loads(resp.read())

reko = data.get('explanation', {}).get('rekomendasi', '')
print("=== REKOMENDASI ===")
if "Pengobatan:" in reko:
    print("BERHASIL! Solusi muncul dari KB:")
    print(reko[:300])
else:
    print(f"GAGAL: '{reko}'")
