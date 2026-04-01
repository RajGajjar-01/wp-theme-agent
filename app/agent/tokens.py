# Token tracking for Fireworks GLM-5

# Fireworks GLM-5 pricing (per 1M tokens)
PRICING = {
    "input": 1.0,  # $1.00 per 1M input tokens
    "cache_input": 0.20,  # $0.20 per 1M cached input tokens
    "output": 3.2,  # $3.20 per 1M output tokens
}

# Token tracking for session
_token_stats = {
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0,
    "total_cost": 0.0,
}


def reset_token_stats():
    """Reset token stats at start of each session."""
    _token_stats["prompt_tokens"] = 0
    _token_stats["completion_tokens"] = 0
    _token_stats["total_tokens"] = 0
    _token_stats["total_cost"] = 0.0


def get_token_stats():
    """Return current token stats."""
    return _token_stats.copy()


def calculate_cost(usage: dict) -> float:
    """Calculate cost based on Fireworks GLM-5 pricing."""
    input_tokens = usage.get("prompt_tokens", 0)
    output_tokens = usage.get("completion_tokens", 0)
    cache_tokens = usage.get("cached_prompt_tokens", 0)

    input_cost = (input_tokens / 1_000_000) * PRICING["input"]
    cache_cost = (cache_tokens / 1_000_000) * PRICING["cache_input"]
    output_cost = (output_tokens / 1_000_000) * PRICING["output"]

    return round(input_cost + cache_cost + output_cost, 6)


def update_token_stats(usage: dict):
    """Update token stats with usage from API response."""
    if usage:
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", 0)

        _token_stats["prompt_tokens"] += prompt_tokens
        _token_stats["completion_tokens"] += completion_tokens
        _token_stats["total_tokens"] += total_tokens
        _token_stats["total_cost"] += calculate_cost(usage)
