"""
Car Rental Agent Lambda Function
Handles vehicle search, booking, and rental cancellation operations for the travel booking multi-agent system
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
    from db_utils import DatabaseManager, CarRentalService
except ImportError:
    # Fallback for local testing
    sys.path.append('../../database')
    from db_utils import DatabaseManager, CarRentalService

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
    AWS Lambda handler for car rental agent operations
    
    Expected event structure:
    {
        'agent': 'car-rental-agent',
        'actionGroup': 'car-rental-operations',
        'function': 'search_cars|book_car|cancel_rental',
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
        car_rental_service = CarRentalService(db_manager)
        
        # Route to appropriate function
        if function_name == 'search_cars':
            result = handle_search_cars(car_rental_service, params_dict)
        elif function_name == 'book_car':
            result = handle_book_car(car_rental_service, params_dict)
        elif function_name == 'cancel_rental':
            result = handle_cancel_rental(car_rental_service, params_dict)
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
            'actionGroup': event.get('actionGroup', 'car-rental-operations'),
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

def handle_search_cars(car_rental_service: CarRentalService, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle car rental search requests
    
    Input parameters:
    - pickup_location: Pickup location (city or airport)
    - dropoff_location: Drop-off location (city or airport)
    - pickup_date: Pickup date and time (YYYY-MM-DD HH:MM:SS)
    - dropoff_date: Drop-off date and time (YYYY-MM-DD HH:MM:SS)
    - car_type: Vehicle category preference (optional)
    
    Output:
    - car_list: List of available rental cars with prices, vehicle specs, availability, rental terms
    """
    
    try:
        # Validate required parameters
        required_params = ['pickup_location', 'dropoff_location', 'pickup_date', 'dropoff_date']
        for param in required_params:
            if param not in params:
                return {
                    'success': False,
                    'error': f'Missing required parameter: {param}',
                    'error_type': 'validation_error'
                }
        
        # Extract parameters
        pickup_location = params['pickup_location']
        dropoff_location = params['dropoff_location']
        pickup_date = params['pickup_date']
        dropoff_date = params['dropoff_date']
        car_type = params.get('car_type')
        
        # Validate dates
        try:
            pickup_dt = datetime.strptime(pickup_date, '%Y-%m-%d %H:%M:%S')
            dropoff_dt = datetime.strptime(dropoff_date, '%Y-%m-%d %H:%M:%S')
            
            if pickup_dt >= dropoff_dt:
                return {
                    'success': False,
                    'error': 'Drop-off date must be after pickup date',
                    'error_type': 'validation_error'
                }
            
            if pickup_dt < datetime.now():
                return {
                    'success': False,
                    'error': 'Pickup date cannot be in the past',
                    'error_type': 'validation_error'
                }
                
        except ValueError:
            return {
                'success': False,
                'error': 'Invalid date format. Use YYYY-MM-DD HH:MM:SS',
                'error_type': 'validation_error'
            }
        
        # Search cars
        search_results = car_rental_service.search_cars(
            pickup_location=pickup_location,
            dropoff_location=dropoff_location,
            pickup_date=pickup_date,
            dropoff_date=dropoff_date,
            car_type=car_type
        )
        
        if not search_results:
            return {
                'success': False,
                'error': 'No rental cars found for the specified criteria',
                'error_type': 'no_results'
            }
        
        # Calculate rental days
        rental_days = max(1, (dropoff_dt - pickup_dt).days)
        
        # Format car rental results
        formatted_results = {
            'success': True,
            'search_criteria': {
                'pickup_location': pickup_location,
                'dropoff_location': dropoff_location,
                'pickup_date': pickup_date,
                'dropoff_date': dropoff_date,
                'rental_days': rental_days,
                'car_type': car_type
            },
            'rental_cars': format_car_list(search_results, rental_days)
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
            'error': f'Car rental search failed: {str(e)}',
            'error_type': 'service_error'
        }

