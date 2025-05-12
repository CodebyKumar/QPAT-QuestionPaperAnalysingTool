import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

def setup_api():
    """Set up the Google Generative AI API with the API key from environment variables."""
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        raise ValueError("Google API Key is not set. Please provide it in the .env file.")
    
    genai.configure(api_key=api_key)
    print("✅ API configured successfully")
    
def collect_all_questions(json_root_folder):
    """
    Recursively collect all JSON question data from subfolders.
    
    Args:
        json_root_folder (str): Path to the root folder containing JSON files
        
    Returns:
        list: List of question dictionaries
    """
    all_questions = []
    
    # Check if the folder exists
    if not os.path.exists(json_root_folder):
        print(f"❌ Folder not found: {json_root_folder}")
        return all_questions
        
    print(f"🔍 Searching for JSON files in {json_root_folder}")
    
    # Walk through all subdirectories
    for dirpath, _, filenames in os.walk(json_root_folder):
        for filename in filenames:
            if filename.endswith(".json"):
                full_path = os.path.join(dirpath, filename)
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        questions = json.load(f)
                        if isinstance(questions, list):
                            all_questions.extend(questions)
                            print(f"📄 Added {len(questions)} questions from {filename}")
                        elif isinstance(questions, dict):
                            all_questions.append(questions)
                            print(f"📄 Added 1 question from {filename}")
                except Exception as e:
                    print(f"⚠️ Error reading {full_path}: {e}")
    
    print(f"📊 Total questions collected: {len(all_questions)}")
    return all_questions

def ask_gemini_to_format(questions):
    """
    Send raw JSON question list to Gemini and request well-formatted Markdown.
    
    Args:
        questions (list): List of question dictionaries
        
    Returns:
        str: Formatted markdown text
    """
    print("🤖 Sending questions to Gemini for formatting...")
    
    prompt = f"""
You are an assistant that formats academic exam question banks into clean **Markdown**.

### Your task is:
1. Group all questions by `"subject"` and then by `"unit"` (e.g., Unit I, Unit II).
2. Within each unit, number the questions sequentially starting from 1.
3. If the **same question** appears in **multiple years** or with different marks, merge their appearances like this:
   - Example: `What is data mining? [6-2021, 4-2022]`
4. If a question includes a **table or structured data**, display that part as a properly formatted Markdown table. Ensure newlines before and after the table so it renders correctly.
5. Follow this **exact structure**:
Subject Name
Unit Name
Question text [marks-year, marks-year]
Another question [marks-year]
6. Use **Markdown** syntax for formatting, including:
- Headers
- Lists
- Tables
7. Do not include any additional text or explanations outside of the Markdown content.
8. each questions should be well structured and easy to read.
Here is the raw question data in JSON format:  
```json
{json.dumps(questions, indent=2)}

Return ONLY the formatted Markdown content. Do not include any explanation or surrounding text.
"""
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        print("✅ Received formatted response from Gemini")
        return response.text
    except Exception as e:
        print(f"❌ Error communicating with Gemini API: {e}")
        return None

def save_markdown(markdown_text, output_path):
    """
    Save the generated Markdown content to a file.
    
    Args:
        markdown_text (str): Formatted markdown text
        output_path (str): Path to save the output file
    """
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_text)
        print(f"✅ Optimized Markdown saved to '{output_path}'")
    except Exception as e:
        print(f"❌ Error saving markdown to {output_path}: {e}")

def recheck(markdown_text):
    """
    Recheck the generated Markdown content for any issues.
    
    Args:
        markdown_text (str): Formatted markdown text
        
    Returns:
        str: Cleaned markdown text
    """
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(markdown_text)
        print("✅ Received formatted response from Gemini")
        markdown_text = response.text
    except Exception as e:
        print(f"❌ Error communicating with Gemini API: {e}")
        return None
    
    return markdown_text


def main():
    """Main function to run the question bank formatter."""
    print("🚀 Starting Question Bank Formatter")
    
    # Configure paths
    json_folder = "json_data"
    output_file = "md/optimized_questions.md"
    
    # Setup API
    try:
        setup_api()
    except ValueError as e:
        print(f"❌ {e}")
        return
    
    # Step 1: Collect JSON data
    questions = collect_all_questions(json_folder)
    if not questions:
        print("❌ No questions found in the specified folder.")
        return
    
    # Step 2: Ask Gemini to generate Markdown
    markdown_output = ask_gemini_to_format(questions)
    markdown_output = recheck(markdown_output)
    if not markdown_output:
        print("❌ Failed to generate markdown.")
        return
    
    # Step 3: Save the Markdown file
    save_markdown(markdown_output, output_file)

if __name__ == "__main__":
    main()