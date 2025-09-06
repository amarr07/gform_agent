# Political Survey Google Forms Automation Agent - Instructions

## Overview
Create a Python automation agent that generates dynamic Google Forms for political survey data collection. The agent extracts survey options from Excel sheets and creates AC-specific questionnaires with conditional logic.

## Core Data Flow

### Excel Data Structure Requirements
- **AC<>PC Sheet**: Column C contains AC numbers, Columns H-T contain party options
- **GE2024 Sheet**: Column B contains AC numbers, Column E contains candidate names  
- **MLA_P2 Sheet**: Column B contains AC numbers, Column D contains candidate names, Column E contains party affiliation
- **Caste_Data Sheet**: Column A contains AC numbers, Column B contains caste names

### Data Extraction Logic
**CRITICAL**: Always match AC numbers exactly between user input and Excel data. No partial matches or fuzzy matching allowed.

For each question type, extract options as follows:
1. **Party Questions (Q1, Q2)**: Match user AC number with Column C in AC<>PC sheet, return all non-empty values from columns H-T of that row
2. **MP Candidates (Q3)**: Match user AC number with Column B in GE2024 sheet, return all values from Column E for matching rows
3. **MLA Candidates (Q4)**: Match user AC number with Column B in MLA_P2 sheet, return all values from Column D for matching rows
4. **Congress Candidates (Q5)**: Match user AC number with Column B in MLA_P2 sheet, return values from Column D where Column E equals 'INC'
5. **Caste Options (Q6)**: Match user AC number with Column A in Caste_Data sheet, return all values from Column B for matching rows

## Form Structure Requirements

### Section 1: Introduction
- Display bilingual introduction text (English and Bengali)
- Text must include placeholder `[caller_name]` for dynamic replacement
- No user input required in this section

### Section 2: Basic Information
**All fields mandatory, no skipping allowed**

1. **Agent ID**: Text input field, required
2. **Mobile Number**: Text input field, required, validate 10-digit format
3. **Gender**: Dropdown with options [Male, Female, Other], required
4. **AC Selection**: Dropdown populated with all unique AC numbers from Excel data, required

**CRITICAL**: AC selection dropdown must trigger conditional navigation to corresponding AC-specific section

### Section 3: AC-Specific Sections
**Create one section per unique AC number found in Excel data**

Each AC section contains exactly 6 questions in this order:

#### Question 1: Voting Intention
- **English**: "If the Assembly elections were held in Assam tomorrow, which party would you vote for?"
- **Bengali**: "যদি আগামীকাল অসমে বিধানসভা নির্বাচন হয়, তবে আপনি কোন দলকে ভোট দেবেন?"
- **Options**: Extract from AC<>PC sheet (columns H-T) for matching AC number
- **Type**: Multiple choice, single selection, required

#### Question 2: 2021 Voting History
- **English**: "In the last Assembly (MLA) elections held in 2021, which party did you vote for?"
- **Bengali**: "২০২১ সালে অনুষ্ঠিত শেষ বিধানসভা (এমএলএ) নির্বাচনে আপনি কোন দলকে ভোট দিয়েছিলেন?"
- **Options**: Extract from AC<>PC sheet (columns H-T) for matching AC number
- **Type**: Multiple choice, single selection, required

#### Question 3: 2024 Voting History  
- **English**: "In the last Lok Sabha (MP) elections held in 2024, which party did you vote for?"
- **Bengali**: "২০২৪ সালে অনুষ্ঠিত শেষ লোকসভা (এমপি) নির্বাচনে আপনি কোন দলকে ভোট দিয়েছিলেন?"
- **Options**: Extract candidate names from GE2024 sheet (column E) where column B matches AC number
- **Type**: Multiple choice, single selection, required

#### Question 4: MLA Preference
- **English**: "From your Assembly constituency, which MLA candidate do you consider the most suitable?"
- **Bengali**: "আপনার বিধানসভা কেন্দ্র থেকে কোন বিধায়ক প্রার্থীকে আপনি সবচেয়ে উপযুক্ত মনে করেন?"
- **Options**: Extract names from MLA_P2 sheet (column D) where column B matches AC number
- **Type**: Multiple choice, single selection, required

#### Question 5: Congress Preference
- **English**: "From your Assembly constituency, which Congress party candidate do you consider the most suitable?"
- **Bengali**: "আপনার বিধানসভা কেন্দ্র থেকে কংগ্রেস দলের কোন প্রার্থীকে আপনি সবচেয়ে উপযুক্ত মনে করেন?"
- **Options**: Extract names from MLA_P2 sheet (column D) where column B matches AC number AND column E equals 'INC'
- **Type**: Multiple choice, single selection, required

#### Question 6: Social Category
- **English**: "Which social category/class do you belong to?"
- **Bengali**: "আপনি কোন সামাজিক শ্রেণী/বর্গের অন্তর্ভুক্ত?"
- **Options**: Extract caste names from Caste_Data sheet (column B) where column A matches AC number
- **Type**: Multiple choice, single selection, required

### Section 4: Common Final Questions
**All AC sections must route to this final section**

#### Question 7: Family Income
- **English**: "What is the average monthly income of your family?"
- **Bengali**: "আপনার পরিবারের গড় মাসিক আয় কত?"
- **Options**: [Less than 5000, 5000-7500, 7500-10000, 10000-12500, 12500-15000, 15000-20000, More than 20000, Can't say, Call disconnected]
- **Type**: Multiple choice, single selection, required

#### Question 8: Interview Language
- **English**: "Please select the Language in which the conversation was done."
- **Bengali**: "অনুগ্রহ করে যে ভাষায় কথোপকথনটি করা হয়েছে তা নির্বাচন করুন।"
- **Options**: [Assamese, Bengali, Hindi, Bodo, Other language]
- **Type**: Multiple choice, single selection, required

## Technical Implementation Rules

### Data Processing Rules
1. **Always validate AC numbers exist in ALL required sheets before creating sections**
2. **Skip empty cells when extracting options, never include blank options**
3. **Preserve exact text from Excel cells, no modifications or cleaning**
4. **Handle missing data gracefully - if AC has no options in a sheet, show error message**
5. **Case-sensitive matching for party affiliations (exactly 'INC' for Congress)**

### Form Generation Rules
1. **Each question must be marked as required - no optional questions allowed**
2. **Use conditional logic to show only relevant AC section based on user selection**
3. **All sections except selected AC section should be hidden**
4. **Final section must be accessible from all AC sections**
5. **Form title: "Assam Political Survey - AC [AC_NUMBER]" for each AC section**

### Error Handling Requirements
1. **If AC number has no data in required sheet, add option "No candidates available"**
2. **If Excel file is missing or corrupted, log detailed error and stop execution**
3. **If Google Forms API fails, retry 3 times with exponential backoff**
4. **Log all data extraction steps for debugging purposes**

### Validation Rules
1. **Verify each AC section has exactly 6 questions before creating form**
2. **Confirm all extracted options are non-empty strings**
3. **Validate bilingual text is properly encoded and displays correctly**
4. **Test conditional logic navigation between sections**

## Output Requirements
- Generate one master form with all AC sections
- Return form URL and unique form ID
- Create mapping file of AC numbers to section IDs
- Log summary of questions and options created per AC

## Code Organization Requirements
- Separate functions for each data extraction type
- Dedicated form builder class for Google Forms API interactions
- Configuration file for bilingual question text
- Utility functions for Excel data validation and cleaning