def handle_book_car(car_rental_service: CarRentalService, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle car rental booking requests
    
    Input parameters:
    - car_id: ID of the vehicle to book
    - pickup_location_id: ID of pickup location
    - dropoff_location_id: ID of drop-off location
    - pickup_date: Pickup date and time (YYYY-MM-DD HH:MM:SS)
    - dropoff_date: Drop-off date and time (YYYY-MM-DD HH:MM:SS)
    - driver_details: JSON string with driver information
    
    Output:
    - rental_confirmation: Booking details with booking ID and pickup instructions
    """
    
    try:
        # Validate required parameters
        required_params = ['car_id', 'pickup_location_id', 'dropoff_location_id', 'pickup_date', 'dropoff_date', 'driver_details']
        for param in required_params:
            if param not in params:
                return {
                    'success': False,
                    'error': f'Missing required parameter: {param}',
                    'error_type': 'validation_error'
                }
        
        # Extract parameters
        car_id = int(params['car_id'])
        pickup_location_id = int(params['pickup_location_id'])
        dropoff_location_id = int(params['dropoff_location_id'])
        pickup_date = params['pickup_date']
        dropoff_date = params['dropoff_date']
        
        # Parse driver details
        try:
            if isinstance(params['driver_details'], str):
                driver_details = json.loads(params['driver_details'])
            else:
                driver_details = params['driver_details']
        except json.JSONDecodeError:
            return {
                'success': False,
                'error': 'Invalid driver_details format. Must be valid JSON.',
                'error_type': 'validation_error'
            }
        
        # Validate driver license
        if 'license_number' not in driver_details:
            return {
                'success': False,
                'error': 'Driver license number is required',
                'error_type': 'validation_error'
            }
        
        # Default user ID for demo (in production, this would come from authentication)
        user_id = driver_details.get('user_id', 1)
        
        # Book the car
        booking_result = car_rental_service.book_car(
            user_id=user_id,
            vehicle_id=car_id,
            pickup_location_id=pickup_location_id,
            dropoff_location_id=dropoff_location_id,
            pickup_date=pickup_date,
            dropoff_date=dropoff_date,
            driver_details=driver_details
        )
        
        if not booking_result.get('success'):
            return booking_result
        
        # Format successful booking response
        formatted_result = {
            'success': True,
            'rental_confirmation': {
                'booking_id': booking_result['booking_id'],
                'booking_reference': booking_result['booking_reference'],
                'total_price': booking_result['total_price'],
                'currency': booking_result['currency'],
                'rental_days': booking_result['rental_days'],
                'pickup_date': pickup_date,
                'dropoff_date': dropoff_date,
                'status': 'CONFIRMED',
                'booking_date': datetime.now().isoformat()
            },
            'pickup_instructions': {
                'location': 'Pickup location details will be provided',
                'requirements': [
                    'Valid driver\'s license',
                    'Credit card in driver\'s name',
                    'Proof of insurance (if applicable)'
                ],
                'contact': 'Rental location phone number will be provided'
            },
            'message': f"Car rental successfully booked! Your booking reference is {booking_result['booking_reference']}"
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
            'error': f'Car rental booking failed: {str(e)}',
            'error_type': 'service_error'
        }

def handle_cancel_rental(car_rental_service: CarRentalService, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle car rental cancellation requests
    
    Input parameters:
    - booking_id: Booking reference or ID to cancel
    
    Output:
    - cancellation_status: Cancellation details with refund amount and cancellation fees
    """
    
    try:
        # Validate required parameters
        if 'booking_id' not in params:
            return {
                'success': False,
                'error': 'Missing required parameter: booking_id',
                'error_type': 'validation_error'
            }
        
        booking_id = params['booking_id']
        
        # For demo purposes, simulate cancellation logic
        # In a real implementation, this would update the database
        formatted_result = {
            'success': True,
            'cancellation_status': {
                'booking_id': booking_id,
                'status': 'CANCELLED',
                'refund_amount': 0.00,  # Demo: would calculate actual refund
                'cancellation_fees': 0.00,  # Demo: would calculate fees based on timing
                'currency': 'USD',
                'cancellation_date': datetime.now().isoformat(),
                'refund_timeline': '5-7 business days'
            },
            'message': f"Car rental booking {booking_id} has been successfully cancelled"
        }
        
        return formatted_result
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Car rental cancellation failed: {str(e)}',
            'error_type': 'service_error'
        }

def format_car_list(cars: List[Dict], rental_days: int) -> List[Dict]:
    """Format car rental list for response"""
    
    formatted_cars = []
    
    for car in cars:
        # Parse features JSON
        try:
            features = json.loads(car.get('features', '[]'))
        except:
            features = []
        
        # Calculate total price for rental period
        total_price = car['daily_rate'] * rental_days
        
        formatted_car = {
            'vehicle_id': car['vehicle_id'],
            'location_id': car['location_id'],
            'vehicle': {
                'make': car['make'],
                'model': car['model'],
                'year': car['year'],
                'color': car.get('color', 'Not specified'),
                'license_plate': car.get('license_plate', 'TBD')
            },
            'category': {
                'name': car['category_name'],
                'description': car['category_description'],
                'passenger_capacity': car['passenger_capacity'],
                'luggage_capacity': car['luggage_capacity']
            },
            'specifications': {
                'fuel_type': car['fuel_type'],
                'transmission': car['transmission'],
                'mileage': car.get('mileage', 0),
                'features': features
            },
            'rental_company': {
                'name': car['company_name'],
                'location': car['location_name'],
                'address': car['address'],
                'phone': car['phone']
            },
            'pricing': {
                'daily_rate': car['daily_rate'],
                'total_price': total_price,
                'currency': car['currency']
            },
            'rental_terms': {
                'mileage_policy': 'Unlimited mileage included',
                'fuel_policy': 'Return with same fuel level',
                'age_requirement': 'Minimum age 21',
                'insurance_required': True
            }
        }
        
        formatted_cars.append(formatted_car)
    
    return formatted_cars

# For local testing
if __name__ == "__main__":
    # Test event
    test_event = {
        'agent': 'car-rental-agent',
        'actionGroup': 'car-rental-operations',
        'function': 'search_cars',
        'parameters': [
            {'name': 'pickup_location', 'value': 'JFK Airport'},
            {'name': 'dropoff_location', 'value': 'JFK Airport'},
            {'name': 'pickup_date', 'value': '2024-02-15 10:00:00'},
            {'name': 'dropoff_date', 'value': '2024-02-18 10:00:00'}
        ],
        'sessionAttributes': {},
        'promptSessionAttributes': {}
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))