

def chunk_text(text, max_chars=1000):
    return [text[i:i+max_chars] for i in range(0, len(text), max_chars)]

def format_prompt(input_text, context, prompt_prefix):
    return f"""
{prompt_prefix}

Here is some previous context:
{context}

Now translate the following text to English. Do NOT use Markdown. Westernize names if the romaji resembles western names (Such as Erenora to Elenora). Keep naming and pronouns consistent.
Also extract the following:
- Main characters and their descriptions
- Relationships
- Setting or location info
- Key events
You only need to extract key features and events, Keep it very short (Such as "Yumi travelled to Norham")

Return Format:
<Full Translation>

INFO:
<Extraction>

Begin translating after this text.

{input_text}

"""

def parse_output(output):
    if "INFO:" in output:
        translation, info = output.split("INFO:", 1)
    else:
        translation, info = output, ""
    return translation.strip(), info.strip()