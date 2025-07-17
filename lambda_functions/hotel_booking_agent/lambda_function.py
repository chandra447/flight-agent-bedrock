"""
Hotel Booking Agent Lambda Function
Handles hotel search, booking, and reservation modification operations for the travel booking multi-agent system
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
    from db_utils import DatabaseManager, HotelService
except ImportError:
    # Fallback for local testing
    sys.path.append('../../database')
    from db_utils import DatabaseManager, HotelService

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
    AWS Lambda handler for hotel booking agent operations
    
    Expected event structure:
    {
        'agent': 'hotel-booking-agent',
        'actionGroup': 'hotel-operations',
        'function': 'search_hotels|book_hotel|modify_reservation',
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
        hotel_service = HotelService(db_manager)
        
        # Route to appropriate function
        if function_name == 'search_hotels':
            result = handle_search_hotels(hotel_service, params_dict)
        elif function_name == 'book_hotel':
            result = handle_book_hotel(hotel_service, params_dict)
        elif function_name == 'modify_reservation':
            result = handle_modify_reservation(hotel_service, params_dict)
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
            'actionGroup': event.get('actionGroup', 'hotel-operations'),
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

def handle_search_hotels(hotel_service: HotelService, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle hotel search requests
    
    Input parameters:
    - location: City or location name
    - check_in_date: Check-in date (YYYY-MM-DD)
    - check_out_date: Check-out date (YYYY-MM-DD)
    - guests: Number of guests
    - room_type: Room type preference (optional)
    
    Output:
    - hotel_list: List of available hotels with prices, amenities, ratings, availability
    """
    
    try:
        # Validate required parameters
        required_params = ['location', 'check_in_date', 'check_out_date', 'guests']
        for param in required_params:
            if param not in params:
                return {
                    'success': False,
                    'error': f'Missing required parameter: {param}',
                    'error_type': 'validation_error'
                }
        
        # Extract parameters
        location = params['location']
        check_in_date = params['check_in_date']
        check_out_date = params['check_out_date']
        guests = int(params['guests'])
        room_type = params.get('room_type')
        
        # Validate guest count
        if guests < 1 or guests > 10:
            return {
                'success': False,
                'error': 'Guest count must be between 1 and 10',
                'error_type': 'validation_error'
            }
        
        # Validate dates
        try:
            check_in = datetime.strptime(check_in_date, '%Y-%m-%d').date()
            check_out = datetime.strptime(check_out_date, '%Y-%m-%d').date()
            
            if check_in >= check_out:
                return {
                    'success': False,
                    'error': 'Check-out date must be after check-in date',
                    'error_type': 'validation_error'
                }
            
            if check_in < datetime.now().date():
                return {
                    'success': False,
                    'error': 'Check-in date cannot be in the past',
                    'error_type': 'validation_error'
                }
                
        except ValueError:
            return {
                'success': False,
                'error': 'Invalid date format. Use YYYY-MM-DD',
                'error_type': 'validation_error'
            }
        
        # Search hotels
        search_results = hotel_service.search_hotels(
            location=location,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            guests=guests,
            room_type=room_type
        )
        
        if not search_results:
            return {
                'success': False,
                'error': 'No hotels found for the specified criteria',
                'error_type': 'no_results'
            }
        
        # Calculate nights
        nights = (check_out - check_in).days
        
        # Format hotel results
        formatted_results = {
            'success': True,
            'search_criteria': {
                'location': location,
                'check_in_date': check_in_date,
                'check_out_date': check_out_date,
                'guests': guests,
                'nights': nights,
                'room_type': room_type
            },
            'hotels': format_hotel_list(search_results, nights)
        }
        
        return formatted_results
        
    except ValueError as e:
        return {
            'success': False,
            'error': f'Invalid parameter value: {str(e)}',
            'error_type': 'validation_error'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Hotel search failed: {str(e)}',
            'error_type': 'service_error'
        }

