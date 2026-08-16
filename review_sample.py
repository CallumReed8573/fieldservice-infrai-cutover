from fieldservice_gateway.dispatch_review import review_work_order
from fieldservice_gateway.models import WorkOrderReviewRequest
from fieldservice_gateway.service import build_ai_client


sample = WorkOrderReviewRequest.model_validate(
    {
        "work_order_id": "WO-1842",
        "dispatch_status": "on_site",
        "photos": [
            {
                "url": "https://learn.microsoft.com/en-us/azure/ai-services/computer-vision/media/quickstarts/presentation.png",
                "caption": "Replacement panel after installation",
            }
        ],
        "follow_up": {
            "technician_id": "tech-27",
            "note": "Installed the new panel and restored power.",
            "customer_confirmed": False,
        },
    }
)

print(review_work_order(sample, build_ai_client()).model_dump_json(indent=2))
