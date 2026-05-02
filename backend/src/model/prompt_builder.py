"""
prompt_builder.py
─────────────────
Builds structured prompts for the two-round Gemini VLM pipeline.
Supports optional RAG context injection for few-shot grounding.
"""


def build_round1_prompt(rag_context: str = "") -> str:
    """Build the initial radiologist prompt, optionally grounded with RAG context.

    Parameters
    ----------
    rag_context : str
        Pre-formatted string of similar retrieved cases (from RAGRetriever).
        If empty, the prompt is sent without few-shot examples.
    """
    context_block = ""
    if rag_context and rag_context.strip():
        context_block = f"""
For reference, here are similar cases from the radiology database:

{rag_context}

Use these only as reference. Analyze the current X-ray independently.
"""

    return f"""You are an expert radiologist analyzing a chest X-ray. Please carefully evaluate the image and provide a highly detailed clinical report.
{context_block}
You MUST respond STRICTLY in the following format with no extra text or conversational filler:

FINDINGS: [detailed observations regarding the lungs, heart, pleura, bones, and any abnormalities]
IMPRESSION: [concise clinical conclusion synthesizing the findings]
SEVERITY: [exactly one of: NORMAL / MILD / MODERATE / CRITICAL]
FOLLOW_UP: [recommended next steps or 'None' if not applicable]
"""


def build_round2_prompt(preliminary_report: str) -> str:
    """Build the refinement prompt for the second pass.

    Parameters
    ----------
    preliminary_report : str
        Raw text output from the Round 1 generation.
    """
    return f"""You are an expert reviewing radiologist. Please re-examine the provided chest X-ray along with the preliminary report below.

Your task is to:
1. Check for any missed findings or inaccuracies.
2. Verify the severity assessment.
3. Improve the clinical language for clarity and precision.
4. Note any significant deviations from the preliminary report.

Preliminary Report:
{preliminary_report}

You MUST respond STRICTLY in the following format with no extra text or conversational filler:

FINDINGS: [detailed observations regarding the lungs, heart, pleura, bones, and any abnormalities]
IMPRESSION: [concise clinical conclusion synthesizing the findings]
SEVERITY: [exactly one of: NORMAL / MILD / MODERATE / CRITICAL]
FOLLOW_UP: [recommended next steps or 'None' if not applicable]
DEVIATIONS: [any significant changes from the preliminary report, or 'None']
"""
