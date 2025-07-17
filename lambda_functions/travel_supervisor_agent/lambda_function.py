"""
Travel Supervisor Agent Lambda Function
Handles request analysis, specialist coordination, and response consolidation for the travel booking multi-agent system
"""

import json
import os
import sys
import sqlite3
import boto3
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Add the database utilities to the path
sys.path.append('/opt/python')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# S3 configuration
S3_BUCKET = 'travel-agent-data'
S3_DB_KEY = 'travel_booking.db'
LOCAL_DB_PATH = '/tmp/travel_booking.db'

# Import database utilities
try:
    from db_utils import DatabaseManager
except ImportError:
    # Fallback for local testing
    sys.path.append('../../database')
    from db_utils import DatabaseManager

def download_database_from_s3():
    """Download the SQLite database from S3 to local temp storage"""
    try:
        s3_client = boto3.client('s3')
        
        # Check if database already exists locally and is recent (within 1 hour)
        if os.path.exists(LOCAL_DB_PATH):
            file_age = datetime.now().timestamp() - os.path.getmtime(LOCAL_DB_PATH)
            if file_age < 3600:  # 1 hour in seconds
                return LOCAL_DB_PATH
        
        # Download database from S3
        s3_client.download_file(S3_BUCKET, S3_DB_KEY, LOCAL_DB_PATH)
        print(f"Database downloaded from s3://{S3_BUCKET}/{S3_DB_KEY} to {LOCAL_DB_PATH}")
        
        return LOCAL_DB_PATH
        
    except Exception as e:
        print(f"Error downloading database from S3: {str(e)}")
        # Fallback to local database for testing
        fallback_path = '../../database/travel_booking.db'
        if os.path.exists(fallback_path):
            return fallback_path
        raise e

def lambda_handler(event, context):
    """
    AWS Lambda handler for travel supervisor agent operations
    
    Expected event structure:
    {
        'agent': 'travel-supervisor-agent',
        'actionGroup': 'supervisor-operations',
        'function': 'analyze_request|coordinate_specialists|consolidate_response',
        'parameters': [...],
        'sessionAttributes': {...},
        'promptSessionAttributes': {...}
    }
    """
    
    try:
        # Extract event information
        agent = event.get('agent')
        action_group = event.get('actionGroup')
        function_name = event.get('function')
        parameters = event.get('parameters', [])
        session_attributes = event.get('sessionAttributes', {})
        prompt_session_attributes = event.get('promptSessionAttributes', {})
        
        # Convert parameters list to dictionary
        params_dict = {}
        for param in parameters:
            params_dict[param.get('name')] = param.get('value')
        
        # Download database from S3
        db_path = download_database_from_s3()
        
        # Initialize database services
        db_manager = DatabaseManager(db_path)
        
        # Route to appropriate function
        if function_name == 'analyze_request':
            result = handle_analyze_request(db_manager, params_dict)
        elif function_name == 'coordinate_specialists':
            result = handle_coordinate_specialists(db_manager, params_dict)
        elif function_name == 'consolidate_response':
            result = handle_consolidate_response(db_manager, params_dict)
        else:
            result = {
                'success': False,
                'error': f'Unknown function: {function_name}'
            }
        
        # Format response body
        response_body = {
            'TEXT': {
                'body': json.dumps(result, indent=2)
            }
        }
        
        # Create function response
        function_response = {
            'actionGroup': action_group,
            'function': function_name,
            'functionResponse': {
                'responseBody': response_body
            }
        }
        
        # Create action response
        action_response = {
            'messageVersion': '1.0',
            'response': function_response,
            'sessionAttributes': session_attributes,
            'promptSessionAttributes': prompt_session_attributes
        }
        
        return action_response
        
    except Exception as e:
        # Error handling
        error_response = {
            'success': False,
            'error': str(e),
            'error_type': 'system_error'
        }
        
        response_body = {
            'TEXT': {
                'body': json.dumps(error_response, indent=2)
            }
        }
        
        function_response = {
            'actionGroup': event.get('actionGroup', 'supervisor-operations'),
            'function': event.get('function', 'unknown'),
            'functionResponse': {
                'responseBody': response_body
            }
        }
        
        action_response = {
            'messageVersion': '1.0',
            'response': function_response,
            'sessionAttributes': event.get('sessionAttributes', {}),
            'promptSessionAttributes': event.get('promptSessionAttributes', {})
        }
        
        return action_response

