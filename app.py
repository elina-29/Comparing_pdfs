import os
from flask import Flask, render_template, request
from PyPDF2 import PdfReader
import pandas as pd
from bs4 import BeautifulSoup
import io

app = Flask(__name__)

# Function to extract text from a PDF file
def extract_text_from_pdf(pdf_file):
    text = ""
    pdf_reader = PdfReader(io.BytesIO(pdf_file.read()))
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# Function to extract text from a CSV file
def extract_text_from_csv(csv_file):
    df = pd.read_csv(io.StringIO(csv_file.read().decode('utf-8')))
    return df.to_string(index=False)

# Function to extract text from an HTML file
def extract_text_from_html(html_file):
    html_content = html_file.read()
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find the table containing error information
    error_table = soup.find('table', class_='table table-striped text-center')
    
    # Initialize lists to store severity and error messages
    severities = []
    error_messages = []

    # Find all rows in the table body
    rows = error_table.find('tbody').find_all('tr')
    
    # Loop through rows to extract severity and error messages
    for row in rows:
        # Extract severity
        severity_td = row.find('td', class_=True)
        if severity_td:
            severity = severity_td['class'][0].replace('bg-severity-', '')
            severities.append(severity)

        # Extract error message
        error_message_td = row.find_all('td')[1]
        if error_message_td:
            error_message = error_message_td.get_text(strip=True)
            error_messages.append(error_message)
    
    # Combine severities and error messages into a single string
    result = '\n'.join([f"{severities[i]}: {error_messages[i]}" for i in range(len(severities))])

    return result

# Rest of the code remains the same...




# Rest of the code remains the same...


# Function to compare two sets of text and find new and resolved errors
def compare_text(previous_text, current_text):
    previous_errors = set(previous_text.split('\n'))
    current_errors = set(current_text.split('\n'))

    new_errors = current_errors - previous_errors
    resolved_errors = previous_errors - current_errors

    return new_errors, resolved_errors

# Function to filter errors by severity
def filter_errors_by_severity(errors, severities):
    filtered_errors = [error for error in errors if any(error.lower().startswith(severity) for severity in severities)]
    return filtered_errors

@app.route('/', methods=['GET', 'POST'])
def index():
    new_errors = []
    resolved_errors = []
    info_lines = []  # Store lines starting with "info"

    if request.method == 'POST':
        # Handle file uploads
        previous_file = request.files['previous_file']
        current_file = request.files['current_file']

        # Ensure files were uploaded
        if previous_file and current_file:
            previous_filename = previous_file.filename
            current_filename = current_file.filename

            # Determine the file format and extract text/data accordingly
            if previous_filename.endswith('.pdf') and current_filename.endswith('.pdf'):
                previous_text = extract_text_from_pdf(previous_file)
                current_text = extract_text_from_pdf(current_file)
            elif previous_filename.endswith('.csv') and current_filename.endswith('.csv'):
                previous_text = extract_text_from_csv(previous_file)
                current_text = extract_text_from_csv(current_file)
            elif previous_filename.endswith('.html') and current_filename.endswith('.html'):
                previous_text = extract_text_from_html(previous_file)
                current_text = extract_text_from_html(current_file)
            else:
                return "Unsupported file formats. Please upload PDF, CSV, or HTML files."

            # Compare text and find new and resolved errors
            new_errors, resolved_errors = compare_text(previous_text, current_text)

            # Extract lines starting with "info" and store them separately
            info_lines = [line.strip() for line in current_text.split('\n') if line.lower().startswith('info')]

    # Define the severities to filter for
    severities_to_print = ['low', 'medium', 'critical', 'high']

    # Filter errors by severity
    new_errors = filter_errors_by_severity(new_errors, severities_to_print)
    resolved_errors = filter_errors_by_severity(resolved_errors, severities_to_print)

    # Calculate the counts of new and resolved errors
    new_errors_count = len(new_errors)
    resolved_errors_count = len(resolved_errors)

    return render_template('index.html', new_errors=new_errors, resolved_errors=resolved_errors, info_lines=info_lines, new_errors_count=new_errors_count, resolved_errors_count=resolved_errors_count)



if __name__ == '__main__':
    app.run(debug=True)
