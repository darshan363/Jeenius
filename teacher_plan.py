"""JEENIUS Teacher Plan policy. All features in this rollout are free."""

PAYMENT_ENFORCEMENT_ENABLED = False
TEACHER_PLAN_WAS_PRICE_INR = 999
TEACHER_PLAN_PRICE_INR = 0
TEACHER_PLAN_BILLING = "monthly"


def ai_access_allowed(user):
    """No payment is required in this rollout; account verification/approval is enforced elsewhere."""
    return True


def teacher_plan_message(user=None):
    return "JEENIUS Teacher Plan is currently free (₹0). Complete the required account setup and admin approval to use AI."


def teacher_plan_summary():
    return {
        "name": "Teacher Plan",
        "original_price_inr": TEACHER_PLAN_WAS_PRICE_INR,
        "price_inr": TEACHER_PLAN_PRICE_INR,
        "billing": TEACHER_PLAN_BILLING,
        "payment_enforcement_enabled": PAYMENT_ENFORCEMENT_ENABLED,
        "payment_integration": "not_configured",
        "included_features": ["searchable animation catalogue", "interactive labs"],
    }
