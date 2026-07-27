"""Script stage: turn a block's raw source data into drill sentence pairs.

One LLM call per block using structured output, so only clean {target, native}
string values are ever produced -- no markdown, numbering, or headers that would
otherwise be read aloud by the TTS.
"""

import json


def _schema(target_code: str, native_code: str) -> dict:
    return {
        "name": "drill_sentences",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "sentences": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            target_code: {"type": "string"},
                            native_code: {"type": "string"},
                        },
                        "required": [target_code, native_code],
                        "additionalProperties": False,
                    },
                }
            },
            "required": ["sentences"],
            "additionalProperties": False,
        },
    }


def _system_prompt(config, block) -> str:
    return (
        f"You are a {config.target_language} teacher creating a listening drill for a "
        f"beginner student named {config.user_name} (level {config.level}).\n"
        f"Rewrite the provided data into at most {block.target_sentences} short, simple "
        f"{config.target_language} sentence(s), using {config.dialect} {config.target_language}.\n"
        f"Task for this section: {block.prompt}\n\n"
        "Rules:\n"
        "- Use simple grammar and high-frequency vocabulary.\n"
        "- Each sentence must be short enough to hear and repeat easily.\n"
        f"- For every sentence provide the {config.target_language} ('{config.target_code}') "
        f"and a natural {config.native_language} translation ('{config.native_code}').\n"
        "- Return ONLY the structured data. Never use markdown, numbering, bullet points, "
        "headings, or emoji -- the text is read aloud verbatim."
    )


def generate_sentences(client, config, block, raw_data) -> list[dict[str, str]]:
    response = client.chat.completions.create(
        model=config.llm.get("model", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": _system_prompt(config, block)},
            {"role": "user", "content": str(raw_data)},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": _schema(config.target_code, config.native_code),
        },
    )
    content = response.choices[0].message.content
    data = json.loads(content)
    sentences = data.get("sentences", [])
    if not sentences:
        raise ValueError("LLM returned no sentences")
    return sentences
