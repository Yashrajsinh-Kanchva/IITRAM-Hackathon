ALLOWED_USER_STATUSES = {"active", "inactive", "suspended"}
ALLOWED_USER_ROLES = {"farmer", "buyer"}
ALLOWED_PRODUCT_REVIEW_STATUSES = {"approved", "rejected", "hidden"}
ALLOWED_ORDER_STATUSES = {"pending", "confirmed", "packed", "shipped", "delivered", "cancelled"}
ALLOWED_PAYMENT_STATUSES = {"pending", "paid", "failed", "refunded"}
ALLOWED_REVIEW_STATES = {"pending_review", "reviewed", "flagged"}
ALLOWED_RANGES = {"7d": 7, "30d": 30, "90d": 90}
ALLOWED_OFFER_STATUSES = {
    "pending",
    "countered",
    "accepted",
    "rejected",
    "expired",
}
ACTIVE_OFFER_STATUSES = {"pending", "countered"}

OFFER_RESPONSE_TRANSITIONS = {
    "pending": {"accepted", "rejected", "countered"},
    "countered": {"accepted", "rejected", "countered"},
    "accepted": set(),
    "rejected": set(),
    "expired": set(),
}


ORDER_STATUS_TRANSITIONS = {
    "pending": {"confirmed", "cancelled"},
    "confirmed": {"packed", "cancelled"},
    "packed": {"shipped", "cancelled"},
    "shipped": {"delivered"},
    "delivered": set(),
    "cancelled": set(),
}


def is_valid_order_transition(current_status, next_status):
    if current_status == next_status:
        return True
    return next_status in ORDER_STATUS_TRANSITIONS.get(current_status, set())


def is_valid_offer_transition(current_status, next_status):
    return next_status in OFFER_RESPONSE_TRANSITIONS.get(current_status, set())
