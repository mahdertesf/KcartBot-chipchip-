import os
from google import genai

# Initialize Gemini client
client = genai.Client(api_key=os.environ.get('GOOGLE_API_KEY'))

def identify_language(text: str) -> str:
    """
    Identifies the language of the input text.
    Returns one of: 'english', 'amharic', 'amharic_latin', or 'other'
    """
    try:
        prompt = f"""You are a language classifier. Classify the following text into EXACTLY ONE of these categories:
- 'english': Text is in English
- 'amharic': Text is in Amharic using Fidel script (ሀ, ለ, ሐ, etc.)
- 'amharic_latin': Text is Amharic transliterated using Latin alphabet (e.g., "selam", "ishi")
- 'other': Any other language

Examples:
Input: "Hello, how are you?"
Output: english

Input: "ሰላም እንደምን ነህ?"
Output: amharic

Input: "selam indemin neh?"
Output: amharic_latin

Input: "Bonjour comment allez-vous?"
Output: other

Now classify this text. Respond with ONLY the category name, nothing else:
Text: "{text}"
"""
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        result = (response.text or '').strip().lower()
        
        # Validate the response
        valid_languages = ['english', 'amharic', 'amharic_latin', 'other']
        if result in valid_languages:
            return result
        else:
            return 'other'
            
    except Exception as e:
        print(f"Error in identify_language: {e}")
        return 'other'


def translate_to_english(text: str) -> str:
    """
    Translates Amharic text (Fidel or Latin script) to English.
    Preserves the core intent of the user's request.
    """
    try:
        prompt = f"""You are a professional Amharic to English translator. 
Translate the following Amharic text to English, preserving the core intent and meaning.
If the text is a question or request, maintain that tone in the translation.

Amharic text: "{text}"

Provide ONLY the English translation, nothing else:"""
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return (response.text or text).strip()
        
    except Exception as e:
        print(f"Error in translate_to_english: {e}")
        return text  # Return original text if translation fails


def translate_from_english(text: str, target_language: str) -> str:
    """
    Translates English text to the target language.
    target_language should be 'amharic' or 'amharic_latin'
    """
    try:
        # Handle None or empty text
        if not text:
            return ""
        
        if target_language == 'amharic':
            script_instruction = "Translate the provided english text to Amharic using the Fidel script (ሀ, ለ, ሐ, etc.)."
        elif target_language == 'amharic_latin':
            script_instruction = "Translate the provided english text to Amharic using the Fidel script (ሀ, ለ, ሐ, etc.)."
        else:
            return text  # Return original if target language is not supported
        
        prompt = f"""{script_instruction}
Maintain the tone and meaning of the original message.

English text: "{text}"

Provide ONLY the translation, nothing else:"""
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        result = response.text if response.text else text
        return result.strip() if result else ""
        
    except Exception as e:
        print(f"Error in translate_from_english: {e}")
        return text if text else ""  # Return original text if translation fails

