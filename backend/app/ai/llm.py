try:
    import instructor
    from litellm import acompletion
    client = instructor.from_litellm(acompletion)
except ImportError:
    client = None
    acompletion = None

from pydantic import BaseModel
from typing import Type, TypeVar, Any
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog
import time

logger = structlog.get_logger()

T = TypeVar('T', bound=BaseModel)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def call_llm(
    prompt: str,
    response_model: Type[T],
    model: str = "groq/llama3-70b-8192",
    system_prompt: str = "You are a helpful AI assistant.",
    temperature: float = 0.0,
    **kwargs: Any
) -> T:
    """
    Core utility to call an LLM and get a structured response via Instructor.
    """
    start_time = time.time()
    logger.info("llm_call_started", model=model, response_model=response_model.__name__)
    
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            response_model=response_model,
            temperature=temperature,
            **kwargs
        )
        
        latency = time.time() - start_time
        logger.info("llm_call_success", model=model, latency_sec=round(latency, 3), response_model=response_model.__name__)
        
        return response
        
    except Exception as e:
        latency = time.time() - start_time
        logger.error("llm_call_failed", model=model, latency_sec=round(latency, 3), error=str(e))
        raise
