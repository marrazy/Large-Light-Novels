from openai import OpenAI
from utils.tools import chunk_text, format_prompt, parse_output
from utils.vectordb import get_context, store_info

def process_text(input_text, prompt_prefix, model_name, api_key):
    client = OpenAI(api_key=api_key)
    chunks = chunk_text(input_text)
    results = []
    for chunk in chunks:
        context = get_context(chunk)
        prompt = format_prompt(chunk, context, prompt_prefix)

        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1500
        )

        output = response.choices[0].message.content
        translation, extracted_info = parse_output(output)

        store_info(chunk, translation, extracted_info)
        results.append((chunk, translation, extracted_info))
    return results