def handle_book_hotel(hotel_service: HotelService, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle hotel booking requests
    
    Input parameters:
    - hotel_id: ID of the hotel to book
    - room_type_id: ID of the room type to book
    - check_in_date: Check-in date (YYYY-MM-DD)
    - check_out_date: Check-out date (YYYY-MM-DD)
    - guest_details: JSON string with guest information
    
    Output:
    - reservation_confirmation: Booking details with booking ID and check-in instructions
    """
    
    try:
        # Validate required parameters
        required_params = ['hotel_id', 'room_type_id', 'check_in_date', 'check_out_date', 'guest_details']
        for param in required_params:
            if param not in params:
                return {
                    'success': False,
                    'error': f'Missing required parameter: {param}',
                    'error_type': 'validation_error'
                }
        
        # Extract parameters
        hotel_id = int(params['hotel_id'])
        room_type_id = int(params['room_type_id'])
        check_in_date = params['check_in_date']
        check_out_date = params['check_out_date']
        
        # Parse guest details
        try:
            if isinstance(params['guest_details'], str):
                guest_details = json.loads(params['guest_details'])
            else:
                guest_details = params['guest_details']
        except json.JSONDecodeError:
            return {
                'success': False,
                'error': 'Invalid guest_details format. Must be valid JSON.',
                'error_type': 'validation_error'
            }
        
        # Default user ID for demo (in production, this would come from authentication)
        user_id = guest_details.get('user_id', 1)
        
        # Book the hotel
        booking_result = hotel_service.book_hotel(
            user_id=user_id,
            hotel_id=hotel_id,
            room_type_id=room_type_id,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            guest_details=guest_details
        )
        
        if not booking_result.get('success'):
            return booking_result
        
        # Format successful booking response
        formatted_result = {
            'success': True,
            'reservation_confirmation': {
                'booking_id': booking_result['booking_id'],
                'booking_reference': booking_result['booking_reference'],
                'total_price': booking_result['total_price'],
                'currency': booking_result['currency'],
                'nights': booking_result['nights'],
                'check_in_date': check_in_date,
                'check_out_date': check_out_date,
                'status': 'CONFIRMED',
                'booking_date': datetime.now().isoformat()
            },
            'check_in_instructions': {
                'check_in_time': '15:00',
                'check_out_time': '11:00',
                'instructions': 'Please bring a valid ID and credit card for check-in'
            },
            'message': f"Hotel successfully booked! Your booking reference is {booking_result['booking_reference']}"
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
            'error': f'Hotel booking failed: {str(e)}',
            'error_type': 'service_error'
        }

def handle_modify_reservation(hotel_service: HotelService, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle hotel reservation modification requests
    
    Input parameters:
    - reservation_id: Booking reference or ID to modify
    - modifications: JSON string with modification details
    
    Output:
    - updated_reservation: Updated booking details with change fees and confirmation
    """
    
    try:
        # Validate required parameters
        required_params = ['reservation_id', 'modifications']
        for param in required_params:
            if param not in params:
                return {
                    'success': False,
                    'error': f'Missing required parameter: {param}',
                    'error_type': 'validation_error'
                }
        
        reservation_id = params['reservation_id']
        
        # Parse modifications
        try:
            if isinstance(params['modifications'], str):
                modifications = json.loads(params['modifications'])
            else:
                modifications = params['modifications']
        except json.JSONDecodeError:
            return {
                'success': False,
                'error': 'Invalid modifications format. Must be valid JSON.',
                'error_type': 'validation_error'
            }
        
        # For demo purposes, simulate modification logic
        # In a real implementation, this would update the database
        formatted_result = {
            'success': True,
            'updated_reservation': {
                'reservation_id': reservation_id,
                'modifications_applied': modifications,
                'change_fees': 0.00,  # Demo: no change fees
                'new_total': modifications.get('new_total', 'unchanged'),
                'status': 'MODIFIED',
                'modification_date': datetime.now().isoformat()
            },
            'message': f"Reservation {reservation_id} has been successfully modified"
        }
        
        return formatted_result
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Reservation modification failed: {str(e)}',
            'error_type': 'service_error'
        }

def format_hotel_list(hotels: List[Dict], nights: int) -> List[Dict]:
    """Format hotel list for response"""
    
    formatted_hotels = []
    
    for hotel in hotels:
        # Parse amenities JSON
        try:
            amenities = json.loads(hotel.get('amenities', '[]'))
        except:
            amenities = []
        
        # Calculate total price for stay
        total_price = hotel['base_price_per_night'] * nights
        
        formatted_hotel = {
            'hotel_id': hotel['hotel_id'],
            'room_type_id': hotel['room_type_id'],
            'property': {
                'name': hotel['hotel_name'],
                'chain': hotel.get('hotel_chain', 'Independent'),
                'star_rating': hotel['star_rating'],
                'guest_rating': hotel['guest_rating']
            },
            'location': {
                'address': hotel['address'],
                'city': hotel['city'],
                'country': hotel['country']
            },
            'room': {
                'type': hotel['room_type_name'],
                'description': hotel['room_description'],
                'max_occupancy': hotel['max_occupancy'],
                'bed_type': hotel['bed_type'],
                'size_sqm': hotel['room_size_sqm']
            },
            'pricing': {
                'price_per_night': hotel['base_price_per_night'],
                'total_price': total_price,
                'currency': hotel['currency']
            },
            'amenities': amenities,
            'policies': {
                'check_in_time': hotel.get('check_in_time', '15:00'),
                'check_out_time': hotel.get('check_out_time', '11:00')
            }
        }
        
        formatted_hotels.append(formatted_hotel)
    
    return formatted_hotels

# For local testing
if __name__ == "__main__":
    # Test event
    test_event = {
        'agent': 'hotel-booking-agent',
        'actionGroup': 'hotel-operations',
        'function': 'search_hotels',
        'parameters': [
            {'name': 'location', 'value': 'New York'},
            {'name': 'check_in_date', 'value': '2024-02-15'},
            {'name': 'check_out_date', 'value': '2024-02-18'},
            {'name': 'guests', 'value': '2'}
        ],
        'sessionAttributes': {},
        'promptSessionAttributes': {}
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))