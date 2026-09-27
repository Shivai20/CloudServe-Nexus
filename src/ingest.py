"""Multi-Channel Ingestion Module (A2).

Normalizes incoming tickets from Email, Live Chat, Docs Comments,
and Community Forums into a unified, validated NormalizedTicket representation.
"""

from typing import Any, Dict, List, Union
import json
import logging
from src.models import NormalizedTicket, TicketChannel

logger = logging.getLogger(__name__)

CHANNEL_MAP = {
    "email": TicketChannel.EMAIL,
    "mail": TicketChannel.EMAIL,
    "chat": TicketChannel.CHAT,
    "live_chat": TicketChannel.CHAT,
    "livechat": TicketChannel.CHAT,
    "docs_comment": TicketChannel.DOCS_COMMENT,
    "doc_comment": TicketChannel.DOCS_COMMENT,
    "docs": TicketChannel.DOCS_COMMENT,
    "forum": TicketChannel.FORUM,
    "community": TicketChannel.FORUM,
    "community_forum": TicketChannel.FORUM,
}


def normalize_channel(raw_channel: Any) -> TicketChannel:
    """Safely map arbitrary channel string to supported TicketChannel enum."""
    if not raw_channel or not isinstance(raw_channel, str):
        return TicketChannel.EMAIL
    cleaned = raw_channel.strip().lower().replace("-", "_").replace(" ", "_")
    return CHANNEL_MAP.get(cleaned, TicketChannel.EMAIL)


def normalize_ticket(data: Dict[str, Any]) -> NormalizedTicket:
    """Normalize a raw ticket dictionary into a validated NormalizedTicket.
    
    Handles missing fields, empty bodies, and irregular formats gracefully.
    """
    ticket_id = str(data.get("ticket_id") or data.get("id") or "UNKNOWN-TICKET")
    channel = normalize_channel(data.get("channel"))
    subject = str(data.get("subject") or "").strip()
    
    # Body extraction with fallback
    body = str(
        data.get("body")
        or data.get("content")
        or data.get("message")
        or data.get("text")
        or ""
    ).strip()
    
    received_at = data.get("received_at") or data.get("created_at") or None
    customer_id = data.get("customer_id")
    customer_name = data.get("customer_name")
    customer_tier = data.get("customer_tier") or "standard"
    customer_region = data.get("customer_region")
    language_fluency = data.get("language_fluency") or "fluent"

    return NormalizedTicket(
        ticket_id=ticket_id,
        channel=channel,
        subject=subject,
        body=body,
        received_at=str(received_at) if received_at else None,
        customer_id=str(customer_id) if customer_id else None,
        customer_name=str(customer_name) if customer_name else None,
        customer_tier=str(customer_tier),
        customer_region=str(customer_region) if customer_region else None,
        language_fluency=str(language_fluency),
        raw_data=data,
    )


def load_and_normalize_tickets(source: Union[str, List[Dict[str, Any]]]) -> List[NormalizedTicket]:
    """Load tickets from a file path or list of dictionaries, returning normalized tickets."""
    if isinstance(source, str):
        with open(source, "r", encoding="utf-8") as f:
            raw_list = json.load(f)
    elif isinstance(source, list):
        raw_list = source
    else:
        raise ValueError(f"Unsupported ticket source type: {type(source)}")

    normalized = []
    for item in raw_list:
        try:
            normalized.append(normalize_ticket(item))
        except Exception as e:
            logger.warning(f"Error normalizing ticket: {e}. Ingesting fallback.")
            normalized.append(
                NormalizedTicket(
                    ticket_id=str(item.get("ticket_id", "MALFORMED")),
                    channel=TicketChannel.EMAIL,
                    body=str(item.get("body", "")),
                    raw_data=item,
                )
            )
    return normalized
