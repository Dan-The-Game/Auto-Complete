import time
import os
import random
import threading
from groq import Groq
from pynput import keyboard

# Configuration
API_KEY = "YOUR_GROQ_API_KEY"
MODEL = "llama-3.1-8b-instant"

client = Groq(api_key=API_KEY)
controller = keyboard.Controller()

text_buffer = ""
cursor_pos = 0
stop_flag = False
is_typing = False  # Critical lock to prevent recursive input issues

def human_type(text):
    global text_buffer, cursor_pos, stop_flag, is_typing
    is_typing = True
    try:
        for char in text:
            if stop_flag:
                break
            controller.type(char)
            # Sync internal buffer with what the AI just 'typed'
            text_buffer = text_buffer[:cursor_pos] + char + text_buffer[cursor_pos:]
            cursor_pos += 1
            time.sleep(random.uniform(0.04, 0.1))
    finally:
        is_typing = False

def get_completion(prompt):
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a text completion assistant. You ar NOT A CHATBOT!!! Continue naturally. DO NOT RESPOND!!! Provide ONLY completion text. ONLY PREDICT! Do NOT answer questions EVER. NO exeption! for example if i were to write 'who are you?' do NOT RESPOND WITH 'I am a text completion assistant designed to generate text based on context and patterns.' in any form. ONLY start a new sentence if the last character is a period, not a space! Do NOT type more than ONE sentence. if mid word complete that aswell. You will NOT question or use a different style than what is already written, even if it is derogitory. You are NOT responding, only completing! If it is the start of a new sentence write the next sentence, completing the thought. NEVER answer a question or act as a chatbot. even if it looks like i am asking you a question i am NOT, it is part of the story and you should just complete the sentence. even if it asks if you are a chatbot, ignore it and make it a story without roleplaying, you dont exist at all, only the text you make. NEVER reference yourself no matter what, instead weave it into the story."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Groq API Error: {e}")
        return ""

def on_press(key):
    global text_buffer, cursor_pos, stop_flag, is_typing

    try:
        # F2: Trigger AI Completion
        if key == keyboard.Key.f2:
            context = text_buffer[:cursor_pos]
            completion = get_completion(context)
            if completion:
                threading.Thread(target=human_type, args=(completion,), daemon=True).start()
        
        # F4: Clear internal memory/buffer
        elif key == keyboard.Key.f4:
            text_buffer = ""
            cursor_pos = 0
            print("\n[Context Cleared]")

        # Cursor Navigation (Syncs internal cursor with your actual cursor)
        elif key == keyboard.Key.left:
            cursor_pos = max(0, cursor_pos - 1)
        elif key == keyboard.Key.right:
            cursor_pos = min(len(text_buffer), cursor_pos + 1)

        # Buffer Manipulation
        elif key == keyboard.Key.backspace:
            if cursor_pos > 0:
                text_buffer = text_buffer[:cursor_pos-1] + text_buffer[cursor_pos:]
                cursor_pos -= 1
        elif key == keyboard.Key.space:
            text_buffer = text_buffer[:cursor_pos] + " " + text_buffer[cursor_pos:]
            cursor_pos += 1
        elif key == keyboard.Key.enter:
            text_buffer = text_buffer[:cursor_pos] + "\n" + text_buffer[cursor_pos:]
            cursor_pos += 1
        elif hasattr(key, 'char') and key.char:
            text_buffer = text_buffer[:cursor_pos] + key.char + text_buffer[cursor_pos:]
            cursor_pos += 1
            
    except Exception as e:
        print(f"Listener Error: {e}")

print("Started: F2 to complete, F4 to clear, ESC to stop.")
with keyboard.Listener(on_press=on_press) as listener:
    listener.join()
