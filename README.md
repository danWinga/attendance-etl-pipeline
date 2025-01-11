# Attendance ETL Pipeline

This project implements an ETL (Extract, Transform, Load) pipeline for processing attendance data. The pipeline extracts raw data, transforms it to calculate work hours and overtime, and summarizes the results with additional calculations for overtime rates.

## Features
- **Data Extraction**: Reads raw attendance data from a CSV file.
- **Data Transformation**:
  - Filters and cleans attendance data.
  - Calculates work hours (`WorkHrs`) and overtime (`Overtime`).
  - Adjusts time formats and resolves invalid entries.
- **Summary Generation**:
  - Aggregates data by employee name.
  - Calculates `TotalWorkHrs` and `TotalOvertime`.
  - Computes `OvertimeAmnt` based on predefined rates.
- **Data Loading**: Saves the processed data and summary to an Excel file.

## Repository Structure
- **`data/`**: Contains input and output files.
- **`src/`**: Contains Python scripts for each stage of the pipeline.
- **`tests/`**: Contains unit tests for transformation and summary logic.
- **`README.md`**: Provides an overview and usage guide.
- **`requirements.txt`**: Lists Python dependencies.

## Prerequisites
- Python 3.8 or higher
- Pandas library
- XlsxWriter for Excel output

Install the required dependencies using:
```bash
pip install -r requirements.txt