def handle_analyze_request(db_manager: DatabaseManager, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle travel request analysis
    
    Input parameters:
    - user_request: The travel request from the user
    - request_type: Type of travel request (optional)
    
    Output:
    - analysis_result: Analysis with required_agents, priority, complexity_score
    """
    
    try:
        # Validate required parameters
        if 'user_request' not in params:
            return {
                'success': False,
                'error': 'Missing required parameter: user_request',
                'error_type': 'validation_error'
            }
        
        user_request = params['user_request']
        request_type = params.get('request_type', 'general')
        
        # Analyze the request to determine required services
        analysis = analyze_travel_request(user_request)
        
        # Format analysis response
        formatted_result = {
            'success': True,
            'analysis_result': {
                'request_summary': user_request,
                'request_type': analysis['request_type'],
                'complexity_score': analysis['complexity_score'],
                'priority': analysis['priority'],
                'required_agents': analysis['required_agents'],
                'estimated_duration': analysis['estimated_duration'],
                'key_requirements': analysis['key_requirements'],
                'potential_challenges': analysis['potential_challenges'],
                'recommended_approach': analysis['recommended_approach']
            },
            'coordination_plan': {
                'agent_sequence': analysis['agent_sequence'],
                'parallel_tasks': analysis['parallel_tasks'],
                'dependencies': analysis['dependencies']
            },
            'message': f"Travel request analyzed. {len(analysis['required_agents'])} specialist agents required."
        }
        
        return formatted_result
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Request analysis failed: {str(e)}',
            'error_type': 'service_error'
        }

def handle_coordinate_specialists(db_manager: DatabaseManager, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle specialist coordination
    
    Input parameters:
    - specialist_responses: JSON string with responses from specialist agents
    - request_context: Context information about the original request
    
    Output:
    - coordination_plan: Plan with task_assignments, dependencies
    """
    
    try:
        # Validate required parameters
        required_params = ['specialist_responses', 'request_context']
        for param in required_params:
            if param not in params:
                return {
                    'success': False,
                    'error': f'Missing required parameter: {param}',
                    'error_type': 'validation_error'
                }
        
        # Parse specialist responses
        try:
            if isinstance(params['specialist_responses'], str):
                specialist_responses = json.loads(params['specialist_responses'])
            else:
                specialist_responses = params['specialist_responses']
        except json.JSONDecodeError:
            return {
                'success': False,
                'error': 'Invalid specialist_responses format. Must be valid JSON.',
                'error_type': 'validation_error'
            }
        
        # Parse request context
        try:
            if isinstance(params['request_context'], str):
                request_context = json.loads(params['request_context'])
            else:
                request_context = params['request_context']
        except json.JSONDecodeError:
            return {
                'success': False,
                'error': 'Invalid request_context format. Must be valid JSON.',
                'error_type': 'validation_error'
            }
        
        # Coordinate specialist responses
        coordination = coordinate_specialist_responses(specialist_responses, request_context)
        
        # Format coordination response
        formatted_result = {
            'success': True,
            'coordination_plan': {
                'task_assignments': coordination['task_assignments'],
                'dependencies': coordination['dependencies'],
                'timeline': coordination['timeline'],
                'resource_allocation': coordination['resource_allocation'],
                'risk_assessment': coordination['risk_assessment'],
                'contingency_plans': coordination['contingency_plans']
            },
            'next_steps': coordination['next_steps'],
            'message': f"Coordination plan created for {len(specialist_responses)} specialist responses"
        }
        
        return formatted_result
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Specialist coordination failed: {str(e)}',
            'error_type': 'service_error'
        }

