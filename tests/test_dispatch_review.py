from fieldservice_gateway.dispatch_review import review_work_order
from fieldservice_gateway.models import WorkOrderReviewRequest


def test_customer_confirmation_closes_work_order_without_ai_call() -> None:
    request = WorkOrderReviewRequest.model_validate(
        {
            "work_order_id": "WO-1842",
            "dispatch_status": "on_site",
            "photos": [],
            "follow_up": {
                "technician_id": "tech-27",
                "note": "Customer checked the repaired storefront lighting.",
                "customer_confirmed": True,
            },
        }
    )

    result = review_work_order(request, client=None)  # type: ignore[arg-type]

    assert result.dispatch_status.value == "completed"
    assert result.next_action == "close work order"
    assert result.photo_review is None
