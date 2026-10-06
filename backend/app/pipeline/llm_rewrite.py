"""Optional small-model rewrite of the deterministic template summary into
smoother prose. Strictly a rephrasing pass: the model is given the exact
template text and told only to polish wording, never to add numbers,
claims, or recommendations it wasn't handed. Off by default
(USE_LLM_SUMMARY_REWRITE in settings) -- the template summary is already
correct and this adds model-load latency for a wording upgrade only.
"""
from __future__ import annotations

from functools import lru_cache

from app.config.settings import LLM_SUMMARY_MODEL

_PROMPT_PREFIX = (
    "Rewrite the following product review summary in smoother, more natural "
    "English. Do not add any new facts, numbers, or recommendations. Keep "
    "every number and claim exactly as given. Text: "
)


@lru_cache(maxsize=1)
def _get_pipeline():
    from transformers import pipeline

    return pipeline("text2text-generation", model=LLM_SUMMARY_MODEL)


def rewrite_summary(template_text: str) -> str:
    """Returns a rephrased version of template_text, or the original text
    unchanged if the rewrite looks unreliable (empty, way too short/long,
    or the model errors out) -- never let this step silently corrupt the
    factual summary.
    """
    try:
        pipe = _get_pipeline()
        result = pipe(_PROMPT_PREFIX + template_text, max_new_tokens=160, do_sample=False)
        rewritten = result[0]["generated_text"].strip()
    except Exception:
        return template_text

    if not rewritten or len(rewritten) < 0.4 * len(template_text):
        return template_text
    return rewritten
