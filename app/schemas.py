HEADERS = {
    "reviews": ["review_id", "user_id", "business_id", "rating", "title", "text", "ip_address", "created_at"],
    "users": ["user_id", "user_name", "email", "country"],
    "reviews_expanded": [
        "review_id", "rating", "title", "text", "ip_address", "created_at",
        "user_id", "user_name", "email", "country",
        "business_id", "business_name",
    ],
}
