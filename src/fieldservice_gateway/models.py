from enum import Enum
from dataclasses import dataclass, field
from typing import Any

try:
    from pydantic import BaseModel, Field, HttpUrl
except ModuleNotFoundError:
    BaseModel = None  # type: ignore[assignment,misc]


class DispatchStatus(str, Enum):
    ASSIGNED = "assigned"
    ON_SITE = "on_site"
    AWAITING_REVIEW = "awaiting_review"
    COMPLETED = "completed"


if BaseModel is not None:
    class WorkOrderPhoto(BaseModel):
        url: HttpUrl
        caption: str = Field(min_length=1, max_length=240)


    class TechnicianFollowUp(BaseModel):
        technician_id: str = Field(min_length=1)
        note: str = Field(min_length=1, max_length=1000)
        customer_confirmed: bool = False


    class WorkOrderReviewRequest(BaseModel):
        work_order_id: str = Field(min_length=1)
        dispatch_status: DispatchStatus
        photos: list[WorkOrderPhoto] = Field(default_factory=list, max_length=8)
        follow_up: TechnicianFollowUp


    class WorkOrderReviewResponse(BaseModel):
        work_order_id: str
        dispatch_status: DispatchStatus
        photo_review: str | None = None
        next_action: str
else:
    @dataclass
    class WorkOrderPhoto:
        url: str
        caption: str


    @dataclass
    class TechnicianFollowUp:
        technician_id: str
        note: str
        customer_confirmed: bool = False


    @dataclass
    class WorkOrderReviewRequest:
        work_order_id: str
        dispatch_status: DispatchStatus
        photos: list[WorkOrderPhoto] = field(default_factory=list)
        follow_up: TechnicianFollowUp | None = None

        @classmethod
        def model_validate(cls, value: dict[str, Any]) -> "WorkOrderReviewRequest":
            return cls(
                work_order_id=value["work_order_id"],
                dispatch_status=DispatchStatus(value["dispatch_status"]),
                photos=[WorkOrderPhoto(**photo) for photo in value.get("photos", [])],
                follow_up=TechnicianFollowUp(**value["follow_up"]),
            )


    @dataclass
    class WorkOrderReviewResponse:
        work_order_id: str
        dispatch_status: DispatchStatus
        next_action: str
        photo_review: str | None = None
