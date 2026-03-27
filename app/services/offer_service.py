import logging
from datetime import timedelta

from app.services.exceptions import ServiceError
from app.utils.pagination import parse_pagination
from app.utils.time_utils import utcnow
from app.utils.validators import ACTIVE_OFFER_STATUSES, is_valid_offer_transition

logger = logging.getLogger(__name__)


class OfferService:
    def __init__(self, offer_repo, page_size=20, expiry_hours=24):
        self.offer_repo = offer_repo
        self.page_size = page_size
        self.expiry_hours = expiry_hours

    def create_offer(self, payload, actor):
        actor_user = self._load_actor(actor, required_role="buyer")
        product_id = self._clean_string(payload.get("product_id"), "product_id")
        price = self._as_positive_number(payload.get("price"), "price")
        quantity = self._as_positive_int(payload.get("quantity"), "quantity")
        note = self._clean_optional(payload.get("note"))

        product = self.offer_repo.find_product_by_id(product_id)
        if not product:
            raise ServiceError("Product not found", status_code=404)

        farmer_id = self._owner_from_product(product)
        if not farmer_id:
            raise ServiceError("Product owner not set", status_code=400)
        if farmer_id == actor_user["id"]:
            raise ServiceError("Farmer cannot create offer on own product", status_code=403)

        self.offer_repo.expire_active_offer_for_pair(product_id, actor_user["id"])
        expires_at = utcnow() + timedelta(hours=self.expiry_hours)
        created, error = self.offer_repo.create_offer(
            product_id=product_id,
            buyer_id=actor_user["id"],
            farmer_id=farmer_id,
            price=price,
            quantity=quantity,
            expires_at=expires_at,
            note=note,
        )
        if error == "duplicate_active_offer":
            raise ServiceError(
                "Active offer already exists for this buyer and product",
                status_code=409,
            )
        if not created:
            logger.error("Offer create failed unexpectedly", extra={"product_id": product_id})
            raise ServiceError("Unable to create offer", status_code=500)
        return created

    def list_offers(self, query_args, actor):
        actor_user = self._load_actor(actor)
        product_id = self._clean_string(query_args.get("product_id"), "product_id")
        product = self.offer_repo.find_product_by_id(product_id)
        if not product:
            raise ServiceError("Product not found", status_code=404)

        farmer_id = self._owner_from_product(product)
        if actor_user["role"] == "farmer" and actor_user["id"] != farmer_id:
            raise ServiceError("Only owner farmer can view offers", status_code=403)

        self.offer_repo.expire_offers_for_product(product_id)
        pagination = parse_pagination(query_args, default_page_size=self.page_size)
        buyer_id = actor_user["id"] if actor_user["role"] == "buyer" else None
        items, meta = self.offer_repo.list_by_product(
            product_id=product_id,
            page=pagination["page"],
            page_size=pagination["page_size"],
            buyer_id=buyer_id,
        )
        return {"items": items, "pagination": meta}

    def respond_offer(self, offer_id, payload, actor):
        actor_user = self._load_actor(actor, required_role="farmer")
        response = self._clean_string(payload.get("response"), "response").lower()
        if response not in {"accepted", "rejected", "countered"}:
            raise ServiceError("response must be accepted, rejected, or countered", status_code=400)

        offer = self.offer_repo.find_by_id(offer_id)
        if not offer:
            raise ServiceError("Offer not found", status_code=404)

        if offer.get("farmer_id") != actor_user["id"]:
            raise ServiceError("Only product owner can respond to offer", status_code=403)

        expired_doc = self.offer_repo.expire_offer_if_needed(offer_id)
        if expired_doc:
            raise ServiceError("Offer expired", status_code=409)

        current_status = offer.get("status", "")
        if current_status == "accepted":
            raise ServiceError("Offer already accepted", status_code=409)
        if current_status == "expired":
            raise ServiceError("Offer expired", status_code=409)
        if not is_valid_offer_transition(current_status, response):
            raise ServiceError(
                f"Invalid offer transition from '{current_status}' to '{response}'",
                status_code=400,
            )

        note = self._clean_optional(payload.get("note"))
        expected_statuses = ACTIVE_OFFER_STATUSES
        counter_price = None
        counter_quantity = None
        if response == "countered":
            counter_price = self._as_positive_number(payload.get("price"), "price")
            counter_quantity = self._as_positive_int(payload.get("quantity"), "quantity")

        updated = self.offer_repo.respond_offer(
            offer_id=offer_id,
            expected_statuses=expected_statuses,
            response_status=response,
            actor_id=actor_user["id"],
            actor_role=actor_user["role"],
            counter_price=counter_price,
            counter_quantity=counter_quantity,
            note=note,
            counter_expiry_hours=self.expiry_hours,
        )
        if not updated:
            logger.warning(
                "Offer respond race/conflict",
                extra={"offer_id": offer_id, "response": response, "farmer_id": actor_user["id"]},
            )
            latest = self.offer_repo.find_by_id(offer_id)
            if latest and latest.get("status") == "accepted":
                raise ServiceError("Offer already accepted", status_code=409)
            if latest and latest.get("expires_at") and latest.get("expires_at") <= utcnow():
                raise ServiceError("Offer expired", status_code=409)
            raise ServiceError("Offer state changed; retry", status_code=409)
        return updated

    def _owner_from_product(self, product):
        for field in ("farmer_id", "seller_id", "owner_id", "user_id"):
            user_id = product.get(field)
            if user_id:
                owner = self.offer_repo.find_user_by_id(user_id)
                if owner and owner.get("role") == "farmer":
                    return str(owner["_id"])

        for field in ("seller_email", "owner_email", "farmer_email"):
            email = product.get(field)
            if email:
                owner = self.offer_repo.find_user_by_email(email)
                if owner and owner.get("role") == "farmer":
                    return str(owner["_id"])
        return None

    def _load_actor(self, actor, required_role=None):
        role = actor.get("role")
        user_id = self._clean_string(actor.get("user_id"), "user_id")
        user = self.offer_repo.find_user_by_id(user_id)
        if not user:
            raise ServiceError("Unauthorized user", status_code=401)
        if user.get("status") != "active":
            raise ServiceError("User account is not active", status_code=403)
        if role != user.get("role"):
            raise ServiceError("Unauthorized role", status_code=403)
        if required_role and role != required_role:
            raise ServiceError("Unauthorized role", status_code=403)
        return {"id": str(user["_id"]), "role": role}

    def _clean_string(self, value, field):
        sanitized = str(value or "").replace("\x00", "").strip()
        if not sanitized:
            raise ServiceError(f"{field} is required", status_code=400)
        return sanitized

    def _clean_optional(self, value):
        if value is None:
            return None
        cleaned = str(value).replace("\x00", "").strip()
        return cleaned or None

    def _as_positive_number(self, value, field):
        try:
            numeric = float(value)
        except (TypeError, ValueError) as exc:
            raise ServiceError(f"{field} must be a number", status_code=400) from exc
        if numeric <= 0:
            raise ServiceError(f"{field} must be > 0", status_code=400)
        return numeric

    def _as_positive_int(self, value, field):
        try:
            numeric = int(value)
        except (TypeError, ValueError) as exc:
            raise ServiceError(f"{field} must be an integer", status_code=400) from exc
        if numeric <= 0:
            raise ServiceError(f"{field} must be > 0", status_code=400)
        return numeric
