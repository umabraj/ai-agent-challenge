# Bank PDF Parser Project

This project demonstrates an automated agent that generates a parser to extract data from bank statement PDFs and save as a CSV.

The Bank Statement Parser Agent is a Python-based tool designed to parse bank statements in PDF or CSV format into structured pandas DataFrames. The project provides automated validation against reference CSV files and generates custom parsers for different banks. It ensures accurate extraction, normalization, and verification of transaction data.
The agent can optionally leverage the Groq API for advanced parsing if an API key is provided. Otherwise, it uses a default parser template to process statements.

Key Features

Parses bank statements from PDF or CSV files into pandas DataFrames.

Normalizes numeric columns (Debit Amt, Credit Amt, Balance) and cleans string columns (Date, Description).

Validates parsed data against reference CSV files to ensure accuracy.

Generates custom parsers for different banks automatically.

Supports optional integration with Groq API for intelligent parsing


Parse Data

Reads the PDF or CSV file.

Extracts and organizes data into a pandas DataFrame.

Cleans and normalizes numeric and string columns.

Handles missing or empty values.

Validate Parsed Data

Compares parsed DataFrame with the reference CSV (if available).

Reports column mismatches for correction.

Display Output

Prints parsed DataFrame in the console.

Indicates matching and mismatched columns.

Confirms parser test success if all validations pass.

## Run
```bash
python agent.py --target icici
```

## Test
```bash
python -m pytest test_parser.py
```

## Install Requirements
```bash
pip install -r requirements.txt
```
Groq API Key
   
   If you want the parser agent to use the LLM-based parser generation, open agent.py and replace the placeholder API key:

   ```python
   GROQ_API_KEY = "your_groq_api_key_here"
