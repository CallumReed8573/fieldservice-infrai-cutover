from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from openai import OpenAI
else:
    OpenAI = Any

from .models import DispatchStatus, WorkOrderReviewRequest, WorkOrderReviewResponse


def needs_photo_review(work_order: WorkOrderReviewRequest) -> bool:
    return (
        work_order.dispatch_status == DispatchStatus.ON_SITE
        and bool(work_order.photos)
        and not work_order.follow_up.customer_confirmed
    )


def review_work_order(
    work_order: WorkOrderReviewRequest, client: OpenAI
) -> WorkOrderReviewResponse:
    if not needs_photo_review(work_order):
        next_action = (
            "close work order"
            if work_order.follow_up.customer_confirmed
            else "collect an on-site photo and customer confirmation"
        )
        status = (
            DispatchStatus.COMPLETED
            if work_order.follow_up.customer_confirmed
            else work_order.dispatch_status
        )
        return WorkOrderReviewResponse(
            work_order_id=work_order.work_order_id,
            dispatch_status=status,
            next_action=next_action,
        )

    photo_content = [
        {"type": "image_url", "image_url": {"url": str(photo.url)}}
        for photo in work_order.photos
    ]
    prompt = (
        "Review these field-service photos against the technician note. "
        "State visible completion evidence and the next dispatcher action in two sentences. "
        f"Technician note: {work_order.follow_up.note}"
    )
    completion = client.chat.completions.create(
        model="auto",
        messages=[
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}, *photo_content],
            }
        ],
    )
    review = completion.choices[0].message.content or "Review recorded."
    return WorkOrderReviewResponse(
        work_order_id=work_order.work_order_id,
        dispatch_status=DispatchStatus.AWAITING_REVIEW,
        photo_review=review,
        next_action="dispatcher reviews evidence and requests customer confirmation",
    )
