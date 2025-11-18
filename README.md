# Political Survey Google Forms Automation Agent

A Python automation agent that generates dynamic Google Forms for political survey data collection in Assam Assembly Constituencies. The agent extracts survey options from Excel sheets and creates AC-specific questionnaires.

## Overview

This automation agent creates comprehensive Google Forms for political surveys with:
- Bilingual support (English and Bengali)
- Dynamic AC-specific sections based on Excel data
- Automated data extraction from Excel
- Interactive command-line interface
- Complete form generation with proper structure

## Project Structure

```
gform_agent/
├── main.py                       # All-in-one consolidated script
├── assam.xlsx                    # Source Excel file with all AC data
├── credentials.json              # Google OAuth credentials (you need to add this)
├── credentials_template.json     # Template for credentials setup
├── settings.yaml                 # App configuration
├── requirements.txt              # Python dependencies
├── generated_forms.json          # Tracking of generated forms
└── README.md                     # This file
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

4. **Your Excel data file (`assam.xlsx`) should have these sheets:**
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
   - `assam.xlsx` with proper data structure
   - `credentials.json` with Google API credentials
   - `settings.yaml` with configuration

2. **Run the agent:**
```bash
python main.py
```

3. **Enter AC numbers when prompted:**
```
Enter AC numbers separated by commas (e.g., 22,23,25,26):
> 22,23,25,26
```

4. **Follow OAuth authentication flow** (browser window will open on first run)

5. **Check outputs:**
   - Form URL will be displayed in the console
   - Metadata saved to `ac_22_23_25_26_bengali_metadata.json`
   - `political_survey_agent.log` contains execution logs
   - Form link is ready to share!

## Form Structure

The generated form includes:

### 1. Introduction Section
- Bilingual welcome message (Bengali and English)
- Survey purpose explanation
- Confidentiality notice

### 2. Basic Information Section
- Agent ID (text input)
- Mobile Number (text input with validation)
- Gender (radio buttons: Male, Female)
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

All questions are displayed in bilingual format (English | Bengali).

## Configuration

### Settings (settings.yaml)
- Excel file and sheet configurations
- Google Forms API settings
- Retry and error handling parameters
- Fixed options for questions

The consolidated `main.py` script includes:
- **ConfigLoader**: Loads settings from YAML and environment
- **DataValidator**: Validates AC numbers and data integrity
- **ExcelProcessor**: Extracts data from Excel sheets
- **FormGenerator**: Creates and manages Google Forms via API

## Data Validation

The agent performs comprehensive validation:

- **AC Number Validation**: Ensures all AC numbers are valid integers
- **Data Availability**: Checks each AC has data in all required sheets
- **Option Validation**: Removes empty/invalid options
- **Error Handling**: Graceful handling of missing data with fallback options

All validation logic is built into the consolidated `main.py` script.

## Logging and Monitoring

### Log Levels
- **INFO**: General progress and status updates
- **WARNING**: Data availability issues, missing options
- **ERROR**: Critical failures, API errors

### Output Files
- **political_survey_agent.log**: Detailed execution log
- **ac_[numbers]_bengali_metadata.json**: Form generation metadata for each run
- **generated_forms.json**: Master tracking file for all generated forms

## Error Handling

### Common Issues and Solutions

1. **"File not found" errors:**
   - Ensure `assam.xlsx` and `credentials.json` exist
   - Check file paths in settings.yaml

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

## Customization

### Modifying the Script
Since all code is in a single `main.py` file, you can easily:

1. **Add new questions**: Edit the form generation section
2. **Change data sources**: Update Excel column mappings in ConfigLoader
3. **Modify validation**: Update DataValidator class
4. **Change form structure**: Edit FormGenerator methods

The consolidated structure makes it easy to understand and modify the entire workflow.

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
Modify logging level in `main.py` (line ~552):
```python
logger = setup_logging("DEBUG")
```

### Test Components
The consolidated script includes all components in one file:
- ConfigLoader (handles YAML and settings)
- ExcelProcessor (extracts data from Excel)
- FormGenerator (creates Google Forms)
- DataValidator (validates all data)

All classes are accessible within `main.py` for testing and debugging.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes to `main.py`
4. Test thoroughly with your data
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review `political_survey_agent.log` for error details
3. Ensure all prerequisites are met (credentials.json, assam.xlsx, settings.yaml)
4. Create an issue with detailed error information

## Version History

- **v2.0.0**: Consolidated single-file version
  - All code in one `main.py` file
  - Simplified structure with 7 essential files
  - Interactive command-line interface
  - Bengali language support
  - Streamlined deployment

- **v1.0.0**: Initial release
  - Excel data extraction
  - Google Forms generation
  - Bilingual support
  - AC-specific sections
  - Comprehensive validation
