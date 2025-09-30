import os
import tempfile

# Configure an isolated writable test database BEFORE importing the app.
# Use a temp file so parallel runs / reruns don't collide.
_tmp_db_path = os.path.join(tempfile.gettempdir(), f"trustpilot_test_{os.getpid()}.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db_path}"
if os.path.exists(_tmp_db_path):
    os.remove(_tmp_db_path)

import csv
from io import StringIO
import pandas as pd
from fastapi.testclient import TestClient
from app.main import app
from app.ingest import run as ingest_csv
from app.schemas import HEADERS

client = TestClient(app)

def setup_module(module):
    # Create seed CSV (idempotent)
    df = pd.DataFrame([
        {
            "review_id": "r1",
            "user_id": "u1",
            "user_name": "Alice",
            "email": "alice@example.com",
            "business_id": "b1",
            "business_name": "CoffeeCo",
            "rating": 5,
            "title": "Great",
            "text": "Loved it",
            "ip_address": "1.1.1.3",
            "created_at": "2024-01-01T10:00:00Z",
        },
        {
            "review_id": "r2",
            "user_id": "u1",
            "user_name": "Alice",
            "email": "alice@example.com",
            "business_id": "b2",
            "business_name": "TeaCo",
            "rating": 3,
            "title": "Okay",
            "text": "It was fine",
            "ip_address": "1.1.1.2",
            "created_at": "2024-02-01T10:00:00Z",
        },
        {
            "review_id": "r3",
            "user_id": "u2",
            "user_name": "Bob",
            "email": "bob@example.com",
            "business_id": "b1",
            "business_name": "CoffeeCo",
            "rating": 1,
            "title": "Bad",
            "text": "Did not like it",
            "ip_address": "1.1.1.1",
            "created_at": "2024-03-01T10:00:00Z",
        },
    ])
    csv_path = "/tmp/data/trustpilot_challenge/data/test_reviews.csv"
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    df.to_csv(csv_path, index=False)
    ingest_csv(csv_path)

def parse_csv(text):
    sio = StringIO(text)
    reader = csv.DictReader(sio)
    return list(reader)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_reviews_business():
    r = client.get("/reviews/business/b1")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    assert "r1" in r.text
    assert "CoffeeCo" not in r.text  # not part of narrow output columns

def test_reviews_user_min_rating():
    r = client.get("/reviews/user/u1?min_rating=4")
    assert r.status_code == 200
    csv_text = r.text
    assert "r1" in csv_text and "r2" not in csv_text  # r1 rating 5 passes, r2 rating 3 filtered out

def test_reviews_user_rating_range():
    r = client.get("/reviews/user/u1?min_rating=3&max_rating=4")
    assert r.status_code == 200
    rows = parse_csv(r.text)
    ids = {row["review_id"] for row in rows}
    assert ids == {"r2"}  # only rating 3 inside range [3,4]

def test_reviews_user_date_filters_start():
    r = client.get("/reviews/user/u1?start_date=2024-02-01")
    rows = parse_csv(r.text)
    ids = {row["review_id"] for row in rows}
    assert ids == {"r2"}  # r1 is before start_date

def test_reviews_user_date_filters_end():
    r = client.get("/reviews/user/u1?end_date=2024-01-15")
    rows = parse_csv(r.text)
    ids = {row["review_id"] for row in rows}
    assert ids == {"r1"}  # r2 after end_date filtered

def test_reviews_business_combined_filters():
    # business b1 has r1 (rating 5) and r3 (rating 1)
    r = client.get("/reviews/business/b1?min_rating=2")
    rows = parse_csv(r.text)
    ids = {row["review_id"] for row in rows}
    assert ids == {"r1"}  # r3 filtered out

def test_reviews_business_pagination():
    # Order is DB dependent; rely on count + disjoint sets via offset
    r_page1 = client.get("/reviews/business/b1?limit=1&offset=0")
    r_page2 = client.get("/reviews/business/b1?limit=1&offset=1")
    rows1 = parse_csv(r_page1.text)
    rows2 = parse_csv(r_page2.text)
    assert len(rows1) == 1 and len(rows2) == 1
    assert rows1[0]["review_id"] != rows2[0]["review_id"]

def test_user_info_masks_email():
    r = client.get("/users/u1")
    assert r.status_code == 200
    assert "***@example.com" in r.text
    # Header validation
    header_line = r.text.splitlines()[0].split(",")
    assert header_line == HEADERS["users"]

def test_user_info_not_found():
    r = client.get("/users/does_not_exist")
    assert r.status_code == 404

def test_expanded_business_default_masks():
    r = client.get("/reviews/business/b1/expanded")
    assert r.status_code == 200
    text = r.text
    assert "***@example.com" in text or "***@example" in text  # masked
    assert "alice@example.com" not in text
    # Header contains joined fields
    header = text.splitlines()[0]
    assert "user_id" in header and "business_id" in header and "review_id" in header

def test_expanded_business_unmasked():
    r = client.get("/reviews/business/b1/expanded?mask_pii=false")
    assert r.status_code == 200
    text = r.text
    assert "alice@example.com" in text or "bob@example.com" in text

def test_expanded_user_mask_toggle():
    masked = client.get("/reviews/user/u1/expanded")
    raw = client.get("/reviews/user/u1/expanded?mask_pii=false")
    assert masked.status_code == 200 and raw.status_code == 200
    assert "alice@example.com" not in masked.text
    assert "alice@example.com" in raw.text

def test_content_disposition_filenames():
    r1 = client.get("/reviews/user/u1")
    r2 = client.get("/reviews/user/u1/expanded")
    r3 = client.get("/users/u1")
    cd1 = r1.headers.get("content-disposition", "").lower()
    cd2 = r2.headers.get("content-disposition", "").lower()
    cd3 = r3.headers.get("content-disposition", "").lower()
    assert "reviews_user_u1.csv" in cd1
    assert "reviews_user_u1_expanded.csv" in cd2
    assert "user_u1.csv" in cd3

def test_csv_headers_narrow_reviews():
    r = client.get("/reviews/user/u1")
    first_line = r.text.splitlines()[0]
    # HEADERS["reviews"] expected
    assert first_line == ",".join(HEADERS["reviews"])

def test_no_results_returns_header_only():
    # Valid range that produces zero rows (u1 has ratings 5 and 3 only)
    r = client.get("/reviews/user/u1?min_rating=4&max_rating=4")
    assert r.status_code == 200
    lines = r.text.splitlines()
    assert len(lines) == 1
    assert lines[0] == ",".join(HEADERS["reviews"])

def test_business_not_found():
    r = client.get("/reviews/business/does_not_exist")
    assert r.status_code in (200, 404)  # Adjust to your design
    # If 200-with-header-only pattern, then:
    if r.status_code == 200:
        assert len(r.text.splitlines()) == 1

def test_business_expanded_not_found():
    r = client.get("/reviews/business/does_not_exist/expanded")
    assert r.status_code in (200, 404)
    if r.status_code == 200:
        assert len(r.text.splitlines()) == 1

def test_invalid_rating_range():
    r = client.get("/reviews/user/u1?min_rating=5&max_rating=3")
    assert r.status_code in (400, 422)

def test_invalid_date_format():
    r = client.get("/reviews/user/u1?start_date=2024-13-40")
    assert r.status_code in (400, 422)

def test_start_date_after_end_date():
    r = client.get("/reviews/user/u1?start_date=2024-03-01&end_date=2024-01-01")
    assert r.status_code in (400, 422)

def test_negative_limit_offset():
    r1 = client.get("/reviews/user/u1?limit=-1")
    r2 = client.get("/reviews/user/u1?offset=-5")
    assert r1.status_code in (400, 422)
    assert r2.status_code in (400, 422)

def test_offset_past_end_returns_header_only():
    r = client.get("/reviews/business/b1?limit=10&offset=100")
    lines = r.text.splitlines()
    assert len(lines) == 1  # only header

def test_combined_filters_user():
    r = client.get("/reviews/user/u1?min_rating=3&max_rating=5&start_date=2024-01-15&end_date=2024-12-31")
    rows = parse_csv(r.text)
    ids = {row["review_id"] for row in rows}
    # r1 (rating 5, date Jan 1) excluded by start_date; r2 included
    assert ids == {"r2"}

def test_expanded_user_headers():
    r = client.get("/reviews/user/u1/expanded")
    header = r.text.splitlines()[0].split(",")
    # Ensure expanded includes something extra beyond narrow headers
    assert "email" in header and "review_id" in header

def test_expanded_business_headers():
    r = client.get("/reviews/business/b1/expanded")
    header = r.text.splitlines()[0].split(",")
    assert "email" in header and "review_id" in header and "user_id" in header

def test_default_masks_vs_explicit_true():
    default_r = client.get("/reviews/user/u1/expanded")
    explicit_r = client.get("/reviews/user/u1/expanded?mask_pii=true")
    assert "***" in default_r.text
    assert default_r.text == explicit_r.text

def test_unmasked_no_mask_patterns():
    r = client.get("/reviews/user/u1/expanded?mask_pii=false")
    assert "***" not in r.text
    assert "alice@example.com" in r.text

def test_business_zero_rows_after_filters():
    # b1 has ratings 5 and 1 only
    r = client.get("/reviews/business/b1?min_rating=4&max_rating=4")
    assert r.status_code == 200
    lines = r.text.splitlines()
    assert len(lines) == 1
    assert lines[0].split(",") == HEADERS["reviews"]

def test_idempotent_ingest():
    # Re-run ingest on same file; row count should not double if code enforces uniqueness
    csv_path = "/tmp/data/trustpilot_challenge/data/test_reviews.csv"
    before = client.get("/reviews/user/u1")
    count_before = len(parse_csv(before.text))
    ingest_csv(csv_path)
    after = client.get("/reviews/user/u1")
    count_after = len(parse_csv(after.text))
    # If you enforce unique review_id, counts should match
    assert count_after == count_before

def test_csv_escaping_with_commas_quotes(tmp_path):
    extra_csv = tmp_path / "extra.csv"
    # Append a row with commas and quotes
    import pandas as pd
    df_extra = pd.DataFrame([{
        "review_id": "r_escape",
        "user_id": "u1",
        "user_name": "Alice",
        "email": "alice@example.com",
        "business_id": "b1",
        "business_name": "CoffeeCo",
        "rating": 4,
        "title": 'Great, "really"',
        "text": 'Line1,\n"Quoted", test',
        "ip_address": "1.1.1.9",
        "created_at": "2024-04-01T10:00:00Z",
    }])
    df_existing = pd.read_csv("/tmp/data/trustpilot_challenge/data/test_reviews.csv")
    combined = pd.concat([df_existing, df_extra], ignore_index=True)
    combined.to_csv(extra_csv, index=False)
    ingest_csv(str(extra_csv))
    r = client.get("/reviews/business/b1/expanded?mask_pii=false")
    assert 'r_escape' in r.text

def test_content_type_all_endpoints():
    endpoints = [
        "/reviews/business/b1",
        "/reviews/business/b1/expanded",
        "/reviews/user/u1",
        "/reviews/user/u1/expanded",
        "/users/u1",
    ]
    for ep in endpoints:
        resp = client.get(ep)
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/csv")

def test_reviews_expanded_masked():
    resp = client.get("/reviews/business/b1/expanded?mask_pii=true")
    assert resp.status_code == 200
    csv_text = resp.text
    assert "***@" in csv_text  # masked email
    assert "***" in csv_text   # masked name
    assert "***.***" in csv_text  # masked IP