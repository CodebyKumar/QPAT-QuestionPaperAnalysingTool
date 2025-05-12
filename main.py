import streamlit as st
import os
import shutil
import tempfile
import base64
from io import BytesIO
from dotenv import load_dotenv
import markdown
import json

# Import functions from existing files
from src.pdf_to_json import configure_gemini_api, convert_pdf_to_json
from src.json_to_markdown import collect_all_questions, ask_gemini_to_format, save_markdown
from src.markdown_to_pdf import markdown_to_pdf
# Add import for most likely questions generator
from src.most_likely_questions import generate_most_likely_questions

def get_binary_file_downloader_html(bin_file, file_label='File'):
    """Generate a download link for a binary file."""
    with open(bin_file, 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{os.path.basename(bin_file)}">{file_label}</a>'

# App title and configuration
st.set_page_config(
    page_title="Question Paper Analysing Tool (QPAT-01)",
    page_icon="📚",
    layout="wide"
)

# App title and description
st.title("📚 Question Paper Analysing Tool (QPAT-01)")
st.write("Analyze past papers, spot repeated questions, and focus on high-weight topics.")

# Initialize session state if not already done
if 'api_configured' not in st.session_state:
    st.session_state.api_configured = False
if 'json_data' not in st.session_state:
    st.session_state.json_data = []
if 'markdown_content' not in st.session_state:
    st.session_state.markdown_content = ""
if 'optimized_markdown' not in st.session_state:
    st.session_state.optimized_markdown = ""
if 'pdf_path' not in st.session_state:
    st.session_state.pdf_path = ""

# Sidebar for Google API key
st.sidebar.title("Configuration")
api_key = st.sidebar.text_input("Enter your Google API Key", type="password")

# Configure API if key provided
if api_key:
    try:
        # Create .env file and configure API
        with open(".env", "w") as env_file:
            env_file.write(f'GOOGLE_API_KEY="{api_key}"\n')
        load_dotenv()
        
        # Configure the API
        configure_gemini_api()
        
        st.session_state.api_configured = True
        st.sidebar.success("✅ API Key configured successfully!")
    except Exception as e:
        st.sidebar.error(f"❌ Error configuring API: {e}")
        st.session_state.api_configured = False
else:
    st.sidebar.warning("⚠️ Please provide a valid Google API Key.")

# Create necessary directories
for folder in ["pdf", "json_data", "md", "output"]:
    os.makedirs(folder, exist_ok=True)

# File uploader
st.subheader("Upload your previous year question papers")
uploaded_files = st.file_uploader("Choose PDF files", type="pdf", accept_multiple_files=True, key="uploaded_files")

# Process button
if uploaded_files and st.button("Process Files"):
    if not st.session_state.api_configured:
        st.error("❌ Please configure the Google API Key first!")
    else:
        # Create progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Clean directories
        for folder in ["pdf", "json_data"]:
            for file in os.listdir(folder):
                file_path = os.path.join(folder, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
        
        # Save uploaded files
        status_text.text("Saving uploaded files...")
        for i, uploaded_file in enumerate(uploaded_files):
            # Save file with original name
            pdf_path = os.path.join("pdf", uploaded_file.name)
            with open(pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            progress_bar.progress((i + 1) / (len(uploaded_files) * 3))
        
        # Process PDFs to JSON
        status_text.text("Converting PDFs to JSON...")
        successful_files = 0
        for i, uploaded_file in enumerate(uploaded_files):
            pdf_path = os.path.join("pdf", uploaded_file.name)
            if convert_pdf_to_json(pdf_path):
                successful_files += 1
            progress_bar.progress((len(uploaded_files) + i + 1) / (len(uploaded_files) * 3))
        
        # Collect all questions from JSON files
        all_questions = collect_all_questions("json_data")
        st.session_state.json_data = all_questions
        
        # Convert to markdown
        status_text.text("Creating markdown content...")
        if all_questions:
            # Save combined questions to a single JSON file
            with open("json_data/all_questions.json", "w", encoding="utf-8") as f:
                json.dump(all_questions, f, indent=2, ensure_ascii=False)
            
            # Generate markdown from combined questions using Gemini
            optimized_markdown = ask_gemini_to_format(all_questions)
            
            if optimized_markdown:
                st.session_state.optimized_markdown = optimized_markdown
                
                # Save the markdown content to file before converting to PDF
                save_markdown(optimized_markdown, "md/optimized_questions.md")
                
                # Generate most likely questions
                status_text.text("Generating most likely questions...")
                try:
                    generate_most_likely_questions(all_questions, "md/predicted_questions.md")
                except Exception as e:
                    st.error(f"Error generating most likely questions: {str(e)}")
                
                # Create PDF using the saved markdown file
                status_text.text("Converting markdown to PDF...")
                
                # Generate PDF
                markdown_to_pdf(INPUT_FILE = "md/optimized_questions.md", OUTPUT_FILE = "output/output.pdf")
                
                # Set the PDF path in session state
                st.session_state.pdf_path = "output/output.pdf"
                
                progress_bar.progress(1.0)
                status_text.text(f"✅ Processing complete! Successfully processed {successful_files} out of {len(uploaded_files)} PDF files.")
            else:
                status_text.error("❌ Error generating markdown.")
        else:
            status_text.error("❌ No questions could be extracted from the PDFs.")

# Display results if available
if st.session_state.optimized_markdown:
    st.subheader("Question Bank")
    
    # Modified tabs structure as requested
    tabs = st.tabs(["Question Bank", "Most Likely Question", "Download Options"])
    
    with tabs[0]:
        # Content from previous "Markdown View" tab
        st.markdown(st.session_state.optimized_markdown)
    
    with tabs[1]:
        # Content for Most Likely Questions tab
        try:
            if os.path.exists("md/predicted_questions.md"):
                with open("md/predicted_questions.md", "r") as f:
                    predicted_questions_content = f.read()
                st.markdown(predicted_questions_content)
            else:
                st.info("Most likely questions have not been generated yet. Please process your question papers first.")
        except Exception as e:
            st.error(f"Error loading most likely questions: {e}")
    
    with tabs[2]:
        # Combined download options from both previous tabs
        st.subheader("Question Bank Downloads")
        col1, col2 = st.columns(2)
        
        # Download original markdown
        with col1:
            st.download_button(
                label="Download Question Bank Markdown",
                data=st.session_state.optimized_markdown,
                file_name="question_bank.md",
                mime="text/markdown"
            )
        
        # Download PDF
        with col2:
            # Add generate PDF button first
            if st.button("Generate Question Bank PDF"):
                try:
                    with st.spinner("Generating PDF..."):
                        pdf_path = markdown_to_pdf(
                            INPUT_FILE="md/optimized_questions.md", 
                            OUTPUT_FILE="output/output.pdf"
                        )
                        st.session_state.pdf_path = "output/output.pdf"
                        st.session_state.pdf_generated = True
                        
                        # Show download button only after successful generation
                        if os.path.exists(pdf_path):
                            with open(pdf_path, "rb") as pdf_file:
                                pdf_data = pdf_file.read()
                                pdf_download = st.download_button(
                                    label="Download Question Bank PDF",
                                    data=pdf_data,
                                    file_name="question_bank.pdf",
                                    mime="application/pdf"
                                )
                        else:
                            st.error("Failed to generate PDF file")
                except Exception as e:
                    st.error(f"Error generating PDF: {e}")
        
        # Add a separator
        st.markdown("---")
        
        # Most Likely Questions download options
        st.subheader("Most Likely Questions Downloads")
        col3, col4 = st.columns(2)

        with col3:
            # Download as Markdown
            try:
                with open("md/predicted_questions.md", "r") as f:
                    predicted_questions_md = f.read()
                st.download_button(
                    label="Download Most Likely Questions Markdown",
                    data=predicted_questions_md,
                    file_name="most_likely_questions.md",
                    mime="text/markdown"
                )
            except Exception as e:
                st.error(f"Error preparing markdown download: {e}")

        with col4:
            # Download as PDF
            if st.button("Generate Most Likely Questions PDF"):
                try:
                    with st.spinner("Generating PDF..."):
                        pdf_path = markdown_to_pdf(
                            INPUT_FILE="md/predicted_questions.md", 
                            OUTPUT_FILE="output/most_likely_questions.pdf"
                        )
                        
                        if pdf_path and os.path.exists(pdf_path):
                            with open(pdf_path, "rb") as f:
                                pdf_data = f.read()
                            st.download_button(
                                label="Download Most Likely Questions PDF",
                                data=pdf_data,
                                file_name="most_likely_questions.pdf",
                                mime="application/pdf"
                            )
                        else:
                            st.error("Failed to generate PDF")
                except Exception as e:
                    st.error(f"Error generating PDF: {e}")
        
        # Option to view raw JSON data
        st.markdown("---")
        with st.expander("View Raw JSON Data"):
            if st.session_state.json_data:
                st.json(st.session_state.json_data)
            else:
                st.info("No JSON data available.")

# Add footer
st.markdown("---")
st.markdown("**Question Paper Analysing Tool (QPAT-01)** | **Save Your Time**")