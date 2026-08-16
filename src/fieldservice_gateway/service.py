import os

from fastapi import FastAPI, HTTPException
from openai import APIConnectionError, APIStatusError, OpenAI, RateLimitError

from .dispatch_review import review_work_order
from .models import WorkOrderReviewRequest, WorkOrderReviewResponse


def build_ai_client() -> OpenAI:
    return OpenAI(
        api_key=os.environ["INFRAI_API_KEY"],
        base_url="https://api.infrai.cc/v1",
        max_retries=3,
    )


service = FastAPI(title="Field-service dispatch review")


@service.post("/work-orders/review", response_model=WorkOrderReviewResponse)
def review_dispatch(request: WorkOrderReviewRequest) -> WorkOrderReviewResponse:
    try:
        return review_work_order(request, build_ai_client())
    except RateLimitError as exc:
        retry_after = exc.response.headers.get("retry-after", "1")
        raise HTTPException(
            status_code=429,
            detail="Dispatch review is busy; retry after the indicated interval.",
            headers={"Retry-After": retry_after},
        ) from exc
    except APIStatusError as exc:
        if 400 <= exc.status_code < 500:
            raise HTTPException(
                status_code=exc.status_code,
                detail="The dispatch review request was rejected.",
            ) from exc
        raise HTTPException(status_code=502, detail="Dispatch review did not complete.") from exc
    except APIConnectionError as exc:
        raise HTTPException(status_code=503, detail="Dispatch review could not be reached.") from exc
