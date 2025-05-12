import google.generativeai as genai
import os
from dotenv import load_dotenv
import json

# Configure Gemini API
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

def generate_most_likely_questions(questions_data, output_file="md/predicted_questions.md"):
    """
    Generate most likely questions based on provided questions data.
    
    Args:
        questions_data (list/dict): The JSON data containing questions
        output_file (str): Path where to save the markdown output
    
    Returns:
        str: The generated most likely questions in markdown format
    """
    # Initialize the model
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    # Get markdown content from optimized questions if available
    # Otherwise, convert questions_data to a readable format
    try:
        if os.path.exists("md/optimized_questions.md"):
            with open("md/optimized_questions.md", "r") as file:
                markdown_content = file.read()
        else:
            # If optimized questions markdown doesn't exist, format the JSON data
            markdown_content = json.dumps(questions_data, indent=2)
    except Exception as e:
        print(f"Error reading markdown content: {e}")
        markdown_content = json.dumps(questions_data, indent=2)
    
    # Construct prompt for Gemini
    prompt = (
        "You are a university professor predicting exam questions.\n"
        "Given the following content of past exam questions along with the information of [marks-year], "
        "analyze and return a Markdown list of the most likely or expected future questions.\n\n"
        "The questions should be in the same format as the given data.\n"
        f"{markdown_content}"
    )

    # Get response from Gemini
    response = model.generate_content(prompt)
    predicted_questions = response.text

    # Write to markdown file
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w") as file:
        file.write("# Most Likely Upcoming Questions\n\n")
        file.write(predicted_questions)

    print(f"Predicted questions written to: {output_file}")
    return predicted_questions

# If the script is run directly, use the sample file
if __name__ == "__main__":
    # === Step 3: Read your markdown content ===
    input_file = "md/optimized_questions.md"
    with open(input_file, "r") as file:
        markdown_content = file.read()
        
    # Use the function with the markdown content
    generate_most_likely_questions(markdown_content)
