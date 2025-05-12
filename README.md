# Question Paper Analyzing Tool (QPAT-01)

## Overview

QPAT-01 is an AI-powered tool designed to analyze past question papers, identify recurring patterns, and generate insightful question banks. It helps students and educators focus on high-priority topics, predict potential exam questions, and save valuable preparation time.

## Key Capabilities

*   **Automated PDF Extraction**: Automatically extracts questions from PDF files.
*   **Intelligent Question Analysis**: Uses AI to understand question context and categorize them.
*   **Pattern Identification**: Identifies frequently repeated questions across multiple years.
*   **Question Bank Generation**: Creates organized question banks, categorized by subject, unit, and year.
*   **Likely Question Prediction**: Predicts potential questions for future exams based on historical data.
*   **Flexible Export Options**: Supports downloads in both Markdown and PDF formats.
*   **User-Friendly Interface**: Provides an intuitive web interface via Streamlit.

## Getting Started

### Prerequisites

*   Python 3.7+
*   A valid Google API key (required for AI functionalities)
*   Internet connectivity (for accessing Google AI services)

### Installation

1.  Clone the repository:

    ```bash
    git clone <repository-url>
    cd EH_01
    ```

2.  Install the required Python packages:

    ```bash
    pip install -r requirements.txt
    ```

### Configuration

1.  **API Key**: Obtain a Google API key and enter it in the application's sidebar. The application will automatically save it to `.env` file.

### Usage

1.  Run the Streamlit application:

    ```bash
    streamlit run main.py
    ```

2.  Open the URL displayed in the terminal in your web browser (usually `http://localhost:8501`).

3.  Upload your PDF question papers using the file uploader.

4.  Click the "Process Files" button.

5.  Explore the generated question bank, predicted questions, and download options in the provided tabs.

## Project Structure

```text
/Users/kumarswamikallimath/Desktop/QPAT/
├── .streamlit/             # Streamlit configuration files
├── data/                  # Data storage (JSON, Markdown, PDFs)
│   ├── json_data/
│   ├── md/
│   └── output/
├── pdf/                   # Directory for uploaded PDF files
├── src/                   # Python source code
│   ├── json_to_markdown.py
│   ├── markdown_to_pdf.py
│   ├── most_likely_questions.py
│   └── pdf_to_json.py
├── .env                    # Stores the Google API key
├── .gitignore              # Specifies intentionally untracked files that Git should ignore
└── main.py                 # Streamlit application entry point
```

## Contributing

Feel free to contribute to the project by submitting pull requests, reporting issues, or suggesting new features.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


