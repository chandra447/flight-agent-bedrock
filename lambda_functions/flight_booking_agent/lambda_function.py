"""
Flight Booking Agent Lambda Function
Handles flight search, booking, and cancellation operations for the travel booking multi-agent system
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
    from db_utils import DatabaseManager, FlightService
except ImportError:
    # Fallback for local testing
    sys.path.append('../../database')
    from db_utils import DatabaseManager, FlightService

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
    AWS Lambda handler for flight booking agent operations
    
    Expected event structure:
    {
        'agent': 'flight-booking-agent',
        'actionGroup': 'flight-operations',
        'function': 'search_flights|book_flight|cancel_flight',
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
        flight_service = FlightService(db_manager)
        
        # Route to appropriate function
        if function_name == 'search_flights':
            result = handle_search_flights(flight_service, params_dict)
        elif function_name == 'book_flight':
            result = handle_book_flight(flight_service, params_dict)
        elif function_name == 'cancel_flight':
            result = handle_cancel_flight(flight_service, params_dict)
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
            'actionGroup': event.get('actionGroup', 'flight-operations'),
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

def handle_search_flights(flight_service: FlightService, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle flight search requests
    
    Input parameters:
    - origin: Origin airport code or city name
    - destination: Destination airport code or city name  
    - departure_date: Departure date (YYYY-MM-DD)
    - return_date: Return date (YYYY-MM-DD, optional)
    - passengers: Number of passengers
    
    Output:
    - flight_list: List of available flights with prices, times, airlines
    """
    
    try:
        # Validate required parameters
        required_params = ['origin', 'destination', 'departure_date', 'passengers']
        for param in required_params:
            if param not in params:
                return {
                    'success': False,
                    'error': f'Missing required parameter: {param}',
                    'error_type': 'validation_error'
                }
        
        # Extract parameters
        origin = params['origin']
        destination = params['destination']
        departure_date = params['departure_date']
        return_date = params.get('return_date')
        passengers = int(params['passengers'])
        
        # Validate passenger count
        if passengers < 1 or passengers > 9:
            return {
                'success': False,
                'error': 'Passenger count must be between 1 and 9',
                'error_type': 'validation_error'
            }
        
        # Search flights
        search_results = flight_service.search_flights(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            passengers=passengers
        )
        
        if not search_results:
            return {
                'success': False,
                'error': 'No flights found for the specified criteria',
                'error_type': 'no_results'
            }
        
        # Format flight results
        formatted_results = {
            'success': True,
            'search_criteria': {
                'origin': origin,
                'destination': destination,
                'departure_date': departure_date,
                'return_date': return_date,
                'passengers': passengers
            },
            'outbound_flights': format_flight_list(search_results.get('outbound_flights', [])),
            'return_flights': format_flight_list(search_results.get('return_flights', [])) if return_date else []
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
            'error': f'Flight search failed: {str(e)}',
            'error_type': 'service_error'
        }

def handle_book_flight(flight_service: FlightService, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle flight booking requests
    
    Input parameters:
    - flight_id: ID of the flight to book
    - passenger_details: JSON string with passenger information
    
    Output:
    - booking_confirmation: Booking details with reference number and status
    """
    
    try:
        # Validate required parameters
        required_params = ['flight_id', 'passenger_details']
        for param in required_params:
            if param not in params:
                return {
                    'success': False,
                    'error': f'Missing required parameter: {param}',
                    'error_type': 'validation_error'
                }
        
        # Extract parameters
        flight_id = int(params['flight_id'])
        
        # Parse passenger details
        try:
            if isinstance(params['passenger_details'], str):
                passenger_details = json.loads(params['passenger_details'])
            else:
                passenger_details = params['passenger_details']
        except json.JSONDecodeError:
            return {
                'success': False,
                'error': 'Invalid passenger_details format. Must be valid JSON.',
                'error_type': 'validation_error'
            }
        
        # Default user ID for demo (in production, this would come from authentication)
        user_id = passenger_details.get('user_id', 1)
        
        # Book the flight
        booking_result = flight_service.book_flight(
            user_id=user_id,
            flight_id=flight_id,
            passenger_details=passenger_details
        )
        
        if not booking_result.get('success'):
            return booking_result
        
        # Format successful booking response
        formatted_result = {
            'success': True,
            'booking_confirmation': {
                'booking_id': booking_result['booking_id'],
                'booking_reference': booking_result['booking_reference'],
                'total_price': booking_result['total_price'],
                'currency': booking_result['currency'],
                'status': 'CONFIRMED',
                'booking_date': datetime.now().isoformat()
            },
            'message': f"Flight successfully booked! Your booking reference is {booking_result['booking_reference']}"
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
            'error': f'Flight booking failed: {str(e)}',
            'error_type': 'service_error'
        }

def handle_cancel_flight(flight_service: FlightService, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle flight cancellation requests
    
    Input parameters:
    - booking_reference: Booking reference number to cancel
    
    Output:
    - cancellation_status: Cancellation details with refund information
    """
    
    try:
        # Validate required parameters
        if 'booking_reference' not in params:
            return {
                'success': False,
                'error': 'Missing required parameter: booking_reference',
                'error_type': 'validation_error'
            }
        
        booking_reference = params['booking_reference']
        
        # Cancel the flight
        cancellation_result = flight_service.cancel_flight(booking_reference)
        
        if not cancellation_result.get('success'):
            return cancellation_result
        
        # Format successful cancellation response
        formatted_result = {
            'success': True,
            'cancellation_status': {
                'booking_reference': booking_reference,
                'status': 'CANCELLED',
                'refund_amount': cancellation_result['refund_amount'],
                'currency': cancellation_result['currency'],
                'cancellation_date': datetime.now().isoformat()
            },
            'message': f"Flight booking {booking_reference} has been successfully cancelled. Refund of {cancellation_result['currency']} {cancellation_result['refund_amount']} will be processed."
        }
        
        return formatted_result
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Flight cancellation failed: {str(e)}',
            'error_type': 'service_error'
        }

def format_flight_list(flights: List[Dict]) -> List[Dict]:
    """Format flight list for response"""
    
    formatted_flights = []
    
    for flight in flights:
        formatted_flight = {
            'flight_id': flight['flight_id'],
            'flight_number': flight['flight_number'],
            'airline': {
                'code': flight['airline_code'],
                'name': flight['airline_name']
            },
            'route': {
                'origin': {
                    'code': flight['origin_code'],
                    'city': flight['origin_city']
                },
                'destination': {
                    'code': flight['destination_code'],
                    'city': flight['destination_city']
                }
            },
            'schedule': {
                'departure_time': flight['departure_time'],
                'arrival_time': flight['arrival_time']
            },
            'aircraft': flight['aircraft_type'],
            'pricing': {
                'base_price': flight['base_price'],
                'currency': flight['currency']
            },
            'availability': {
                'total_seats': flight['total_seats'],
                'available_seats': flight['available_seats']
            }
        }
        
        formatted_flights.append(formatted_flight)
    
    return formatted_flights

# For local testing
if __name__ == "__main__":
    # Test event
    test_event = {
        'agent': 'flight-booking-agent',
        'actionGroup': 'flight-operations',
        'function': 'search_flights',
        'parameters': [
            {'name': 'origin', 'value': 'JFK'},
            {'name': 'destination', 'value': 'LAX'},
            {'name': 'departure_date', 'value': '2024-02-15'},
            {'name': 'passengers', 'value': '2'}
        ],
        'sessionAttributes': {},
        'promptSessionAttributes': {}
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))