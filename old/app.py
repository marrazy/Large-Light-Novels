#Gradio UI
import gradio as gr
from main import process_text
from utils.library import create_new_library, set_active_library, save_current_library
from utils.vectordb import undo_last_entry

API_KEY = ""
MODEL = "gpt-3.5-turbo"
LANGUAGE_PROMPT_MAP = {
    "JP": "You are translating a Japanese light novel",
    "KR": "You are translating a Korean light novel",
    "CN": "You are translating a Chinese light novel"
}

libraries = []
current_library = None

def handle_translate(text, lang, model_name, key):
    global API_KEY, MODEL
    API_KEY = key
    MODEL = model_name
    prompt_prefix = LANGUAGE_PROMPT_MAP.get(lang, "You are translating a light novel.")
    result = process_text(text, prompt_prefix=prompt_prefix, model_name=MODEL, api_key=API_KEY)

    return "\n\n".join([r[1] for r in result])

def handle_new_library(name):
    global current_library
    if not name or name.strip() == "":
        return gr.update(choices=libraries, value=None)
    
    if name in libraries:
        return gr.update(choices=libraries, value=None)
    
    if current_library and current_library in libraries:
        save_current_library(current_library)
    
    libraries.append(name)
    create_new_library(name)
    set_active_library(name)
    current_library = name
    return gr.update(choices=libraries, value=name)

def handle_switch_library(name):
    global current_library
    if name and name in libraries:
        if current_library and current_library in libraries:
            save_current_library(current_library)
        set_active_library(name)
        current_library = name

def handle_undo():
    undo_last_entry()
    return "Last entry removed."

with gr.Blocks() as app:
    with gr.Row():
        lang_dd = gr.Dropdown(label="Source Language", choices=["Japanese", "Korean", "Chinese"], value="Japanese")
        model_dd = gr.Dropdown(label="Model", choices=["gpt-3.5-turbo", "gpt-4"], value="gpt-3.5-turbo")
        key_box = gr.Textbox(label="OpenAI API Key", type="password")

    with gr.Row():
        text_box = gr.Textbox(lines=10, label="Untranslated Text")
        out_box = gr.Textbox(label="Translated Output")

    translate_btn = gr.Button("Translate")
    undo_btn = gr.Button("Undo Last")

    with gr.Row():
        lib_name = gr.Textbox(label="New Novel Name")
        create_btn = gr.Button("New Library")
        lib_dd = gr.Dropdown(label="Saved Libraries", choices=libraries)
        switch_btn = gr.Button("Switch")

    translate_btn.click(handle_translate, inputs=[text_box, lang_dd, model_dd, key_box], outputs=out_box)
    undo_btn.click(handle_undo, outputs=out_box)
    create_btn.click(handle_new_library, inputs=[lib_name], outputs=lib_dd)
    switch_btn.click(handle_switch_library, inputs=[lib_dd])

app.launch()