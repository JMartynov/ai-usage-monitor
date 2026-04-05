from app.config.pricing import MODEL_PRICING, DEFAULT_PRICING

def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    if prompt_tokens is None:
        prompt_tokens = 0
    if completion_tokens is None:
        completion_tokens = 0

    pricing = MODEL_PRICING.get(model, DEFAULT_PRICING)

    input_cost = (prompt_tokens / 1000) * pricing["input_per_1k"]
    output_cost = (completion_tokens / 1000) * pricing["output_per_1k"]

    return round(input_cost + output_cost, 6)
