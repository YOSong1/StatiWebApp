from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    src = root / "src"
    sys.path.insert(0, str(src))

    from fastapi.testclient import TestClient
    from webapp.app import create_app

    base = root
    sample_dir = base / "sampledata"

    candidates = [
        "orthogonal_sample.xlsx",
        "taguchi_sample.xlsx",
        "rsm_sample.xlsx",
        "ccd_sample.xlsx",
        "sample.xlsx",
    ]

    app = create_app()
    client = TestClient(app)

    pid = client.post("/api/v1/projects", json={"name": None}).json()["data"]["project_id"]

    picked = None
    for name in candidates:
        p = sample_dir / name
        if not p.exists():
            continue
        with p.open("rb") as f:
            r = client.post(
                f"/api/v1/projects/{pid}/data/upload",
                files={"file": (name, f, "application/octet-stream")},
            )
        if r.status_code == 200:
            picked = name
            break

    print("upload:", picked)
    if not picked:
        print("No sample uploaded")
        return 2

    summary = client.get(f"/api/v1/projects/{pid}/data/summary").json()["data"]
    cols = summary["columns"]
    dtypes = summary["dtypes"]

    numeric = []
    for c in cols:
        dt = str(dtypes.get(c, "")).lower()
        if "int" in dt or "float" in dt or "double" in dt:
            numeric.append(c)

    response = numeric[-1] if numeric else cols[-1]
    factors = [c for c in cols if c != response][:3]

    print("columns:", cols)
    print("response:", response)
    print("factors:", factors)

    rr = client.get(f"/api/v1/recommendations/projects/{pid}")
    print("recommendations:", rr.status_code)
    if rr.status_code != 200:
        print(json.dumps(rr.json(), ensure_ascii=False, indent=2))
    else:
        recs = rr.json()["data"].get("recommended", [])
        print("recommended.count:", len(recs))

    r = client.post(
        f"/api/v1/analysis/projects/{pid}/doe_anova",
        json={"response": response, "factors": factors},
    )
    print("doe_anova:", r.status_code)
    if r.status_code != 200:
        print(json.dumps(r.json(), ensure_ascii=False, indent=2))
    else:
        data = r.json()["data"]
        print("doe_anova.type:", data.get("type"))

    for chart_type, body in [
        ("주효과도", {"chart_type": "주효과도", "x_var": (factors[0] if factors else None), "y_var": response, "group_var": None, "options": None}),
        ("상호작용도", {"chart_type": "상호작용도", "x_var": (factors[0] if factors else None), "y_var": response, "group_var": (factors[1] if len(factors) > 1 else None), "options": None}),
        ("상관행렬", {"chart_type": "상관행렬", "x_var": None, "y_var": None, "group_var": None, "options": None}),
    ]:
        rc = client.post(f"/api/v1/charts/projects/{pid}", json=body)
        print("chart", chart_type, rc.status_code)
        if rc.status_code != 200:
            print(" ", json.dumps(rc.json(), ensure_ascii=False, indent=2))
        else:
            print(" ", "image_base64_png" in rc.json()["data"])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
