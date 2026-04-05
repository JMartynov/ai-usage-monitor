from app.services.pricing import calculate_cost
from app.config.pricing import MODEL_PRICING, DEFAULT_PRICING

def test_known_model_pricing_correct():
    model = "gpt-4o"
    prompt_tokens = 1000
    completion_tokens = 1000

    expected_cost = MODEL_PRICING[model]["input_per_1k"] + MODEL_PRICING[model]["output_per_1k"]
    cost = calculate_cost(model, prompt_tokens, completion_tokens)

    assert cost == expected_cost

def test_unknown_model_uses_default():
    model = "unknown-model-123"
    prompt_tokens = 1000
    completion_tokens = 1000

    expected_cost = DEFAULT_PRICING["input_per_1k"] + DEFAULT_PRICING["output_per_1k"]
    cost = calculate_cost(model, prompt_tokens, completion_tokens)

    assert cost == expected_cost

def test_zero_tokens_zero_cost():
    model = "gpt-4o"
    prompt_tokens = 0
    completion_tokens = 0

    cost = calculate_cost(model, prompt_tokens, completion_tokens)

    assert cost == 0.0

def test_none_tokens_zero_cost():
    model = "gpt-4o"

    cost = calculate_cost(model, None, None)

    assert cost == 0.0
