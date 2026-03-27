from datetime import datetime, timedelta, timezone

from app.services.exceptions import ServiceError
from app.utils.time_utils import utcnow
from app.utils.validators import ALLOWED_RANGES


def compute_quality_score(product: dict) -> int:
    product = product or {}
    score = 0

    has_image = bool(
        product.get("image")
        or product.get("image_url")
        or product.get("product_image")
    )
    if has_image:
        score += 20

    description = str(product.get("description") or "")
    if len(description.strip()) > 100:
        score += 20

    try:
        price = float(product.get("price") or 0)
    except (TypeError, ValueError):
        price = 0
    if price > 0:
        score += 15

    if str(product.get("category") or "").strip():
        score += 15

    if bool(
        product.get("farmer_verified_badge")
        or product.get("seller_verified")
        or product.get("is_farmer_verified")
    ):
        score += 20

    created_at = product.get("created_at")
    if created_at:
        now = utcnow().astimezone(timezone.utc)
        if getattr(created_at, "tzinfo", None) is None:
            created_utc = created_at.replace(tzinfo=timezone.utc)
        else:
            created_utc = created_at.astimezone(timezone.utc)
        age = now - created_utc
        if age <= timedelta(days=30):
            score += 10

    return max(0, min(int(score), 100))


class AnalyticsService:
    def __init__(self, order_repo, transaction_repo, user_repo, product_repo, alert_repo=None):
        self.order_repo = order_repo
        self.transaction_repo = transaction_repo
        self.user_repo = user_repo
        self.product_repo = product_repo
        self.alert_repo = alert_repo

    def _window(self, range_key):
        if range_key not in ALLOWED_RANGES:
            raise ServiceError("range must be one of 7d, 30d, 90d", status_code=400)
        now = utcnow()
        days = ALLOWED_RANGES[range_key]
        start = now - timedelta(days=days - 1)
        return start, now, days

    def _series(self, start, days, value_map, cast=float):
        points = []
        for index in range(days):
            day = (start + timedelta(days=index)).date().isoformat()
            value = value_map.get(day, 0)
            points.append({"date": day, "value": cast(value)})
        return points

    def sales_trend(self, range_key):
        start, end, days = self._window(range_key)
        values = self.transaction_repo.daily_sales(start, end)
        return {
            "range": range_key,
            "series": self._series(start, days, values, cast=float),
        }

    def orders_trend(self, range_key):
        start, end, days = self._window(range_key)
        values = self.order_repo.daily_order_counts(start, end)
        return {
            "range": range_key,
            "series": self._series(start, days, values, cast=int),
        }

    def overview(self, range_key="30d"):
        start, end, days = self._window(range_key)
        categories = self.product_repo.category_activity_since(start)
        users = self.user_repo.user_growth_series(start, end)
        return {
            "range": range_key,
            "category_activity": [
                {"category": key, "count": value}
                for key, value in sorted(categories.items(), key=lambda kv: kv[1], reverse=True)
            ],
            "user_growth": self._series(start, days, users, cast=int),
        }

    def get_3d_data(self, range_key="30d", limit=100):
        """
        Return a clean dataset for 3D analytics:
        [{time, price, quantity}, ...]
        """
        start, end, _ = self._window(range_key)
        raw_rows = self.order_repo.fetch_recent_for_3d(start, end, limit=min(max(limit, 1), 100))

        cleaned = []
        for row in raw_rows:
            created_at = row.get("created_at")
            if not isinstance(created_at, datetime):
                continue
            if created_at.tzinfo is not None:
                created_at = created_at.astimezone(timezone.utc).replace(tzinfo=None)

            price_raw = (
                row.get("total_price")
                if row.get("total_price") is not None
                else row.get("total_amount")
            )
            if price_raw is None:
                price_raw = row.get("price")
            quantity_raw = (
                row.get("quantity")
                if row.get("quantity") is not None
                else row.get("total_quantity")
            )

            try:
                price = float(price_raw)
                quantity = float(quantity_raw)
            except (TypeError, ValueError):
                continue

            if price <= 0 or quantity <= 0:
                continue

            cleaned.append(
                {
                    "time": created_at.isoformat() + "Z",
                    "price": price,
                    "quantity": quantity,
                }
            )

        return cleaned[:100]

    def _trigger(self, alert_type, severity, message, active):
        if not active or self.alert_repo is None:
            return None
        return self.alert_repo.upsert_unresolved(alert_type, severity, message)

    def _order_spike_alert(self, now):
        today = now.date().isoformat()
        previous_start = (now - timedelta(days=7)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        values = self.order_repo.daily_order_counts(previous_start, now)
        today_count = int(values.get(today, 0))

        previous_sum = 0
        for days_ago in range(1, 8):
            key = (now - timedelta(days=days_ago)).date().isoformat()
            previous_sum += int(values.get(key, 0))
        average = previous_sum / 7.0

        is_spike = today_count > 2 * average if average > 0 else today_count >= 10
        message = (
            f"Order spike detected: {today_count} orders today vs "
            f"7-day avg {average:.1f}."
        )
        return self._trigger("order_spike", "warning", message, is_spike)

    def _payment_failure_alert(self, now):
        window_start = now - timedelta(hours=24)
        total = self.transaction_repo.collection.count_documents(
            {"created_at": {"$gte": window_start}}
        )
        failed = self.transaction_repo.collection.count_documents(
            {"created_at": {"$gte": window_start}, "payment_status": "failed"}
        )
        failure_rate = (failed / total) if total else 0.0
        is_high = total > 0 and failure_rate > 0.15
        message = (
            f"Payment failure rate is {failure_rate * 100:.1f}% in last 24h "
            f"({failed}/{total} failed transactions)."
        )
        return self._trigger("payment_failure_rate", "critical", message, is_high)

    def _user_registration_drop_alert(self, now):
        yesterday_start = (now - timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        yesterday_end = yesterday_start + timedelta(days=1)
        prev_start = yesterday_start - timedelta(days=1)

        yesterday_count = self.user_repo.collection.count_documents(
            {"created_at": {"$gte": yesterday_start, "$lt": yesterday_end}}
        )
        previous_count = self.user_repo.collection.count_documents(
            {"created_at": {"$gte": prev_start, "$lt": yesterday_start}}
        )

        drop_ratio = (
            (previous_count - yesterday_count) / previous_count
            if previous_count > 0
            else 0.0
        )
        is_drop = previous_count > 0 and drop_ratio > 0.5
        message = (
            "New registrations dropped "
            f"{drop_ratio * 100:.1f}% vs previous day "
            f"({yesterday_count} vs {previous_count})."
        )
        return self._trigger("user_registration_drop", "warning", message, is_drop)

    def _product_rejection_alert(self, now):
        window_start = now - timedelta(hours=48)
        total = self.product_repo.collection.count_documents(
            {"created_at": {"$gte": window_start}}
        )
        rejected = self.product_repo.collection.count_documents(
            {"created_at": {"$gte": window_start}, "status": "rejected"}
        )
        rejection_rate = (rejected / total) if total else 0.0
        is_spike = total > 0 and rejection_rate > 0.3
        message = (
            f"Product rejection rate is {rejection_rate * 100:.1f}% in last 48h "
            f"({rejected}/{total} rejected listings)."
        )
        return self._trigger("product_rejection_spike", "critical", message, is_spike)

    def detect_anomalies(self):
        now = utcnow()
        alerts = []
        for detect_fn in (
            self._order_spike_alert,
            self._payment_failure_alert,
            self._user_registration_drop_alert,
            self._product_rejection_alert,
        ):
            alert = detect_fn(now)
            if alert:
                alerts.append(alert)
        return alerts

    def list_unresolved_alerts(self, limit=25):
        if self.alert_repo is None:
            return []
        return self.alert_repo.list_unresolved(limit=limit)

    def resolve_alert(self, alert_id, admin_id):
        if self.alert_repo is None:
            raise ServiceError("alerts not configured", status_code=500)
        updated = self.alert_repo.resolve(alert_id, resolved_by=admin_id)
        if not updated:
            raise ServiceError("alert not found or already resolved", status_code=404)
        return updated
