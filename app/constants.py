# --- Source dataset column names (raw CSV headers) ---
COL_REVIEW_ID = "Review Id"
COL_REVIEWER_NAME = "Reviewer Name"
COL_REVIEW_TITLE = "Review Title"
COL_REVIEW_RATING = "Review Rating"
COL_REVIEW_CONTENT = "Review Content"
COL_REVIEW_IP = "Review IP Address"
COL_BUSINESS_ID = "Business Id"
COL_BUSINESS_NAME = "Business Name"
COL_REVIEWER_ID = "Reviewer Id"
COL_EMAIL = "Email Address"
COL_COUNTRY = "Reviewer Country"
COL_REVIEW_DATE = "Review Date"

# --- Normalized field names (internal schema) ---
F_REVIEW_ID = "review_id"
F_USER_ID = "user_id"
F_BUSINESS_ID = "business_id"
F_RATING = "rating"
F_TITLE = "title"
F_TEXT = "text"
F_IP = "ip_address"
F_CREATED_AT = "created_at"
F_USER_NAME = "user_name"
F_EMAIL = "email"
F_COUNTRY = "country"
F_BUSINESS_NAME = "business_name"
F_FILE_HASH = "file_hash"
F_SOURCE_PATH = "source_path"
F_TOTAL_ROWS = "total_rows"
F_LOADED_ROWS = "loaded_rows"

# Ordered collections (optional convenience)
SOURCE_COLUMNS = [
    COL_REVIEW_ID,
    COL_REVIEWER_ID,
    COL_REVIEWER_NAME,
    COL_EMAIL,
    COL_COUNTRY,
    COL_BUSINESS_ID,
    COL_BUSINESS_NAME,
    COL_REVIEW_RATING,
    COL_REVIEW_TITLE,
    COL_REVIEW_CONTENT,
    COL_REVIEW_IP,
    COL_REVIEW_DATE,
]

NORMALIZED_FIELDS = [
    F_REVIEW_ID,
    F_USER_ID,
    F_USER_NAME,
    F_EMAIL,
    F_COUNTRY,
    F_BUSINESS_ID,
    F_BUSINESS_NAME,
    F_RATING,
    F_TITLE,
    F_TEXT,
    F_IP,
    F_CREATED_AT,
]

# Mapping raw CSV header -> normalized internal field
RENAME_MAP = {
    COL_REVIEW_ID: F_REVIEW_ID,
    COL_REVIEWER_ID: F_USER_ID,
    COL_REVIEWER_NAME: F_USER_NAME,
    COL_EMAIL: F_EMAIL,
    COL_COUNTRY: F_COUNTRY,
    COL_BUSINESS_ID: F_BUSINESS_ID,
    COL_BUSINESS_NAME: F_BUSINESS_NAME,
    COL_REVIEW_RATING: F_RATING,
    COL_REVIEW_TITLE: F_TITLE,
    COL_REVIEW_CONTENT: F_TEXT,
    COL_REVIEW_IP: F_IP,
    COL_REVIEW_DATE: F_CREATED_AT,
}

# --- Table names ---
TBL_USERS = "users"
TBL_BUSINESSES = "businesses"
TBL_REVIEWS = "reviews"
TBL_INGEST_METADATA = "ingest_metadata"

__all__ = [
    "COL_REVIEW_ID",
    "COL_REVIEWER_NAME",
    "COL_REVIEW_TITLE",
    "COL_REVIEW_RATING",
    "COL_REVIEW_CONTENT",
    "COL_REVIEW_IP",
    "COL_BUSINESS_ID",
    "COL_BUSINESS_NAME",
    "COL_REVIEWER_ID",
    "COL_EMAIL",
    "COL_COUNTRY",
    "COL_REVIEW_DATE",
    "F_REVIEW_ID",
    "F_USER_ID",
    "F_BUSINESS_ID",
    "F_RATING",
    "F_TITLE",
    "F_TEXT",
    "F_IP",
    "F_CREATED_AT",
    "F_USER_NAME",
    "F_EMAIL",
    "F_COUNTRY",
    "F_BUSINESS_NAME",
    "SOURCE_COLUMNS",
    "NORMALIZED_FIELDS",
    "RENAME_MAP",
    "TBL_USERS",
    "TBL_BUSINESSES",
    "TBL_REVIEWS",
    "TBL_INGEST_METADATA",
    "F_SOURCE_PATH",
    "F_TOTAL_ROWS",
    "F_LOADED_ROWS",
    "F_FILE_HASH",
]