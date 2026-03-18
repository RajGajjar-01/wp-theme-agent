import json
import logging
import re
from typing import TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def strip_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()


async def llm_parse(
    client: AsyncOpenAI,
    model: str,
    messages: list[dict],
    response_model: type[T],
    temperature: float = 0.1,
) -> T:
    """
    Call an OpenAI-compatible API and parse the response into a Pydantic model.
    """

    # --- Attempt 1: Structured output via beta.parse ---
    try:
        completion = await client.beta.chat.completions.parse(
            model=model,
            messages=messages,
            response_format=response_model,
            temperature=temperature,
        )
        parsed = completion.choices[0].message.parsed
        if parsed is not None:
            logger.debug("Structured output succeeded for %s", response_model.__name__)
            return parsed
    except Exception as e:
        logger.debug("Structured output not supported, falling back to manual parse: %s", e)

    # --- Attempt 2: Manual JSON extraction + Pydantic validation ---
    completion = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    raw_text = completion.choices[0].message.content or ""
    cleaned = strip_fences(raw_text)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error("JSON parse failed for %s: %s\nRaw text: %s", response_model.__name__, e, raw_text[:500])
        raise ValueError(f"LLM returned invalid JSON for {response_model.__name__}: {e}") from e

    try:
        return response_model.model_validate(data)
    except ValidationError as e:
        logger.error("Pydantic validation failed for %s: %s\nData: %s", response_model.__name__, e, str(data)[:500])
        raise ValueError(f"LLM output failed validation for {response_model.__name__}: {e}") from e


async def llm_parse_list(
    client: AsyncOpenAI,
    model: str,
    messages: list[dict],
    item_model: type[T],
    temperature: float = 0.1,
) -> list[T]:
    """
    Call an OpenAI-compatible API and parse the response as a JSON array
    of Pydantic model instances.
    """
    completion = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    raw_text = completion.choices[0].message.content or ""
    cleaned = strip_fences(raw_text)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error("JSON parse failed for list[%s]: %s\nRaw text: %s", item_model.__name__, e, raw_text[:500])
        raise ValueError(f"LLM returned invalid JSON for list[{item_model.__name__}]: {e}") from e

    if not isinstance(data, list):
        raise ValueError(f"Expected JSON array for list[{item_model.__name__}], got {type(data).__name__}")

    items: list[T] = []
    for i, item_data in enumerate(data):
        try:
            items.append(item_model.model_validate(item_data))
        except ValidationError as e:
            logger.warning("Skipping invalid item %d in list[%s]: %s", i, item_model.__name__, e)

    return items