def handle_consolidate_response(db_manager: DatabaseManager, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle response consolidation
    
    Input parameters:
    - multiple_agent_responses: JSON string with responses from multiple agents
    - user_context: Context about the user and their preferences
    
    Output:
    - unified_response: Consolidated response with recommendations, booking_options, next_steps
    """
    
    try:
        # Validate required parameters
        required_params = ['multiple_agent_responses', 'user_context']
        for param in required_params:
            if param not in params:
                return {
                    'success': False,
                    'error': f'Missing required parameter: {param}',
                    'error_type': 'validation_error'
                }
        
        # Parse agent responses
        try:
            if isinstance(params['multiple_agent_responses'], str):
                agent_responses = json.loads(params['multiple_agent_responses'])
            else:
                agent_responses = params['multiple_agent_responses']
        except json.JSONDecodeError:
            return {
                'success': False,
                'error': 'Invalid multiple_agent_responses format. Must be valid JSON.',
                'error_type': 'validation_error'
            }
        
        # Parse user context
        try:
            if isinstance(params['user_context'], str):
                user_context = json.loads(params['user_context'])
            else:
                user_context = params['user_context']
        except json.JSONDecodeError:
            return {
                'success': False,
                'error': 'Invalid user_context format. Must be valid JSON.',
                'error_type': 'validation_error'
            }
        
        # Consolidate responses
        consolidation = consolidate_agent_responses(agent_responses, user_context)
        
        # Format consolidated response
        formatted_result = {
            'success': True,
            'unified_response': {
                'travel_package_summary': consolidation['package_summary'],
                'recommendations': consolidation['recommendations'],
                'booking_options': consolidation['booking_options'],
                'pricing_summary': consolidation['pricing_summary'],
                'timeline': consolidation['timeline'],
                'alternatives': consolidation['alternatives'],
                'important_notes': consolidation['important_notes']
            },
            'next_steps': consolidation['next_steps'],
            'booking_instructions': consolidation['booking_instructions'],
            'message': f"Consolidated travel package created with {len(consolidation['booking_options'])} booking options"
        }
        
        return formatted_result
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Response consolidation failed: {str(e)}',
            'error_type': 'service_error'
        }

def analyze_travel_request(user_request: str) -> Dict[str, Any]:
    """Analyze a travel request to determine required services and complexity"""
    
    request_lower = user_request.lower()
    
    # Determine request type and required agents
    required_agents = []
    request_type = 'general'
    complexity_score = 1
    
    # Check for flight-related keywords
    if any(keyword in request_lower for keyword in ['flight', 'fly', 'airline', 'airport', 'departure', 'arrival']):
        required_agents.append('flight-booking-agent')
        request_type = 'flight' if request_type == 'general' else 'multi-service'
        complexity_score += 1
    
    # Check for hotel-related keywords
    if any(keyword in request_lower for keyword in ['hotel', 'accommodation', 'stay', 'room', 'resort', 'lodge']):
        required_agents.append('hotel-booking-agent')
        request_type = 'hotel' if request_type == 'general' else 'multi-service'
        complexity_score += 1
    
    # Check for car rental keywords
    if any(keyword in request_lower for keyword in ['car', 'rental', 'drive', 'vehicle', 'auto']):
        required_agents.append('car-rental-agent')
        request_type = 'car-rental' if request_type == 'general' else 'multi-service'
        complexity_score += 1
    
    # Check for travel planning keywords
    if any(keyword in request_lower for keyword in ['itinerary', 'plan', 'destination', 'attractions', 'activities', 'sightseeing']):
        required_agents.append('travel-planner-agent')
        request_type = 'planning' if request_type == 'general' else 'multi-service'
        complexity_score += 1
    
    # If no specific services detected, assume general travel planning
    if not required_agents:
        required_agents.append('travel-planner-agent')
        request_type = 'planning'
    
    # Determine priority based on urgency keywords
    priority = 'medium'
    if any(keyword in request_lower for keyword in ['urgent', 'asap', 'immediately', 'emergency']):
        priority = 'high'
    elif any(keyword in request_lower for keyword in ['flexible', 'whenever', 'no rush']):
        priority = 'low'
    
    # Estimate duration based on complexity
    estimated_duration = f"{complexity_score * 5}-{complexity_score * 10} minutes"
    
    # Identify key requirements
    key_requirements = []
    if 'budget' in request_lower or 'cheap' in request_lower or 'expensive' in request_lower:
        key_requirements.append('Budget considerations')
    if 'date' in request_lower or 'time' in request_lower:
        key_requirements.append('Specific timing requirements')
    if 'group' in request_lower or 'family' in request_lower:
        key_requirements.append('Group travel coordination')
    
    # Identify potential challenges
    potential_challenges = []
    if complexity_score > 3:
        potential_challenges.append('Multi-service coordination complexity')
    if 'international' in request_lower:
        potential_challenges.append('International travel requirements')
    if priority == 'high':
        potential_challenges.append('Time-sensitive booking requirements')
    
    # Determine agent sequence and dependencies
    agent_sequence = []
    parallel_tasks = []
    dependencies = {}
    
    if 'travel-planner-agent' in required_agents:
        agent_sequence.append('travel-planner-agent')
        dependencies['travel-planner-agent'] = []
    
    # Flight, hotel, and car can often be done in parallel
    parallel_agents = [agent for agent in required_agents if agent != 'travel-planner-agent']
    if parallel_agents:
        parallel_tasks.append(parallel_agents)
        for agent in parallel_agents:
            dependencies[agent] = ['travel-planner-agent'] if 'travel-planner-agent' in required_agents else []
    
    return {
        'request_type': request_type,
        'complexity_score': complexity_score,
        'priority': priority,
        'required_agents': required_agents,
        'estimated_duration': estimated_duration,
        'key_requirements': key_requirements,
        'potential_challenges': potential_challenges,
        'recommended_approach': f"Coordinate {len(required_agents)} specialist agents with {'sequential' if len(agent_sequence) > 1 else 'parallel'} execution",
        'agent_sequence': agent_sequence,
        'parallel_tasks': parallel_tasks,
        'dependencies': dependencies
    }

def coordinate_specialist_responses(specialist_responses: Dict, request_context: Dict) -> Dict[str, Any]:
    """Coordinate responses from multiple specialist agents"""
    
    # Analyze responses for conflicts and dependencies
    task_assignments = {}
    timeline = []
    resource_allocation = {}
    risk_assessment = []
    contingency_plans = []
    
    for agent, response in specialist_responses.items():
        # Extract task assignments
        if response.get('success'):
            task_assignments[agent] = {
                'status': 'ready',
                'estimated_time': '5-10 minutes',
                'dependencies': [],
                'outputs': response.get('outputs', [])
            }
        else:
            task_assignments[agent] = {
                'status': 'failed',
                'error': response.get('error', 'Unknown error'),
                'retry_required': True
            }
            risk_assessment.append(f"{agent}: {response.get('error', 'Unknown error')}")
    
    # Create timeline
    timeline = [
        {
            'phase': 'Information Gathering',
            'duration': '2-5 minutes',
            'agents': list(specialist_responses.keys())
        },
        {
            'phase': 'Option Presentation',
            'duration': '1-2 minutes',
            'agents': ['travel-supervisor-agent']
        },
        {
            'phase': 'Booking Execution',
            'duration': '5-10 minutes',
            'agents': [agent for agent in specialist_responses.keys() if 'booking' in agent]
        }
    ]
    
    # Resource allocation
    for agent in specialist_responses.keys():
        resource_allocation[agent] = {
            'priority': 'high' if 'booking' in agent else 'medium',
            'resources_needed': ['database_access', 'external_api_access']
        }
    
    # Contingency plans
    if risk_assessment:
        contingency_plans.append('Retry failed operations with alternative parameters')
        contingency_plans.append('Provide manual booking instructions if automated booking fails')
    
    next_steps = [
        'Review specialist recommendations',
        'Present consolidated options to user',
        'Execute approved bookings',
        'Provide confirmation and documentation'
    ]
    
    return {
        'task_assignments': task_assignments,
        'dependencies': {},
        'timeline': timeline,
        'resource_allocation': resource_allocation,
        'risk_assessment': risk_assessment,
        'contingency_plans': contingency_plans,
        'next_steps': next_steps
    }

def consolidate_agent_responses(agent_responses: Dict, user_context: Dict) -> Dict[str, Any]:
    """Consolidate responses from multiple agents into a unified travel package"""
    
    # Extract information from each agent response
    flight_options = []
    hotel_options = []
    car_options = []
    itinerary_info = {}
    
    for agent, response in agent_responses.items():
        if 'flight' in agent and response.get('success'):
            flight_options.extend(response.get('outbound_flights', []))
        elif 'hotel' in agent and response.get('success'):
            hotel_options.extend(response.get('hotels', []))
        elif 'car' in agent and response.get('success'):
            car_options.extend(response.get('rental_cars', []))
        elif 'planner' in agent and response.get('success'):
            itinerary_info = response.get('detailed_itinerary', {})
    
    # Create package summary
    package_summary = {
        'destination': user_context.get('destination', 'Multiple destinations'),
        'duration': user_context.get('duration', 'Flexible'),
        'travelers': user_context.get('travelers', 1),
        'services_included': []
    }
    
    if flight_options:
        package_summary['services_included'].append('Flights')
    if hotel_options:
        package_summary['services_included'].append('Accommodation')
    if car_options:
        package_summary['services_included'].append('Car Rental')
    if itinerary_info:
        package_summary['services_included'].append('Itinerary Planning')
    
    # Create recommendations
    recommendations = []
    if flight_options:
        recommendations.append(f"Found {len(flight_options)} flight options")
    if hotel_options:
        recommendations.append(f"Found {len(hotel_options)} accommodation options")
    if car_options:
        recommendations.append(f"Found {len(car_options)} car rental options")
    
    # Create booking options (simplified for demo)
    booking_options = [
        {
            'package_name': 'Complete Travel Package',
            'includes': package_summary['services_included'],
            'estimated_total': 'Pricing available upon selection',
            'booking_method': 'Coordinate through travel supervisor'
        }
    ]
    
    # Pricing summary
    pricing_summary = {
        'flight_range': 'Varies by selection',
        'hotel_range': 'Varies by selection',
        'car_rental_range': 'Varies by selection',
        'total_estimate': 'Contact for detailed pricing'
    }
    
    # Timeline
    timeline = {
        'booking_deadline': 'Recommend booking within 24 hours for best rates',
        'travel_dates': user_context.get('travel_dates', 'To be determined'),
        'confirmation_time': '1-2 hours after booking'
    }
    
    # Alternatives
    alternatives = [
        'Book services individually for more flexibility',
        'Consider alternative dates for better pricing',
        'Explore different service levels (economy vs premium)'
    ]
    
    # Important notes
    important_notes = [
        'Prices subject to availability and change',
        'Cancellation policies vary by service provider',
        'Travel insurance recommended for international trips',
        'Check visa and documentation requirements'
    ]
    
    # Next steps
    next_steps = [
        'Review all options and select preferences',
        'Confirm travel dates and passenger details',
        'Proceed with booking selected services',
        'Receive confirmations and travel documents'
    ]
    
    # Booking instructions
    booking_instructions = [
        'Select preferred options from each category',
        'Provide passenger and payment information',
        'Review terms and conditions',
        'Confirm booking and receive confirmations'
    ]
    
    return {
        'package_summary': package_summary,
        'recommendations': recommendations,
        'booking_options': booking_options,
        'pricing_summary': pricing_summary,
        'timeline': timeline,
        'alternatives': alternatives,
        'important_notes': important_notes,
        'next_steps': next_steps,
        'booking_instructions': booking_instructions
    }

# For local testing
if __name__ == "__main__":
    # Test event
    test_event = {
        'agent': 'travel-supervisor-agent',
        'actionGroup': 'supervisor-operations',
        'function': 'analyze_request',
        'parameters': [
            {'name': 'user_request', 'value': 'I need to book a flight and hotel for a business trip to New York next week'},
            {'name': 'request_type', 'value': 'business'}
        ],
        'sessionAttributes': {},
        'promptSessionAttributes': {}
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))