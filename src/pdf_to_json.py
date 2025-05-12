import os
import re
import json
import fitz  # PyMuPDF
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def configure_gemini_api():
    """Configure the Gemini API using the API key from the .env file."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("Google API Key is not set. Please provide it in the .env file.")
    genai.configure(api_key=api_key)
    print("Gemini API configured successfully.")

def extract_text_from_pdf(pdf_path):
    """
    Extracts all text and tables from a PDF file.
    Returns a structured string containing the extracted content.
    """
    try:
        with fitz.open(pdf_path) as doc:
            full_text = ""
            
            # Extract metadata to help with subject identification
            metadata = doc.metadata
            if metadata.get("subject"):
                full_text += f"Subject: {metadata.get('subject')}\n\n"
            if metadata.get("title"):
                full_text += f"Title: {metadata.get('title')}\n\n"
            
            # Process each page
            for page_num, page in enumerate(doc, start=1):
                full_text += f"=== Page {page_num} ===\n"
                
                # Get text with layout recognition
                blocks = page.get_text("dict")["blocks"]
                for block in blocks:
                    if block["type"] == 0:  # Text block
                        for line in block["lines"]:
                            line_text = " ".join(span["text"] for span in line["spans"])
                            if line_text.strip():
                                full_text += line_text + "\n"
                        
                        # Add extra newline between text blocks for readability
                        full_text += "\n"
                
                # Try to identify tables using structure recognition
                tables = []
                try:
                    # Simple table detection heuristic - look for aligned text blocks
                    for block in blocks:
                        if block["type"] == 0 and "lines" in block:
                            lines = [" ".join(span["text"] for span in line["spans"]) for line in block["lines"]]
                            
                            # Check if this might be tabular data
                            if len(lines) >= 2:
                                # Look for consistent spacing patterns or delimiter characters
                                potential_table = True
                                for line in lines:
                                    # Skip very short lines
                                    if len(line) < 5:
                                        continue
                                    # Check for multiple spaces, tabs, or pipe characters
                                    if '  ' not in line and '\t' not in line and '|' not in line:
                                        potential_table = False
                                        break
                                
                                if potential_table:
                                    tables.append("\n".join(lines))
                    
                    if tables:
                        full_text += "\n=== Tables on Page " + str(page_num) + " ===\n"
                        for i, table in enumerate(tables, 1):
                            full_text += f"Table {i}:\n{table}\n\n"
                except Exception as e:
                    print(f"Warning: Table detection error on page {page_num}: {e}")
                
                full_text += "\n"  # Add extra newline between pages
                
            return full_text.strip()  # Return the complete text
            
    except Exception as e:
        print(f"❌ Error processing {pdf_path}: {e}")
        return ""

def refine_extracted_text(text):
    """Refine extracted text by removing unnecessary content."""
    # Remove excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove common header/footer patterns
    text = re.sub(r'Page \d+ of \d+', '', text)
    
    # Clean up whitespace
    text = re.sub(r' {2,}', ' ', text)
    
    return text.strip()

def generate_json_with_gemini(text, pdf_filename):
    """Generate JSON from extracted text using Gemini API."""
    prompt = f"""You are an expert in extracting structured data from exam question papers. Given the raw text extracted from a PDF exam paper, extract the following information for each question:
"question": The full question text. Include all parts of the question and any related content.
"marks": The number of marks allocated to the question as an integer. Use null if not mentioned.
"year": The year the exam was conducted as an integer. Use null if not mentioned.
"unit": The unit the question belongs to (e.g., "Unit 1"). Use null if it cannot be determined.
"subject": The name of the subject of the exam. Use null if not available.

If the question includes a table, extract the table contents as part of the question field. Ensure the table is represented clearly with proper formatting—either markdown-style or CSV-style—with all columns and rows preserved.
For extracting questions,do not extract question numbes or subquestion numbers only the question text.
If you identify any tacle data awhich is given in text make sure you add the proper table syntax to it.

