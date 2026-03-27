import logging

from flask import Blueprint, current_app, jsonify, request

from app.repositories.offer_repository import OfferRepository
from app.services.exceptions import ServiceError
from app.services.offer_service import OfferService
from app.utils.request_auth import extract_user_identity

offers_bp = Blueprint("offers", __name__)
logger = logging.getLogger(__name__)


def _build_service():
    return OfferService(
        OfferRepository(current_app.db),
        page_size=current_app.config.get("ADMIN_PAGE_SIZE", 20),
        expiry_hours=current_app.config.get("OFFER_EXPIRY_HOURS", 24),
    )


def _error_response(error):
    logger.info("Offer API error", extra={"message": error.message, "status": error.status_code})
    return jsonify({"error": error.message, "status": error.status_code}), error.status_code


@offers_bp.post("/offers")
def create_offer_api():
    try:
        actor = extract_user_identity()
        payload = request.get_json(silent=True) or {}
        item = _build_service().create_offer(payload, actor)
        return jsonify({"item": item}), 201
    except ServiceError as error:
        return _error_response(error)


@offers_bp.patch("/offers/<offer_id>/respond")
def respond_offer_api(offer_id):
    try:
        actor = extract_user_identity()
        payload = request.get_json(silent=True) or {}
        item = _build_service().respond_offer(offer_id, payload, actor)
        return jsonify({"item": item})
    except ServiceError as error:
        return _error_response(error)


@offers_bp.get("/offers")
def list_offers_api():
    try:
        actor = extract_user_identity()
        result = _build_service().list_offers(request.args, actor)
        return jsonify(result)
    except ServiceError as error:
        return _error_response(error)
