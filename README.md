# Political Survey Google Forms Automation Agent

A Python automation agent that generates dynamic Google Forms for political survey data collection in Assam Assembly Constituencies. The agent extracts survey options from Excel sheets and creates AC-specific questionnaires with conditional logic.

## Overview

This automation agent creates comprehensive Google Forms for political surveys with:
- Bilingual support (English and Bengali)
- Dynamic AC-specific sections based on Excel data
- Conditional logic for different constituencies
- Automated data extraction and validation
- Complete form generation with proper structure

## Project Structure

```
political-survey-agent/
├── main.py                       # Entry point and orchestration
├── excel_processor.py            # Excel data extraction logic
├── form_generator.py             # Google Forms API interactions
├── data_validator.py             # Data validation and error handling
├── config_loader.py              # Configuration file handling
├── survey_data.xlsx              # Source Excel file with all sheets
├── credentials.json              # Google OAuth credentials (you need to add this)
├── settings.yaml                 # App configuration
├── questions.json                # Bilingual question text
├── requirements.txt              # Python dependencies
├── .env                         # Environment variables
└── README.md                    # This file
```

## Installation

1. **Clone or download the project files**

2. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up Google Forms API credentials:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable Google Forms API and Google Drive API
   - Create OAuth 2.0 credentials (Desktop application)
   - Download the credentials JSON file
   - Rename it to `credentials.json` and place in project root

4. **Prepare your Excel data file:**
   - Create `survey_data.xlsx` with required sheets:
     - `AC<>PC` - AC and party data
     - `GE2024` - MP candidates data
     - `MLA_P2` - MLA candidates data
     - `Caste_Data` - Caste information

## Excel Data Structure Requirements

### AC<>PC Sheet
- **Column C**: AC numbers
- **Columns H-T**: Party options for each AC

### GE2024 Sheet
- **Column B**: AC numbers
- **Column E**: MP candidate names

### MLA_P2 Sheet
- **Column B**: AC numbers
- **Column D**: MLA candidate names
- **Column E**: Party affiliation (use 'INC' for Congress)

### Caste_Data Sheet
- **Column A**: AC numbers
- **Column B**: Caste names

## Usage

### Basic Usage

1. **Ensure all required files are present:**
   - `survey_data.xlsx` with proper data structure
   - `credentials.json` with Google API credentials

2. **Run the agent:**
```bash
python main.py
```

3. **Follow OAuth authentication flow** (browser window will open)

4. **Check outputs:**
   - Form will be created in your Google Drive
   - `form_metadata.json` contains form details
   - `political_survey_agent.log` contains execution logs

### Create Sample Data

To create a sample Excel file structure for testing:

```bash
python main.py --create-sample
```

This creates `sample_survey_data.xlsx` which you can rename to `survey_data.xlsx` and modify with your actual data.

## Form Structure

The generated form includes:

### 1. Introduction Section
- Bilingual welcome message
- Survey purpose explanation
- Confidentiality notice

### 2. Basic Information Section
- Agent ID (text input)
- Mobile Number (text input with validation)
- Gender (radio buttons: Male, Female, Other)
- AC Selection (dropdown with all available ACs)

### 3. AC-Specific Sections
Each AC gets exactly 6 questions:

1. **Voting Intention**: Future Assembly election preference
2. **2021 Voting History**: Last Assembly election choice
3. **2024 Voting History**: Last Lok Sabha election choice (MP candidates)
4. **MLA Preference**: Most suitable MLA candidate
5. **Congress Preference**: Most suitable Congress candidate
6. **Social Category**: Caste/social class

### 4. Final Common Section
- Family income (multiple choice)
- Interview language (multiple choice)

## Configuration

### Environment Variables (.env)
```
GOOGLE_CREDENTIALS_FILE=credentials.json
EXCEL_FILE_PATH=survey_data.xlsx
CALLER_NAME=Political Survey Team
```

### Settings (settings.yaml)
- Excel file and sheet configurations
- Google Forms API settings
- Retry and error handling parameters

### Questions (questions.json)
- All bilingual question text
- Option lists for common questions
- Form section descriptions

## Data Validation

The agent performs comprehensive validation:

- **AC Number Validation**: Ensures all AC numbers are valid integers
- **Data Availability**: Checks each AC has data in all required sheets
- **Option Validation**: Removes empty/invalid options
- **Structure Validation**: Verifies form structure before generation
- **Error Handling**: Graceful handling of missing data with fallback options

## Logging and Monitoring

### Log Levels
- **INFO**: General progress and status updates
- **WARNING**: Data availability issues, missing options
- **ERROR**: Critical failures, API errors

### Output Files
- **political_survey_agent.log**: Detailed execution log
- **form_metadata.json**: Complete form generation metadata

### Monitoring Features
- Data extraction summaries for each AC
- Validation warnings and error counts
- Form generation progress tracking
- API retry and error recovery

## Error Handling

### Common Issues and Solutions

1. **"File not found" errors:**
   - Ensure `survey_data.xlsx` and `credentials.json` exist
   - Check file paths in configuration

2. **Google API authentication issues:**
   - Verify credentials.json is valid
   - Ensure Google Forms API is enabled
   - Check OAuth consent screen configuration

3. **"No data found for AC" warnings:**
   - Verify AC numbers exist in all required sheets
   - Check column mappings in settings.yaml
   - Ensure data format matches expectations

4. **Form generation failures:**
   - Check Google API quotas and limits
   - Verify network connectivity
   - Review error logs for specific issues

### Retry Logic
- Automatic retry for Google API failures (3 attempts)
- Exponential backoff for rate limiting
- Graceful degradation with fallback options

## Customization

### Adding New Questions
1. Update `questions.json` with new question text
2. Modify form generation logic in `form_generator.py`
3. Update validation rules if needed

### Changing Data Sources
1. Update Excel column mappings in `settings.yaml`
2. Modify extraction logic in `excel_processor.py`
3. Update validation rules in `data_validator.py`

### Modifying Form Structure
1. Update section creation in `form_generator.py`
2. Modify conditional logic as needed
3. Update validation rules for new structure

## API Limits and Quotas

Google Forms API has the following limits:
- 300 requests per minute per project
- 30,000 requests per day per project
- Form item limits apply

The agent includes retry logic and rate limiting to handle these constraints.

## Security Considerations

- **Credentials**: Never commit `credentials.json` to version control
- **Data Privacy**: Ensure Excel data doesn't contain sensitive information
- **Access Control**: Review form sharing settings after generation
- **Logging**: Log files may contain survey data - handle appropriately

## Troubleshooting

### Enable Debug Logging
Modify logging level in `main.py`:
```python
logger = setup_logging("DEBUG")
```

### Test Individual Components
```python
# Test Excel processing only
from excel_processor import ExcelProcessor
from config_loader import load_config

config = load_config()
processor = ExcelProcessor(config)
ac_numbers = processor.get_all_ac_numbers()
print(f"Found AC numbers: {ac_numbers}")
```

### Validate Configuration
```python
from config_loader import load_config

try:
    config = load_config()
    errors = config.validate_configuration()
    if errors:
        print("Configuration errors:", errors)
    else:
        print("Configuration is valid")
except Exception as e:
    print(f"Configuration error: {e}")
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review log files for error details
3. Ensure all prerequisites are met
4. Create an issue with detailed error information

## Version History

- **v1.0.0**: Initial release with core functionality
  - Excel data extraction
  - Google Forms generation
  - Bilingual support
  - AC-specific conditional logic
  - Comprehensive validation and error handling
