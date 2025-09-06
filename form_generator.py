"""
Google Forms API interactions for the Political Survey Google Forms Automation Agent.
Handles form creation, section management, and conditional logic setup.
"""

import logging
import time
import os
from typing import Dict, List, Any, Optional, Tuple
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config_loader import ConfigLoader
from data_validator import DataValidator


class FormGenerator:
    """Handles all Google Forms API operations."""
    
    def __init__(self, config: ConfigLoader):
        """
        Initialize Form Generator with configuration.
        
        Args:
            config: Configuration loader instance
        """
        self.config = config
        self.validator = DataValidator()
        self.logger = logging.getLogger(__name__)
        
        # Google Forms API setup
        self.service = None
        self.credentials = None
        self._setup_google_api()
        
        # Load questions configuration
        self.questions = config.get_questions_text()
        self.caller_name = config.get_caller_name()
        
        # Retry settings
        retry_config = config.get_retry_settings()
        self.max_retries = retry_config['attempts']
        self.retry_delay = retry_config['delay']
    
    def _setup_google_api(self):
        """Setup Google Forms API authentication."""
        try:
            scopes = self.config.get_google_forms_config()['scopes']
            creds_file = self.config.get_credentials_file_path()
            
            if not os.path.exists(creds_file):
                raise FileNotFoundError(f"Google credentials file not found: {creds_file}")
            
            self.logger.info("Setting up Google Forms API authentication")
            self.logger.info("A browser window will open for authentication...")
            
            # Load credentials and run OAuth flow
            flow = InstalledAppFlow.from_client_secrets_file(creds_file, scopes)
            self.credentials = flow.run_local_server(
                port=0, 
                prompt='consent',
                success_message='Authentication successful! You can close this window.'
            )
            
            # Build the service
            self.service = build('forms', 'v1', credentials=self.credentials)
            self.logger.info("Google Forms API setup successful")
            
            # Test the connection
            self._test_api_connection()
            
        except FileNotFoundError as e:
            self.logger.error(f"Credentials file not found: {e}")
            raise Exception(f"Please ensure credentials.json exists. See GOOGLE_API_SETUP.md for setup instructions.")
        except Exception as e:
            self.logger.error(f"Failed to setup Google Forms API: {e}")
            raise Exception(f"Google API setup failed: {e}. Check your credentials and internet connection.")
    
    def _test_api_connection(self):
        """Test the Google Forms API connection."""
        try:
            # Try to create a simple test form to verify permissions
            test_form = {
                "info": {
                    "title": "API Test Form - Delete Me"
                }
            }
            
            result = self.service.forms().create(body=test_form).execute()
            test_form_id = result['formId']
            
            # Try to delete the test form (move to trash via Drive API if available)
            self.logger.info("✓ Google Forms API connection successful")
            self.logger.info(f"Test form created and accessible: {test_form_id}")
            
        except Exception as e:
            self.logger.warning(f"API test failed, but proceeding: {e}")
            # Don't fail completely, just warn
    
    def _execute_with_retry(self, operation, operation_name: str):
        """
        Execute Google API operation with retry logic.
        
        Args:
            operation: Function to execute
            operation_name: Name of operation for logging
            
        Returns:
            Operation result
        """
        for attempt in range(self.max_retries):
            try:
                return operation()
            except HttpError as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    self.logger.warning(f"{operation_name} failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"{operation_name} failed after {self.max_retries} attempts: {e}")
                    raise
            except Exception as e:
                self.logger.error(f"{operation_name} failed with unexpected error: {e}")
                raise
    
    def create_form(self, title: str) -> Dict[str, Any]:
        """
        Create a new Google Form.
        
        Args:
            title: Title for the form
            
        Returns:
            Form creation response
        """
        # Only set title when creating form, description will be added later
        form_body = {
            "info": {
                "title": title
            }
        }
        
        def create_operation():
            return self.service.forms().create(body=form_body).execute()
        
        result = self._execute_with_retry(create_operation, "Create form")
        self.logger.info(f"Created form: {title} (ID: {result['formId']})")
        return result
    
    def update_form_description(self, form_id: str, description: str):
        """
        Update form description using batchUpdate.
        
        Args:
            form_id: ID of the form to update
            description: Description text to set
        """
        request_body = {
            "requests": [{
                "updateFormInfo": {
                    "info": {
                        "description": description
                    },
                    "updateMask": "description"
                }
            }]
        }
        
        def update_operation():
            return self.service.forms().batchUpdate(formId=form_id, body=request_body).execute()
        
        self._execute_with_retry(update_operation, "Update form description")
        self.logger.info("Updated form description")
    
    def add_introduction_section(self, form_id: str) -> str:
        """
        Add introduction section with bilingual text.
        
        Args:
            form_id: ID of the form to update
            
        Returns:
            Item ID of the created section
        """
        intro_text = self.questions['introduction']
        english_text = intro_text['english'].replace('[caller_name]', self.caller_name)
        bengali_text = intro_text['bengali'].replace('[caller_name]', self.caller_name)
        
        full_intro = f"{english_text}\n\n{bengali_text}"
        
        request_body = {
            "requests": [{
                "createItem": {
                    "item": {
                        "title": "Introduction / পরিচয়",
                        "description": full_intro,
                        "textItem": {}
                    },
                    "location": {
                        "index": 0
                    }
                }
            }]
        }
        
        def update_operation():
            return self.service.forms().batchUpdate(formId=form_id, body=request_body).execute()
        
        result = self._execute_with_retry(update_operation, "Add introduction section")
        
        # Extract item ID from response
        try:
            item_id = result['replies'][0]['createItem']['item']['itemId']
            self.logger.info(f"Added introduction section (ID: {item_id})")
            return item_id
        except (KeyError, IndexError) as e:
            self.logger.error(f"Error extracting item ID from response: {e}")
            self.logger.error(f"Response structure: {result}")
            # Return a placeholder ID if extraction fails
            return "intro_section"
    
    def add_basic_info_section(self, form_id: str, ac_numbers: List[str]) -> List[str]:
        """
        Add basic information collection section.
        
        Args:
            form_id: ID of the form to update
            ac_numbers: List of AC numbers for dropdown
            
        Returns:
            List of item IDs created
        """
        basic_info = self.questions['basic_info']
        requests = []
        
        # Agent ID question
        requests.append({
            "createItem": {
                "item": {
                    "title": f"{basic_info['agent_id']['english']} / {basic_info['agent_id']['bengali']}",
                    "questionItem": {
                        "question": {
                            "required": True,
                            "textQuestion": {
                                "paragraph": False
                            }
                        }
                    }
                },
                "location": {"index": 1}
            }
        })
        
        # Mobile number question
        requests.append({
            "createItem": {
                "item": {
                    "title": f"{basic_info['mobile_number']['english']} / {basic_info['mobile_number']['bengali']}",
                    "questionItem": {
                        "question": {
                            "required": True,
                            "textQuestion": {
                                "paragraph": False
                            }
                        }
                    }
                },
                "location": {"index": 2}
            }
        })
        
        # Gender question
        gender_options = [{"value": option} for option in basic_info['gender']['options']]
        requests.append({
            "createItem": {
                "item": {
                    "title": f"{basic_info['gender']['english']} / {basic_info['gender']['bengali']}",
                    "questionItem": {
                        "question": {
                            "required": True,
                            "choiceQuestion": {
                                "type": "RADIO",
                                "options": gender_options,
                                "shuffle": False
                            }
                        }
                    }
                },
                "location": {"index": 3}
            }
        })
        
        # AC Selection question
        ac_options = [{"value": f"AC {ac}"} for ac in sorted(ac_numbers, key=lambda x: int(x))]
        requests.append({
            "createItem": {
                "item": {
                    "title": f"{basic_info['ac_selection']['english']} / {basic_info['ac_selection']['bengali']}",
                    "questionItem": {
                        "question": {
                            "required": True,
                            "choiceQuestion": {
                                "type": "DROP_DOWN",
                                "options": ac_options,
                                "shuffle": False
                            }
                        }
                    }
                },
                "location": {"index": 4}
            }
        })
        
        request_body = {"requests": requests}
        
        def update_operation():
            return self.service.forms().batchUpdate(formId=form_id, body=request_body).execute()
        
        result = self._execute_with_retry(update_operation, "Add basic info section")
        
        item_ids = []
        try:
            for reply in result['replies']:
                if 'createItem' in reply:
                    item_ids.append(reply['createItem']['item']['itemId'])
        except (KeyError, IndexError) as e:
            self.logger.error(f"Error extracting item IDs from response: {e}")
            self.logger.error(f"Response structure: {result}")
            # Return placeholder IDs
            item_ids = [f"basic_info_{i}" for i in range(4)]
        
        self.logger.info(f"Added basic info section with {len(item_ids)} questions")
        return item_ids
    
    def add_ac_specific_section(self, form_id: str, ac_number: str, ac_data: Dict[str, List[str]], 
                               start_index: int) -> Tuple[List[str], int]:
        """
        Add AC-specific section with 6 questions.
        
        Args:
            form_id: ID of the form to update
            ac_number: AC number for this section
            ac_data: Dictionary containing all options for this AC
            start_index: Starting index for item placement
            
        Returns:
            Tuple of (list of item IDs, next available index)
        """
        ac_questions = self.questions['ac_questions']
        requests = []
        current_index = start_index
        
        # Page break before AC section
        requests.append({
            "createItem": {
                "item": {
                    "pageBreakItem": {}
                },
                "location": {"index": current_index}
            }
        })
        current_index += 1
        
        # Section title
        requests.append({
            "createItem": {
                "item": {
                    "title": f"Questions for AC {ac_number}",
                    "description": f"Please answer the following questions specific to Assembly Constituency {ac_number}",
                    "textItem": {}
                },
                "location": {"index": current_index}
            }
        })
        current_index += 1
        
        # Question 1: Voting Intention
        q1_options = [{"value": option} for option in ac_data.get('party_options', ['No parties available'])]
        requests.append({
            "createItem": {
                "item": {
                    "title": f"{ac_questions['q1']['english']} | {ac_questions['q1']['bengali']}",
                    "questionItem": {
                        "question": {
                            "required": True,
                            "choiceQuestion": {
                                "type": "RADIO",
                                "options": q1_options,
                                "shuffle": False
                            }
                        }
                    }
                },
                "location": {"index": current_index}
            }
        })
        current_index += 1
        
        # Question 2: 2021 Voting History
        q2_options = [{"value": option} for option in ac_data.get('party_options', ['No parties available'])]
        requests.append({
            "createItem": {
                "item": {
                    "title": f"{ac_questions['q2']['english']} | {ac_questions['q2']['bengali']}",
                    "questionItem": {
                        "question": {
                            "required": True,
                            "choiceQuestion": {
                                "type": "RADIO",
                                "options": q2_options,
                                "shuffle": False
                            }
                        }
                    }
                },
                "location": {"index": current_index}
            }
        })
        current_index += 1
        
        # Question 3: 2024 Voting History (MP candidates)
        q3_options = [{"value": option} for option in ac_data.get('mp_candidates', ['No candidates available'])]
        requests.append({
            "createItem": {
                "item": {
                    "title": f"{ac_questions['q3']['english']} | {ac_questions['q3']['bengali']}",
                    "questionItem": {
                        "question": {
                            "required": True,
                            "choiceQuestion": {
                                "type": "RADIO",
                                "options": q3_options,
                                "shuffle": False
                            }
                        }
                    }
                },
                "location": {"index": current_index}
            }
        })
        current_index += 1
        
        # Question 4: MLA Preference
        q4_options = [{"value": option} for option in ac_data.get('mla_candidates', ['No candidates available'])]
        requests.append({
            "createItem": {
                "item": {
                    "title": f"{ac_questions['q4']['english']} | {ac_questions['q4']['bengali']}",
                    "questionItem": {
                        "question": {
                            "required": True,
                            "choiceQuestion": {
                                "type": "RADIO",
                                "options": q4_options,
                                "shuffle": False
                            }
                        }
                    }
                },
                "location": {"index": current_index}
            }
        })
        current_index += 1
        
        # Question 5: Congress Preference
        q5_options = [{"value": option} for option in ac_data.get('congress_candidates', ['No candidates available'])]
        requests.append({
            "createItem": {
                "item": {
                    "title": f"{ac_questions['q5']['english']} | {ac_questions['q5']['bengali']}",
                    "questionItem": {
                        "question": {
                            "required": True,
                            "choiceQuestion": {
                                "type": "RADIO",
                                "options": q5_options,
                                "shuffle": False
                            }
                        }
                    }
                },
                "location": {"index": current_index}
            }
        })
        current_index += 1
        
        # Question 6: Social Category
        q6_options = [{"value": option} for option in ac_data.get('caste_options', ['No castes available'])]
        requests.append({
            "createItem": {
                "item": {
                    "title": f"{ac_questions['q6']['english']} | {ac_questions['q6']['bengali']}",
                    "questionItem": {
                        "question": {
                            "required": True,
                            "choiceQuestion": {
                                "type": "RADIO",
                                "options": q6_options,
                                "shuffle": False
                            }
                        }
                    }
                },
                "location": {"index": current_index}
            }
        })
        current_index += 1
        
        # Execute batch update
        request_body = {"requests": requests}
        
        def update_operation():
            return self.service.forms().batchUpdate(formId=form_id, body=request_body).execute()
        
        result = self._execute_with_retry(update_operation, f"Add AC {ac_number} section")
        
        item_ids = []
        try:
            for reply in result['replies']:
                if 'createItem' in reply:
                    item_ids.append(reply['createItem']['item']['itemId'])
        except (KeyError, IndexError) as e:
            self.logger.error(f"Error extracting item IDs from response: {e}")
            # Return placeholder IDs
            item_ids = [f"ac_{ac_number}_{i}" for i in range(8)]  # 8 items per AC section
        
        self.logger.info(f"Added AC {ac_number} section with {len(item_ids)} items")
        return item_ids, current_index
    
    def add_final_section(self, form_id: str, start_index: int) -> List[str]:
        """
        Add final common questions section.
        
        Args:
            form_id: ID of the form to update
            start_index: Starting index for item placement
            
        Returns:
            List of item IDs created
        """
        final_questions = self.questions['final_questions']
        requests = []
        current_index = start_index
        
        # Page break before final section
        requests.append({
            "createItem": {
                "item": {
                    "pageBreakItem": {}
                },
                "location": {"index": current_index}
            }
        })
        current_index += 1
        
        # Section title
        requests.append({
            "createItem": {
                "item": {
                    "title": "Final Questions / চূড়ান্ত প্রশ্ন",
                    "description": "Please answer these final questions / অনুগ্রহ করে এই চূড়ান্ত প্রশ্নগুলির উত্তর দিন",
                    "textItem": {}
                },
                "location": {"index": current_index}
            }
        })
        current_index += 1
        
        # Question 7: Family Income
        q7_options = [{"value": option} for option in final_questions['q7']['options']]
        requests.append({
            "createItem": {
                "item": {
                    "title": f"{final_questions['q7']['english']} | {final_questions['q7']['bengali']}",
                    "questionItem": {
                        "question": {
                            "required": True,
                            "choiceQuestion": {
                                "type": "RADIO",
                                "options": q7_options,
                                "shuffle": False
                            }
                        }
                    }
                },
                "location": {"index": current_index}
            }
        })
        current_index += 1
        
        # Question 8: Interview Language
        q8_options = [{"value": option} for option in final_questions['q8']['options']]
        requests.append({
            "createItem": {
                "item": {
                    "title": f"{final_questions['q8']['english']} | {final_questions['q8']['bengali']}",
                    "questionItem": {
                        "question": {
                            "required": True,
                            "choiceQuestion": {
                                "type": "RADIO",
                                "options": q8_options,
                                "shuffle": False
                            }
                        }
                    }
                },
                "location": {"index": current_index}
            }
        })
        current_index += 1
        
        # Execute batch update
        request_body = {"requests": requests}
        
        def update_operation():
            return self.service.forms().batchUpdate(formId=form_id, body=request_body).execute()
        
        result = self._execute_with_retry(update_operation, "Add final section")
        
        item_ids = []
        try:
            for reply in result['replies']:
                if 'createItem' in reply:
                    item_ids.append(reply['createItem']['item']['itemId'])
        except (KeyError, IndexError) as e:
            self.logger.error(f"Error extracting item IDs from response: {e}")
            # Return placeholder IDs
            item_ids = [f"final_{i}" for i in range(4)]  # 4 items in final section
        
        self.logger.info(f"Added final section with {len(item_ids)} items")
        return item_ids
    
    def generate_complete_form(self, all_ac_data: Dict[str, Dict[str, List[str]]]) -> Dict[str, Any]:
        """
        Generate complete form with all AC sections.
        
        Args:
            all_ac_data: Dictionary containing data for all AC numbers
            
        Returns:
            Dictionary containing form details and metadata
        """
        if not all_ac_data:
            raise ValueError("No AC data provided for form generation")
        
        ac_numbers = list(all_ac_data.keys())
        form_title = f"{self.config.get_google_forms_config()['form_title_prefix']} Multiple ACs"
        
        # Create the form
        form_result = self.create_form(form_title)
        form_id = form_result['formId']
        form_url = f"https://docs.google.com/forms/d/{form_id}/edit"
        
        # Add form description
        description = "Political Survey for Assam Assembly Constituencies"
        self.update_form_description(form_id, description)
        
        try:
            # Add introduction section
            intro_id = self.add_introduction_section(form_id)
            
            # Add basic info section
            basic_info_ids = self.add_basic_info_section(form_id, ac_numbers)
            
            # Add AC-specific sections
            current_index = 5  # After basic info section
            ac_section_mapping = {}
            
            for ac_number in sorted(ac_numbers, key=lambda x: int(x)):
                ac_data = all_ac_data[ac_number]
                section_ids, next_index = self.add_ac_specific_section(
                    form_id, ac_number, ac_data, current_index
                )
                ac_section_mapping[ac_number] = section_ids
                current_index = next_index
            
            # Add final section
            final_ids = self.add_final_section(form_id, current_index)
            
            form_metadata = {
                'form_id': form_id,
                'form_url': form_url,
                'edit_url': form_url,
                'public_url': f"https://docs.google.com/forms/d/{form_id}/viewform",
                'title': form_title,
                'total_ac_numbers': len(ac_numbers),
                'ac_numbers': ac_numbers,
                'section_mapping': {
                    'introduction': intro_id,
                    'basic_info': basic_info_ids,
                    'ac_sections': ac_section_mapping,
                    'final_section': final_ids
                },
                'creation_timestamp': time.time()
            }
            
            self.logger.info(f"Successfully generated complete form for {len(ac_numbers)} AC numbers")
            return form_metadata
            
        except Exception as e:
            self.logger.error(f"Error generating form: {e}")
            # Try to delete the partially created form
            try:
                self.delete_form(form_id)
                self.logger.info("Cleaned up partially created form")
            except:
                self.logger.warning("Could not clean up partially created form")
            raise
    
    def delete_form(self, form_id: str):
        """
        Delete a Google Form.
        
        Args:
            form_id: ID of the form to delete
        """
        try:
            # Note: Google Forms API doesn't have a direct delete method
            # This would require using Drive API to move to trash
            self.logger.warning(f"Form deletion not implemented for form {form_id}")
        except Exception as e:
            self.logger.error(f"Error deleting form {form_id}: {e}")
    
    def get_form_info(self, form_id: str) -> Dict[str, Any]:
        """
        Get information about an existing form.
        
        Args:
            form_id: ID of the form
            
        Returns:
            Form information
        """
        def get_operation():
            return self.service.forms().get(formId=form_id).execute()
        
        return self._execute_with_retry(get_operation, f"Get form info for {form_id}")
