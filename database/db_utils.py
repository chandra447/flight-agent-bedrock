"""
Database utilities for Travel Booking Multi-Agent System
Provides connection management and common database operations
"""

import sqlite3
import json
import os
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Union
from contextlib import contextmanager

class DatabaseManager:
    """Database manager for SQLite operations"""
    
    def __init__(self, db_path: str = "database/travel_booking.db"):
        self.db_path = db_path
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """Ensure database exists, create if it doesn't"""
        if not os.path.exists(self.db_path):
            from init_database import create_database, insert_sample_data
            conn = create_database(self.db_path)
            insert_sample_data(conn)
            conn.close()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
        finally:
            conn.close()
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """Execute a SELECT query and return results as list of dictionaries"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute an INSERT/UPDATE/DELETE query and return affected rows"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount
    
    def execute_insert(self, query: str, params: tuple = ()) -> int:
        """Execute an INSERT query and return the last row ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid

class FlightService:
    """Service class for flight-related database operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def search_flights(self, origin: str, destination: str, departure_date: str, 
                      return_date: Optional[str] = None, passengers: int = 1) -> List[Dict]:
        """Search for available flights"""
        
        # Get airport IDs
        origin_query = "SELECT airport_id FROM airports WHERE airport_code = ? OR city LIKE ?"
        origin_result = self.db.execute_query(origin_query, (origin.upper(), f"%{origin}%"))
        
        destination_query = "SELECT airport_id FROM airports WHERE airport_code = ? OR city LIKE ?"
        destination_result = self.db.execute_query(destination_query, (destination.upper(), f"%{destination}%"))
        
        if not origin_result or not destination_result:
            return []
        
        origin_id = origin_result[0]['airport_id']
        destination_id = destination_result[0]['airport_id']
        
        # Search outbound flights
        outbound_query = """
        SELECT f.*, a.airline_name, a.airline_code,
               orig.airport_code as origin_code, orig.city as origin_city,
               dest.airport_code as destination_code, dest.city as destination_city
        FROM flights f
        JOIN airlines a ON f.airline_id = a.airline_id
        JOIN airports orig ON f.origin_airport_id = orig.airport_id
        JOIN airports dest ON f.destination_airport_id = dest.airport_id
        WHERE f.origin_airport_id = ? AND f.destination_airport_id = ?
        AND DATE(f.departure_time) = DATE(?)
        AND f.available_seats >= ?
        ORDER BY f.departure_time
        """
        
        outbound_flights = self.db.execute_query(
            outbound_query, 
            (origin_id, destination_id, departure_date, passengers)
        )
        
        # If return date specified, search return flights
        return_flights = []
        if return_date:
            return_query = """
            SELECT f.*, a.airline_name, a.airline_code,
                   orig.airport_code as origin_code, orig.city as origin_city,
                   dest.airport_code as destination_code, dest.city as destination_city
            FROM flights f
            JOIN airlines a ON f.airline_id = a.airline_id
            JOIN airports orig ON f.origin_airport_id = orig.airport_id
            JOIN airports dest ON f.destination_airport_id = dest.airport_id
            WHERE f.origin_airport_id = ? AND f.destination_airport_id = ?
            AND DATE(f.departure_time) = DATE(?)
            AND f.available_seats >= ?
            ORDER BY f.departure_time
            """
            
            return_flights = self.db.execute_query(
                return_query,
                (destination_id, origin_id, return_date, passengers)
            )
        
        return {
            'outbound_flights': outbound_flights,
            'return_flights': return_flights
        }
    
    def book_flight(self, user_id: int, flight_id: int, passenger_details: Dict) -> Dict:
        """Book a flight"""
        
        # Generate booking reference
        booking_ref = f"FL{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Get flight details
        flight_query = "SELECT * FROM flights WHERE flight_id = ?"
        flight = self.db.execute_query(flight_query, (flight_id,))
        
        if not flight:
            return {'success': False, 'error': 'Flight not found'}
        
        flight = flight[0]
        passenger_count = len(passenger_details.get('passengers', []))
        
        if flight['available_seats'] < passenger_count:
            return {'success': False, 'error': 'Insufficient seats available'}
        
        # Calculate total price
        total_price = flight['base_price'] * passenger_count
        
        # Insert booking
        booking_query = """
        INSERT INTO flight_bookings 
        (user_id, flight_id, booking_reference, passenger_count, total_price, 
         special_requests, booking_status)
        VALUES (?, ?, ?, ?, ?, ?, 'CONFIRMED')
        """
        
        booking_id = self.db.execute_insert(
            booking_query,
            (user_id, flight_id, booking_ref, passenger_count, total_price,
             json.dumps(passenger_details.get('special_requests', [])))
        )
        
        # Update available seats
        update_query = "UPDATE flights SET available_seats = available_seats - ? WHERE flight_id = ?"
        self.db.execute_update(update_query, (passenger_count, flight_id))
        
        return {
            'success': True,
            'booking_id': booking_id,
            'booking_reference': booking_ref,
            'total_price': total_price,
            'currency': flight['currency']
        }
    
    def cancel_flight(self, booking_reference: str) -> Dict:
        """Cancel a flight booking"""
        
        # Get booking details
        booking_query = """
        SELECT fb.*, f.available_seats, f.flight_id
        FROM flight_bookings fb
        JOIN flights f ON fb.flight_id = f.flight_id
        WHERE fb.booking_reference = ?
        """
        
        booking = self.db.execute_query(booking_query, (booking_reference,))
        
        if not booking:
            return {'success': False, 'error': 'Booking not found'}
        
        booking = booking[0]
        
        if booking['booking_status'] == 'CANCELLED':
            return {'success': False, 'error': 'Booking already cancelled'}
        
        # Update booking status
        cancel_query = "UPDATE flight_bookings SET booking_status = 'CANCELLED' WHERE booking_reference = ?"
        self.db.execute_update(cancel_query, (booking_reference,))
        
        # Restore available seats
        restore_query = "UPDATE flights SET available_seats = available_seats + ? WHERE flight_id = ?"
        self.db.execute_update(restore_query, (booking['passenger_count'], booking['flight_id']))
        
        return {
            'success': True,
            'refund_amount': booking['total_price'],
            'currency': booking['currency']
        }

class HotelService:
    """Service class for hotel-related database operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def search_hotels(self, location: str, check_in_date: str, check_out_date: str,
                     guests: int = 1, room_type: Optional[str] = None) -> List[Dict]:
        """Search for available hotels"""
        
        query = """
        SELECT h.*, rt.room_type_name, rt.room_description, rt.max_occupancy,
               rt.base_price_per_night, rt.bed_type, rt.room_size_sqm,
               rt.room_type_id
        FROM hotels h
        JOIN room_types rt ON h.hotel_id = rt.hotel_id
        WHERE (h.city LIKE ? OR h.country LIKE ?)
        AND rt.max_occupancy >= ?
        AND rt.active = 1
        AND h.active = 1
        """
        
        params = [f"%{location}%", f"%{location}%", guests]
        
        if room_type:
            query += " AND rt.room_type_name LIKE ?"
            params.append(f"%{room_type}%")
        
        query += " ORDER BY h.guest_rating DESC, rt.base_price_per_night ASC"
        
        return self.db.execute_query(query, tuple(params))
    
    def book_hotel(self, user_id: int, hotel_id: int, room_type_id: int, 
                   check_in_date: str, check_out_date: str, guest_details: Dict) -> Dict:
        """Book a hotel room"""
        
        # Generate booking reference
        booking_ref = f"HT{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Calculate nights and total price
        check_in = datetime.strptime(check_in_date, '%Y-%m-%d').date()
        check_out = datetime.strptime(check_out_date, '%Y-%m-%d').date()
        nights = (check_out - check_in).days
        
        # Get room type details
        room_query = "SELECT * FROM room_types WHERE room_type_id = ?"
        room = self.db.execute_query(room_query, (room_type_id,))
        
        if not room:
            return {'success': False, 'error': 'Room type not found'}
        
        room = room[0]
        guest_count = len(guest_details.get('guests', []))
        room_count = guest_details.get('room_count', 1)
        
        total_price = room['base_price_per_night'] * nights * room_count
        
        # Insert booking
        booking_query = """
        INSERT INTO hotel_bookings 
        (user_id, hotel_id, room_type_id, booking_reference, check_in_date, 
         check_out_date, guest_count, room_count, total_nights, price_per_night,
         total_price, special_requests, guest_names, booking_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'CONFIRMED')
        """
        
        booking_id = self.db.execute_insert(
            booking_query,
            (user_id, hotel_id, room_type_id, booking_ref, check_in_date,
             check_out_date, guest_count, room_count, nights, 
             room['base_price_per_night'], total_price,
             json.dumps(guest_details.get('special_requests', [])),
             json.dumps(guest_details.get('guests', [])))
        )
        
        return {
            'success': True,
            'booking_id': booking_id,
            'booking_reference': booking_ref,
            'total_price': total_price,
            'currency': room['currency'],
            'nights': nights
        }

