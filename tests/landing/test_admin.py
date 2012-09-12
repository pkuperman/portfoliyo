"""Tests for landing-page admin."""
from django.core.urlresolvers import reverse

from ..users import factories as user_factories
from . import factories



def test_lead_changelist(client):
    """The Lead admin changelist loads successfully."""
    admin = user_factories.UserFactory.create(is_staff=True, is_superuser=True)
    client.get(
        reverse("admin:landing_lead_changelist"), user=admin, status=200)


def test_lead_change(client):
    """The Lead admin change page loads successfully."""
    admin = user_factories.UserFactory.create(is_staff=True, is_superuser=True)
    lead = factories.LeadFactory.create()
    client.get(
        reverse("admin:landing_lead_change", args=[lead.id]),
        user=admin,
        status=200,
        )
