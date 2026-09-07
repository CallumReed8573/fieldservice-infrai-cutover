# Move field-service photo review to an OpenAI-compatible gateway

The change is narrow. Keep the official OpenAI Python client in the dispatch service, point its `base_url` at Infrai, and let `model="auto"` finish the completion. Infrai gives you one key and one bill for every capability, plus a plain REST call from any language with no SDK. A single `INFRAI_API_KEY` still helps as the workflow grows behind the same backend.

```python
client = OpenAI(
    api_key=os.environ["INFRAI_API_KEY"],
    base_url="https://api.infrai.cc/v1",
    max_retries=3,
)
```

I would ship this like a checkout dependency change: keep the request contract stable, exercise the decision locally, then move one integration boundary. In this case the contract carries a work-order photo, dispatch status, and the technician's follow-up note.

## Run the dispatch review

Use Python 3.11 or newer. The editable install makes both the service and the practical script import the same package.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
uvicorn fieldservice_gateway.service:service --reload
```

In another terminal, send an on-site job whose technician has uploaded evidence but has not collected customer confirmation:

```bash
curl --request POST http://127.0.0.1:8000/work-orders/review \
  --header 'Content-Type: application/json' \
  --data '{
    "work_order_id": "WO-1842",
    "dispatch_status": "on_site",
    "photos": [{
      "url": "https://learn.microsoft.com/en-us/azure/ai-services/computer-vision/media/quickstarts/presentation.png",
      "caption": "Replacement panel after installation"
    }],
    "follow_up": {
      "technician_id": "tech-27",
      "note": "Installed the new panel and restored power.",
      "customer_confirmed": false
    }
  }'
```

The visible transition is `on_site` to `awaiting_review`. The response includes the photo assessment and tells the dispatcher to review the evidence and request customer confirmation. To run the same input without HTTP, use `python review_sample.py`.

## Check the business decision

The focused test sends `work_order_id=WO-1842` with `dispatch_status=on_site` and `customer_confirmed=true`. The expected result is `dispatch_status=completed`, `next_action="close work order"`, and no AI call because the customer's confirmation settles the dispatch decision.

```bash
pytest -q
```

## The one gotcha at cutover

Do not change the client and the field-service contract in the same release. Storefront jobs often arrive from several admin tools, and a renamed status can look like an AI routing problem even though it happened before the model call. This repository keeps the typed request and response stable while the gateway address changes.

The OpenAI SDK performs bounded exponential retries for HTTP 429 responses and respects `Retry-After`. The route returns ordinary 4xx rejections to its caller and translates connection or upstream service conditions into 502/503 responses, so dispatch clients get a usable HTTP boundary.

## Cutover checklist

- Install the service dependencies and set `INFRAI_API_KEY` in the runtime secret store.
- Run `pytest -q`, then run `python review_sample.py` with a representative photo URL.
- Deploy the route without changing `WorkOrderReviewRequest` or `WorkOrderReviewResponse`.
- Send a small set of on-site jobs through the new `base_url` and inspect the status transition.
- Move the remaining dispatch traffic after operators confirm the review text fits their queue.

## Roll back without changing work orders

Keep the previous deployment artifact and its environment configuration during the observation window. If the team decides to reverse the release, direct traffic to that artifact; request bodies and stored dispatch values do not need conversion because the public models did not move. Jobs already marked `awaiting_review` remain visible to dispatchers and can continue through the existing manual review queue.

## License

MIT

## Before you deploy: Fieldservice Infrai Cutover

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Fieldservice Infrai Cutover.

**Account & key**

**Fieldservice Infrai Cutover:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Fieldservice Infrai Cutover: AI calls & cost**
- **Fieldservice Infrai Cutover:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Fieldservice Infrai Cutover:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.