class CarRentalService:
    """Service class for car rental-related database operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def search_cars(self, pickup_location: str, dropoff_location: str,
                   pickup_date: str, dropoff_date: str, 
                   car_type: Optional[str] = None) -> List[Dict]:
        """Search for available rental cars"""
        
        query = """
        SELECT av.*, vc.category_name, vc.category_description, vc.passenger_capacity,
               vc.luggage_capacity, crc.company_name, crl.location_name,
               crl.address, crl.phone
        FROM available_vehicles av
        JOIN vehicle_categories vc ON av.category_id = vc.category_id
        JOIN car_rental_companies crc ON av.company_id = crc.company_id
        JOIN car_rental_locations crl ON av.location_id = crl.location_id
        WHERE (crl.city LIKE ? OR crl.location_name LIKE ?)
        AND av.availability_status = 'AVAILABLE'
        """
        
        params = [f"%{pickup_location}%", f"%{pickup_location}%"]
        
        if car_type:
            query += " AND vc.category_name LIKE ?"
            params.append(f"%{car_type}%")
        
        query += " ORDER BY av.daily_rate ASC"
        
        return self.db.execute_query(query, tuple(params))
    
    def book_car(self, user_id: int, vehicle_id: int, pickup_location_id: int,
                dropoff_location_id: int, pickup_date: str, dropoff_date: str,
                driver_details: Dict) -> Dict:
        """Book a rental car"""
        
        # Generate booking reference
        booking_ref = f"CR{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Calculate rental days
        pickup = datetime.strptime(pickup_date, '%Y-%m-%d %H:%M:%S')
        dropoff = datetime.strptime(dropoff_date, '%Y-%m-%d %H:%M:%S')
        rental_days = max(1, (dropoff - pickup).days)
        
        # Get vehicle details
        vehicle_query = "SELECT * FROM available_vehicles WHERE vehicle_id = ?"
        vehicle = self.db.execute_query(vehicle_query, (vehicle_id,))
        
        if not vehicle:
            return {'success': False, 'error': 'Vehicle not found'}
        
        vehicle = vehicle[0]
        total_price = vehicle['daily_rate'] * rental_days
        
        # Insert booking
        booking_query = """
        INSERT INTO car_rental_bookings 
        (user_id, vehicle_id, pickup_location_id, dropoff_location_id,
         booking_reference, pickup_date, dropoff_date, rental_days,
         daily_rate, total_price, driver_license_number, booking_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'CONFIRMED')
        """
        
        booking_id = self.db.execute_insert(
            booking_query,
            (user_id, vehicle_id, pickup_location_id, dropoff_location_id,
             booking_ref, pickup_date, dropoff_date, rental_days,
             vehicle['daily_rate'], total_price, 
             driver_details.get('license_number'), )
        )
        
        # Update vehicle availability
        update_query = "UPDATE available_vehicles SET availability_status = 'RENTED' WHERE vehicle_id = ?"
        self.db.execute_update(update_query, (vehicle_id,))
        
        return {
            'success': True,
            'booking_id': booking_id,
            'booking_reference': booking_ref,
            'total_price': total_price,
            'currency': vehicle['currency'],
            'rental_days': rental_days
        }

class TravelPlannerService:
    """Service class for travel planning-related database operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def get_destination_info(self, destination: str, info_type: Optional[str] = None) -> Dict:
        """Get information about a destination"""
        
        # Get destination details
        dest_query = """
        SELECT * FROM destinations 
        WHERE destination_name LIKE ? OR country LIKE ?
        """
        
        destinations = self.db.execute_query(dest_query, (f"%{destination}%", f"%{destination}%"))
        
        if not destinations:
            return {'success': False, 'error': 'Destination not found'}
        
        dest = destinations[0]
        
        # Get attractions
        attractions_query = """
        SELECT * FROM attractions 
        WHERE destination_id = ? AND active = 1
        ORDER BY rating DESC
        """
        
        attractions = self.db.execute_query(attractions_query, (dest['destination_id'],))
        
        return {
            'success': True,
            'destination': dest,
            'attractions': attractions
        }
    
    def create_itinerary(self, user_id: int, destination: str, duration: int,
                        interests: List[str] = None, budget: Optional[str] = None) -> Dict:
        """Create a travel itinerary"""
        
        # Get destination info
        dest_info = self.get_destination_info(destination)
        
        if not dest_info['success']:
            return dest_info
        
        dest = dest_info['destination']
        attractions = dest_info['attractions']
        
        # Generate itinerary name
        itinerary_name = f"{destination} {duration}-Day Trip"
        
        # Create basic itinerary structure
        start_date = datetime.now().date() + timedelta(days=30)  # Default to 30 days from now
        end_date = start_date + timedelta(days=duration - 1)
        
        # Select top attractions based on interests and duration
        selected_attractions = attractions[:min(len(attractions), duration * 2)]
        
        # Create day-by-day itinerary
        itinerary_data = {
            'destination': dest['destination_name'],
            'duration': duration,
            'budget': budget,
            'interests': interests or [],
            'days': []
        }
        
        for day in range(duration):
            day_attractions = selected_attractions[day*2:(day+1)*2] if day*2 < len(selected_attractions) else []
            
            itinerary_data['days'].append({
                'day': day + 1,
                'date': (start_date + timedelta(days=day)).isoformat(),
                'attractions': day_attractions,
                'activities': [
                    {'time': '09:00', 'activity': 'Breakfast', 'location': 'Hotel'},
                    {'time': '10:00', 'activity': f"Visit {day_attractions[0]['attraction_name']}" if day_attractions else 'Free time'},
                    {'time': '14:00', 'activity': 'Lunch', 'location': 'Local restaurant'},
                    {'time': '15:30', 'activity': f"Explore {day_attractions[1]['attraction_name']}" if len(day_attractions) > 1 else 'Shopping/leisure'},
                    {'time': '19:00', 'activity': 'Dinner', 'location': 'Recommended restaurant'}
                ]
            })
        
        # Save itinerary to database
        itinerary_query = """
        INSERT INTO travel_itineraries 
        (user_id, destination_id, itinerary_name, start_date, end_date,
         duration_days, budget_amount, itinerary_data, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'DRAFT')
        """
        
        budget_amount = None
        if budget and budget.replace('$', '').replace(',', '').isdigit():
            budget_amount = float(budget.replace('$', '').replace(',', ''))
        
        itinerary_id = self.db.execute_insert(
            itinerary_query,
            (user_id, dest['destination_id'], itinerary_name, start_date,
             end_date, duration, budget_amount, json.dumps(itinerary_data))
        )
        
        return {
            'success': True,
            'itinerary_id': itinerary_id,
            'itinerary': itinerary_data
        }
    
    def get_travel_advisories(self, destination: str) -> Dict:
        """Get travel advisories for a destination"""
        
        # Get destination ID
        dest_query = """
        SELECT destination_id FROM destinations 
        WHERE destination_name LIKE ? OR country LIKE ?
        """
        
        destinations = self.db.execute_query(dest_query, (f"%{destination}%", f"%{destination}%"))
        
        if not destinations:
            return {'success': False, 'error': 'Destination not found'}
        
        dest_id = destinations[0]['destination_id']
        
        # Get active advisories
        advisories_query = """
        SELECT * FROM travel_advisories 
        WHERE destination_id = ? AND active = 1
        AND (expiry_date IS NULL OR expiry_date > DATE('now'))
        ORDER BY advisory_level DESC, last_updated DESC
        """
        
        advisories = self.db.execute_query(advisories_query, (dest_id,))
        
        return {
            'success': True,
            'advisories': advisories
        }

# Utility functions for date handling
def serialize_datetime(obj):
    """JSON serializer for datetime objects"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def format_currency(amount: float, currency: str = 'USD') -> str:
    """Format currency amount"""
    symbols = {'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥'}
    symbol = symbols.get(currency, currency)
    return f"{symbol}{amount:,.2f}"