"""Query predicates that keep WhatsApp demo traffic out of business views.

Visitors who reach the CRM through the shared `whatsapp_gateway` are persisted
as ordinary rows — a Contact, a zero-amount lead Deal, and Messages — so that an
operator can reply to them from the inbox. That reply is the whole point of the
CRM demo, so those rows must stay reachable.

They must not reach the curated numbers and lists the CRM puts in front of
prospects, though: a dashboard full of leads named after phone numbers and worth
RM 0 undercuts the product being demonstrated. Inbound marks these contacts with
`Contact.is_gateway` (see `whatsapp_service._handle_message`), and the helpers
below turn that flag into query predicates.

Applied to dashboards, analytics, contact lists and the pipeline. Deliberately
NOT applied to the message inbox or to single-contact lookups by id.
"""

from sqlalchemy import or_, select

from app.models.contact import Contact
from app.models.deal import Deal
from app.models.message import Message


def _demo_contact_ids():
    return select(Contact.id).where(Contact.is_gateway.is_(True))


def contact_not_demo():
    return Contact.is_gateway.is_(False)


def deal_not_demo():
    """Deals whose contact is not a demo visitor.

    Deal carries no flag of its own, so this goes through Contact.
    `Deal.contact_id` is NOT NULL, so a plain `notin_` is safe here.
    """
    return Deal.contact_id.notin_(_demo_contact_ids())


def message_not_demo():
    """Messages whose contact is not a demo visitor.

    `Message.contact_id` is nullable and `NULL NOT IN (...)` evaluates to NULL,
    which would silently drop every contact-less message (e.g. unmatched email).
    The explicit NULL branch keeps them.
    """
    return or_(
        Message.contact_id.is_(None),
        Message.contact_id.notin_(_demo_contact_ids()),
    )