Return the output as a JSON array. Each question must be a single JSON object formatted like this:
[
  {{
    "question": "What is data mining?",
    "marks": 6,
    "year": 2021,
    "unit": "Unit 1",
    "subject": "Data Mining"
  }},
  {{
    "question": "Describe the process of data cleaning.",
    "marks": 4,
    "year": 2022,
    "unit": "Unit 2",
    "subject": "Data Mining"
  }}
]
Here is an example of a question object:
{{
  "question": "Explain the concept of 'cognitive dissonance'. Provide at least three examples to illustrate your explanation.",
  "marks": 15,
  "year": 2023,
  "unit": "Unit 1",
  "subject": "Data Mining"
}}
Use the following extracted text:
{text}

Important:
All fields must appear in every object.
marks and year must be integers or null.
Only return valid JSON. Do not include any additional text, comments, or explanation outside the JSON.
    """
    try:
        # Initialize the model inside the function
        model = genai.GenerativeModel("gemini-1.5-flash")  # Updated to use correct model name
        response = model.generate_content(prompt)

        # Ensure the response is valid
        if not response or not response.text.strip():
            raise ValueError("Empty or invalid response from Gemini API.")

        # Attempt to parse the response as JSON
        try:
            json_data = json.loads(response.text.strip())
        except json.JSONDecodeError as e:
            print(f"Gemini returned invalid JSON, attempting to fix. Error: {e}")
            # Attempt to fix the JSON by extracting the valid JSON part
            start_index = response.text.find('[')
            end_index = response.text.rfind(']')
            if start_index != -1 and end_index != -1:
                try:
                    json_data = json.loads(response.text[start_index:end_index+1])
                except json.JSONDecodeError:
                    raise ValueError("The response from Gemini API is not valid JSON even after attempting to fix.")
            else:
                raise ValueError("The response from Gemini API does not contain valid JSON array.")

        # Save the JSON data to a file
        output_path = os.path.join("json_data", f"{os.path.splitext(os.path.basename(pdf_filename))[0]}_questions.json")
        os.makedirs("json_data", exist_ok=True)  # Ensure the output directory exists
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        print(f"✅ JSON saved to {output_path}")
        return True
    except ValueError as e:
        print(f"❌ Error generating JSON for {pdf_filename}: {e}")
    except Exception as e:
        print(f"❌ Unexpected error generating JSON for {pdf_filename}: {e}")
    return False

def convert_pdf_to_json(pdf_path):
    """Convert a PDF to JSON by extracting and processing text."""
    print(f"📄 Processing {pdf_path}...")
    
    # Extract text from PDF
    extracted_text = extract_text_from_pdf(pdf_path)
    
    if not extracted_text:
        print(f"❌ No text extracted from {pdf_path}")
        return False
    
    # Refine the extracted text
    refined_text = refine_extracted_text(extracted_text)
    
    # Generate JSON using Gemini API
    success = generate_json_with_gemini(refined_text, pdf_path)
    
    return success

def process_pdfs_in_folder():
    """Process all PDFs in the 'pdf' folder."""
    pdf_folder = "pdf"
    if not os.path.exists(pdf_folder):
        print(f"❌ The folder '{pdf_folder}' does not exist.")
        print(f"Creating '{pdf_folder}' folder...")
        os.makedirs(pdf_folder)
        print(f"✅ Please place your PDF files in the '{pdf_folder}' folder and run the script again.")
        return
    
    # Check if there are any PDF files in the folder
    pdf_files = [f for f in os.listdir(pdf_folder) if f.lower().endswith('.pdf')]
    if not pdf_files:
        print(f"❌ No PDF files found in '{pdf_folder}' folder.")
        return
    
    print(f"🔍 Found {len(pdf_files)} PDF files to process.")
    
    # Process each PDF file
    successful = 0
    for filename in pdf_files:
        pdf_path = os.path.join(pdf_folder, filename)
        if convert_pdf_to_json(pdf_path):
            successful += 1
    
    print(f"✅ Processing complete. Successfully processed {successful} out of {len(pdf_files)} PDF files.")

def main():
    """Main function to configure API and process PDFs."""
    try:
        print("🚀 Starting PDF to JSON conversion process...")
        configure_gemini_api()
        process_pdfs_in_folder()
        print("✅ Process completed.")
    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    main()