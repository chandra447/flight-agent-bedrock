"""
Travel Planner Agent Lambda Function
Handles itinerary creation, destination information, and travel advisory operations for the travel booking multi-agent system
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
    from db_utils import DatabaseManager, TravelPlannerService
except ImportError:
    # Fallback for local testing
    sys.path.append('../../database')
    from db_utils import DatabaseManager, TravelPlannerService

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
    AWS Lambda handler for travel planner agent operations
    
    Expected event structure:
    {
        'agent': 'travel-planner-agent',
        'actionGroup': 'travel-planning-operations',
        'function': 'create_itinerary|get_destination_info|get_travel_advisories',
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
        travel_planner_service = TravelPlannerService(db_manager)
        
        # Route to appropriate function
        if function_name == 'create_itinerary':
            result = handle_create_itinerary(travel_planner_service, params_dict)
        elif function_name == 'get_destination_info':
            result = handle_get_destination_info(travel_planner_service, params_dict)
        elif function_name == 'get_travel_advisories':
            result = handle_get_travel_advisories(travel_planner_service, params_dict)
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
            'actionGroup': event.get('actionGroup', 'travel-planning-operations'),
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

def handle_create_itinerary(travel_planner_service: TravelPlannerService, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle itinerary creation requests
    
    Input parameters:
    - destination: Destination name or city
    - duration: Number of days for the trip
    - interests: List of interests/preferences (optional)
    - budget: Budget range or amount (optional)
    
    Output:
    - detailed_itinerary: Complete itinerary with activities, timeline, recommendations
    """
    
    try:
        # Validate required parameters
        required_params = ['destination', 'duration']
        for param in required_params:
            if param not in params:
                return {
                    'success': False,
                    'error': f'Missing required parameter: {param}',
                    'error_type': 'validation_error'
                }
        
        # Extract parameters
        destination = params['destination']
        duration = int(params['duration'])
        interests = params.get('interests', '').split(',') if params.get('interests') else []
        budget = params.get('budget')
        
        # Validate duration
        if duration < 1 or duration > 30:
            return {
                'success': False,
                'error': 'Duration must be between 1 and 30 days',
                'error_type': 'validation_error'
            }
        
        # Clean up interests list
        interests = [interest.strip() for interest in interests if interest.strip()]
        
        # Default user ID for demo (in production, this would come from authentication)
        user_id = 1
        
        # Create itinerary
        itinerary_result = travel_planner_service.create_itinerary(
            user_id=user_id,
            destination=destination,
            duration=duration,
            interests=interests,
            budget=budget
        )
        
        if not itinerary_result.get('success'):
            return itinerary_result
        
        # Format successful itinerary response
        formatted_result = {
            'success': True,
            'detailed_itinerary': {
                'itinerary_id': itinerary_result['itinerary_id'],
                'destination': destination,
                'duration': duration,
                'interests': interests,
                'budget': budget,
                'itinerary_data': itinerary_result['itinerary'],
                'created_date': datetime.now().isoformat()
            },
            'recommendations': generate_travel_recommendations(destination, duration, interests),
            'message': f"Complete {duration}-day itinerary created for {destination}"
        }
        
        return formatted_result
        
    except ValueError as e:
        return {
            'success': False,
            'error': f'Invalid parameter value: {str(e)}',
            'error_type': 'validation_error'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Itinerary creation failed: {str(e)}',
            'error_type': 'service_error'
        }

def handle_get_destination_info(travel_planner_service: TravelPlannerService, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle destination information requests
    
    Input parameters:
    - destination: Destination name or city
    - info_type: Type of information requested (optional)
    
    Output:
    - destination_details: Comprehensive destination information with weather, attractions, local_info, travel_tips
    """
    
    try:
        # Validate required parameters
        if 'destination' not in params:
            return {
                'success': False,
                'error': 'Missing required parameter: destination',
                'error_type': 'validation_error'
            }
        
        destination = params['destination']
        info_type = params.get('info_type', 'general')
        
        # Get destination information
        destination_result = travel_planner_service.get_destination_info(
            destination=destination,
            info_type=info_type
        )
        
        if not destination_result.get('success'):
            return destination_result
        
        dest_info = destination_result['destination']
        attractions = destination_result['attractions']
        
        # Format destination information response
        formatted_result = {
            'success': True,
            'destination_details': {
                'basic_info': {
                    'name': dest_info['destination_name'],
                    'country': dest_info['country'],
                    'region': dest_info['region'],
                    'type': dest_info['destination_type'],
                    'description': dest_info['description']
                },
                'travel_info': {
                    'best_time_to_visit': dest_info['best_time_to_visit'],
                    'average_temperature': f"{dest_info['average_temperature_celsius']}°C",
                    'currency': dest_info['currency'],
                    'language': dest_info['language'],
                    'timezone': dest_info['timezone'],
                    'visa_required': bool(dest_info['visa_required']),
                    'safety_rating': f"{dest_info['safety_rating']}/5",
                    'cost_level': dest_info['cost_level']
                },
                'location': {
                    'latitude': dest_info['latitude'],
                    'longitude': dest_info['longitude']
                },
                'top_attractions': format_attractions_list(attractions[:10]),  # Top 10 attractions
                'local_info': generate_local_info(dest_info),
                'travel_tips': generate_travel_tips(dest_info)
            },
            'message': f"Comprehensive information for {destination} retrieved successfully"
        }
        
        return formatted_result
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Destination information retrieval failed: {str(e)}',
            'error_type': 'service_error'
        }

def handle_get_travel_advisories(travel_planner_service: TravelPlannerService, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle travel advisory requests
    
    Input parameters:
    - destination: Destination name or city
    
    Output:
    - travel_advisories: Current travel advisories with safety_info, visa_requirements, health_recommendations
    """
    
    try:
        # Validate required parameters
        if 'destination' not in params:
            return {
                'success': False,
                'error': 'Missing required parameter: destination',
                'error_type': 'validation_error'
            }
        
        destination = params['destination']
        
        # Get travel advisories
        advisories_result = travel_planner_service.get_travel_advisories(destination)
        
        if not advisories_result.get('success'):
            return advisories_result
        
        advisories = advisories_result['advisories']
        
        # Categorize advisories
        categorized_advisories = {
            'health': [],
            'safety': [],
            'visa': [],
            'weather': [],
            'general': []
        }
        
        for advisory in advisories:
            category = advisory['advisory_type'].lower()
            if category in categorized_advisories:
                categorized_advisories[category].append({
                    'level': advisory['advisory_level'],
                    'title': advisory['title'],
                    'description': advisory['description'],
                    'source': advisory['source'],
                    'effective_date': advisory['effective_date'],
                    'expiry_date': advisory['expiry_date'],
                    'last_updated': advisory['last_updated']
                })
            else:
                categorized_advisories['general'].append({
                    'type': advisory['advisory_type'],
                    'level': advisory['advisory_level'],
                    'title': advisory['title'],
                    'description': advisory['description'],
                    'source': advisory['source'],
                    'effective_date': advisory['effective_date'],
                    'expiry_date': advisory['expiry_date'],
                    'last_updated': advisory['last_updated']
                })
        
        # Format travel advisories response
        formatted_result = {
            'success': True,
            'travel_advisories': {
                'destination': destination,
                'last_updated': datetime.now().isoformat(),
                'health_recommendations': categorized_advisories['health'],
                'safety_info': categorized_advisories['safety'],
                'visa_requirements': categorized_advisories['visa'],
                'weather_alerts': categorized_advisories['weather'],
                'general_advisories': categorized_advisories['general'],
                'summary': generate_advisory_summary(categorized_advisories)
            },
            'message': f"Current travel advisories for {destination} retrieved successfully"
        }
        
        return formatted_result
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Travel advisories retrieval failed: {str(e)}',
            'error_type': 'service_error'
        }

def format_attractions_list(attractions: List[Dict]) -> List[Dict]:
    """Format attractions list for response"""
    
    formatted_attractions = []
    
    for attraction in attractions:
        formatted_attraction = {
            'name': attraction['attraction_name'],
            'type': attraction['attraction_type'],
            'description': attraction['description'],
            'address': attraction.get('address', 'Address not available'),
            'opening_hours': attraction.get('opening_hours', 'Hours not available'),
            'admission_price': {
                'amount': attraction.get('admission_price', 0),
                'currency': attraction.get('currency', 'USD')
            },
            'rating': attraction.get('rating', 0),
            'visit_duration': f"{attraction.get('visit_duration_hours', 1)} hours",
            'best_time_to_visit': attraction.get('best_time_to_visit', 'Year-round'),
            'contact': {
                'website': attraction.get('website'),
                'phone': attraction.get('phone')
            }
        }
        
        formatted_attractions.append(formatted_attraction)
    
    return formatted_attractions

def generate_local_info(dest_info: Dict) -> Dict:
    """Generate local information based on destination"""
    
    return {
        'currency_info': {
            'currency': dest_info['currency'],
            'exchange_tips': f"Exchange money at banks or authorized dealers for best rates"
        },
        'language_info': {
            'primary_language': dest_info['language'],
            'english_spoken': 'English is widely spoken in tourist areas' if dest_info['language'] != 'English' else 'English is the primary language'
        },
        'transportation': {
            'getting_around': 'Public transportation, taxis, and ride-sharing services available',
            'airport_transfer': 'Multiple options available including buses, trains, and taxis'
        },
        'cultural_notes': {
            'tipping': 'Tipping customs vary by location and service type',
            'dress_code': 'Dress modestly when visiting religious sites',
            'business_hours': 'Most businesses open 9 AM - 6 PM, restaurants until late'
        }
    }

def generate_travel_tips(dest_info: Dict) -> List[str]:
    """Generate travel tips based on destination"""
    
    tips = [
        f"Best time to visit: {dest_info['best_time_to_visit']}",
        f"Average temperature: {dest_info['average_temperature_celsius']}°C",
        f"Budget level: {dest_info['cost_level']} - plan accordingly",
        "Book accommodations in advance during peak season",
        "Keep copies of important documents in separate locations",
        "Check visa requirements well in advance of travel",
        "Consider travel insurance for international trips",
        "Research local customs and etiquette before arrival"
    ]
    
    if dest_info['visa_required']:
        tips.append("Visa required - apply at least 2-4 weeks before travel")
    
    return tips

def generate_travel_recommendations(destination: str, duration: int, interests: List[str]) -> Dict:
    """Generate travel recommendations based on parameters"""
    
    recommendations = {
        'packing_suggestions': [
            'Comfortable walking shoes',
            'Weather-appropriate clothing',
            'Portable charger and adapters',
            'First aid kit basics',
            'Camera or smartphone for photos'
        ],
        'budget_tips': [
            'Book flights and hotels in advance for better rates',
            'Consider traveling during shoulder season',
            'Look for package deals combining multiple services',
            'Use public transportation when possible',
            'Try local restaurants for authentic and affordable meals'
        ],
        'activity_suggestions': []
    }
    
    # Add interest-based recommendations
    if 'culture' in [i.lower() for i in interests]:
        recommendations['activity_suggestions'].extend([
            'Visit local museums and cultural sites',
            'Attend traditional performances or festivals',
            'Take a guided historical walking tour'
        ])
    
    if 'food' in [i.lower() for i in interests]:
        recommendations['activity_suggestions'].extend([
            'Try local specialties and street food',
            'Take a cooking class',
            'Visit local markets and food halls'
        ])
    
    if 'nature' in [i.lower() for i in interests]:
        recommendations['activity_suggestions'].extend([
            'Explore parks and natural areas',
            'Consider day trips to scenic locations',
            'Look for hiking or outdoor activity opportunities'
        ])
    
    # Default activities if no specific interests
    if not recommendations['activity_suggestions']:
        recommendations['activity_suggestions'] = [
            'Visit top-rated attractions and landmarks',
            'Explore different neighborhoods',
            'Try local cuisine and dining experiences',
            'Take photos at scenic viewpoints',
            'Shop for local souvenirs and crafts'
        ]
    
    return recommendations

def generate_advisory_summary(advisories: Dict) -> str:
    """Generate a summary of travel advisories"""
    
    total_advisories = sum(len(advisories[category]) for category in advisories)
    
    if total_advisories == 0:
        return "No current travel advisories. Standard travel precautions recommended."
    
    high_priority = []
    for category in advisories:
        for advisory in advisories[category]:
            if advisory.get('level') in ['HIGH', 'CRITICAL']:
                high_priority.append(f"{category.title()}: {advisory.get('title', 'Advisory')}")
    
    if high_priority:
        return f"High priority advisories: {'; '.join(high_priority)}. Review all advisories before travel."
    else:
        return f"{total_advisories} travel advisories found. Review for important travel information."

# For local testing
if __name__ == "__main__":
    # Test event
    test_event = {
        'agent': 'travel-planner-agent',
        'actionGroup': 'travel-planning-operations',
        'function': 'get_destination_info',
        'parameters': [
            {'name': 'destination', 'value': 'Paris'},
            {'name': 'info_type', 'value': 'general'}
        ],
        'sessionAttributes': {},
        'promptSessionAttributes': {}
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))