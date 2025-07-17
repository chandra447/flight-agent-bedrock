#!/usr/bin/env python3
"""
Sample data insertion script for Travel Booking Multi-Agent System
Adds additional sample data for testing and demonstration
"""

import sqlite3
import json
from datetime import datetime, timedelta
from db_utils import DatabaseManager

def insert_additional_sample_data():
    """Insert additional sample data for comprehensive testing"""
    
    db = DatabaseManager()
    
    print("Inserting additional sample data...")
    
    # Additional sample users
    additional_users = [
        ('Alice', 'Wilson', 'alice.wilson@email.com', '+1-555-0789', '1988-07-20', 'US555666777', 'United States'),
        ('David', 'Brown', 'david.brown@email.com', '+44-20-7946-1234', '1975-12-03', 'UK987654321', 'United Kingdom'),
        ('Sophie', 'Martin', 'sophie.martin@email.com', '+33-1-42-86-1234', '1993-04-18', 'FR987654321', 'France'),
        ('Marco', 'Rossi', 'marco.rossi@email.com', '+39-06-1234-5678', '1987-08-25', 'IT123456789', 'Italy'),
        ('Yuki', 'Tanaka', 'yuki.tanaka@email.com', '+81-3-1234-5678', '1991-02-14', 'JP123456789', 'Japan')
    ]
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.executemany(
            "INSERT INTO users (first_name, last_name, email, phone, date_of_birth, passport_number, nationality) VALUES (?, ?, ?, ?, ?, ?, ?)",
            additional_users
        )
        
        # Additional destinations
        additional_destinations = [
            ('Rome', 'Italy', 'Europe', 'City', 'Eternal City with ancient history, art, and incredible cuisine', 'April to October', 15.5, 'EUR', 'Italian', 'Europe/Rome', 0, 4, 'Moderate', 41.9028, 12.4964),
            ('Barcelona', 'Spain', 'Europe', 'City', 'Vibrant city with unique architecture, beaches, and culture', 'May to September', 16.2, 'EUR', 'Spanish', 'Europe/Madrid', 0, 4, 'Moderate', 41.3851, 2.1734),
            ('Amsterdam', 'Netherlands', 'Europe', 'City', 'Charming city with canals, museums, and liberal culture', 'April to October', 9.8, 'EUR', 'Dutch', 'Europe/Amsterdam', 0, 5, 'Moderate', 52.3676, 4.9041),
            ('Sydney', 'Australia', 'Oceania', 'City', 'Harbor city with iconic opera house and beautiful beaches', 'September to March', 18.6, 'AUD', 'English', 'Australia/Sydney', 0, 5, 'Expensive', -33.8688, 151.2093),
            ('Bangkok', 'Thailand', 'Southeast Asia', 'City', 'Bustling metropolis with temples, street food, and nightlife', 'November to March', 28.0, 'THB', 'Thai', 'Asia/Bangkok', 0, 3, 'Budget', 13.7563, 100.5018),
            ('Santorini', 'Greece', 'Europe', 'Beach', 'Stunning island with white buildings, blue domes, and sunsets', 'April to October', 19.1, 'EUR', 'Greek', 'Europe/Athens', 0, 4, 'Expensive', 36.3932, 25.4615),
            ('Kyoto', 'Japan', 'Asia', 'City', 'Ancient capital with temples, gardens, and traditional culture', 'March to May, September to November', 15.8, 'JPY', 'Japanese', 'Asia/Tokyo', 0, 5, 'Moderate', 35.0116, 135.7681)
        ]
        
        cursor.executemany(
            "INSERT INTO destinations (destination_name, country, region, destination_type, description, best_time_to_visit, average_temperature_celsius, currency, language, timezone, visa_required, safety_rating, cost_level, latitude, longitude) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            additional_destinations
        )
        
        # Additional hotels for new destinations
        additional_hotels = [
            ('Hotel de Russie', 'Rocco Forte Hotels', 'Via del Babuino 9', 'Rome', 'Italy', '00187', '+39-06-328-881', 'reservations.derussie@roccofortehotels.com', 'www.roccofortehotels.com', 5, 9.1, 122, '["WiFi", "Spa", "Fitness Center", "Restaurant", "Bar", "Garden"]', 41.9109, 12.4818),
            ('Hotel Casa Fuster', 'Monument Hotels', 'Passeig de Gràcia 132', 'Barcelona', 'Spain', '08008', '+34-93-255-3000', 'casafuster@monumenthotels.com', 'www.hotelcasafuster.com', 5, 8.9, 105, '["WiFi", "Spa", "Restaurant", "Bar", "Rooftop Terrace"]', 41.3977, 2.1580),
            ('The Hoxton Amsterdam', 'The Hoxton', 'Herengracht 255', 'Amsterdam', 'Netherlands', '1016 BJ', '+31-20-888-5555', 'amsterdam@thehoxton.com', 'www.thehoxton.com', 4, 8.7, 111, '["WiFi", "Restaurant", "Bar", "Bike Rental"]', 52.3676, 4.8851),
            ('Park Hyatt Sydney', 'Hyatt Hotels', '7 Hickson Road', 'Sydney', 'Australia', '2000', '+61-2-9241-1234', 'sydney.park@hyatt.com', 'www.hyatt.com', 5, 9.3, 155, '["WiFi", "Spa", "Pool", "Fitness Center", "Restaurant", "Harbor View"]', -33.8590, 151.2104),
            ('Mandarin Oriental Bangkok', 'Mandarin Oriental', '48 Oriental Avenue', 'Bangkok', 'Thailand', '10500', '+66-2-659-9000', 'mobkk-reservations@mohg.com', 'www.mandarinoriental.com', 5, 9.0, 393, '["WiFi", "Spa", "Pool", "Fitness Center", "Restaurant", "River View"]', 13.7244, 100.5156)
        ]
        
        cursor.executemany(
            "INSERT INTO hotels (hotel_name, hotel_chain, address, city, country, postal_code, phone, email, website, star_rating, guest_rating, total_rooms, amenities, latitude, longitude) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            additional_hotels
        )
        
        # Get hotel IDs for room types
        hotel_ids = cursor.execute("SELECT hotel_id, hotel_name FROM hotels WHERE hotel_id > 8").fetchall()
        
        # Additional room types for new hotels
        additional_room_types = []
        for hotel_id, hotel_name in hotel_ids:
            if 'Russie' in hotel_name:
                additional_room_types.extend([
                    (hotel_id, 'Deluxe Room', 'Elegant room with garden or city view', 2, 'King', 32, '["WiFi", "TV", "Mini Bar", "Safe", "Marble Bathroom"]', 420.00, 'EUR', 60),
                    (hotel_id, 'Nijinsky Suite', 'Luxurious suite with terrace', 4, 'King + Sofa Bed', 75, '["WiFi", "TV", "Mini Bar", "Safe", "Terrace", "Butler Service"]', 980.00, 'EUR', 8)
                ])
            elif 'Casa Fuster' in hotel_name:
                additional_room_types.extend([
                    (hotel_id, 'Superior Room', 'Modern room with city view', 2, 'Queen', 28, '["WiFi", "TV", "Mini Bar", "Safe"]', 280.00, 'EUR', 70),
                    (hotel_id, 'Presidential Suite', 'Spectacular suite with terrace', 4, 'King + Sofa Bed', 90, '["WiFi", "TV", "Mini Bar", "Safe", "Terrace", "Living Area"]', 1200.00, 'EUR', 5)
                ])
            elif 'Hoxton' in hotel_name:
                additional_room_types.extend([
                    (hotel_id, 'Cosy Room', 'Compact stylish room', 2, 'Double', 18, '["WiFi", "TV", "Coffee Machine"]', 180.00, 'EUR', 80),
                    (hotel_id, 'Roomy Room', 'Spacious room with canal view', 2, 'King', 25, '["WiFi", "TV", "Coffee Machine", "Canal View"]', 250.00, 'EUR', 31)
                ])
            elif 'Park Hyatt Sydney' in hotel_name:
                additional_room_types.extend([
                    (hotel_id, 'Harbour View Room', 'Room with Sydney Harbour view', 2, 'King', 45, '["WiFi", "TV", "Mini Bar", "Safe", "Harbour View"]', 650.00, 'AUD', 100),
                    (hotel_id, 'Opera House Suite', 'Suite with Opera House view', 4, 'King + Sofa Bed', 85, '["WiFi", "TV", "Mini Bar", "Safe", "Opera House View", "Butler Service"]', 1500.00, 'AUD', 20)
                ])
            elif 'Mandarin Oriental' in hotel_name:
                additional_room_types.extend([
                    (hotel_id, 'Deluxe Room', 'Elegant room with river view', 2, 'King', 42, '["WiFi", "TV", "Mini Bar", "Safe", "River View"]', 8500.00, 'THB', 200),
                    (hotel_id, 'Oriental Suite', 'Luxurious suite with panoramic views', 4, 'King + Sofa Bed', 95, '["WiFi", "TV", "Mini Bar", "Safe", "Panoramic View", "Butler Service"]', 25000.00, 'THB', 35)
                ])
        
        cursor.executemany(
            "INSERT INTO room_types (hotel_id, room_type_name, room_description, max_occupancy, bed_type, room_size_sqm, amenities, base_price_per_night, currency, total_rooms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            additional_room_types
        )
        
        # Additional attractions for new destinations
        additional_attractions = [
            (8, 'Colosseum', 'Ancient Roman amphitheater', 'Piazza del Colosseo 1', '8:30 AM - 7:00 PM', 16.00, 'EUR', 4.6, 2.0, 'Year-round', 'www.coopculture.it', '+39-06-3996-7700', 41.8902, 12.4922),
            (8, 'Vatican Museums', 'Papal art collection including Sistine Chapel', 'Viale Vaticano', '8:00 AM - 6:00 PM', 20.00, 'EUR', 4.5, 3.0, 'Year-round', 'www.museivaticani.va', '+39-06-6988-4676', 41.9065, 12.4536),
            (9, 'Sagrada Familia', 'Gaudí\'s unfinished masterpiece basilica', 'Carrer de Mallorca 401', '9:00 AM - 8:00 PM', 26.00, 'EUR', 4.7, 2.0, 'Year-round', 'www.sagradafamilia.org', '+34-93-208-0414', 41.4036, 2.1744),
            (9, 'Park Güell', 'Gaudí\'s colorful mosaic park', 'Carrer d\'Olot 13', '8:00 AM - 9:30 PM', 10.00, 'EUR', 4.4, 2.5, 'Year-round', 'www.parkguell.cat', '+34-93-409-1831', 41.4145, 2.1527),
            (10, 'Anne Frank House', 'Historic house and museum', 'Prinsengracht 263-267', '9:00 AM - 10:00 PM', 14.00, 'EUR', 4.5, 1.5, 'Year-round', 'www.annefrank.org', '+31-20-556-7105', 52.3752, 4.8840),
            (10, 'Van Gogh Museum', 'World\'s largest Van Gogh collection', 'Museumplein 6', '9:00 AM - 5:00 PM', 20.00, 'EUR', 4.6, 2.0, 'Year-round', 'www.vangoghmuseum.nl', '+31-20-570-5200', 52.3584, 4.8811),
            (11, 'Sydney Opera House', 'Iconic performing arts venue', 'Bennelong Point', '9:00 AM - 8:30 PM', 43.00, 'AUD', 4.5, 1.0, 'Year-round', 'www.sydneyoperahouse.com', '+61-2-9250-7111', -33.8568, 151.2153),
            (11, 'Sydney Harbour Bridge', 'Famous steel arch bridge', 'Sydney Harbour Bridge', '24/7', 0.00, 'AUD', 4.6, 0.5, 'Year-round', 'www.bridgeclimb.com', '+61-2-8274-7777', -33.8523, 151.2108),
            (12, 'Grand Palace', 'Former royal residence complex', 'Na Phra Lan Rd', '8:30 AM - 3:30 PM', 500.00, 'THB', 4.3, 2.5, 'Year-round', 'www.royalgrandpalace.th', '+66-2-623-5500', 13.7500, 100.4915),
            (12, 'Wat Pho Temple', 'Temple with giant reclining Buddha', '2 Sanamchai Road', '8:00 AM - 6:30 PM', 200.00, 'THB', 4.4, 1.5, 'Year-round', 'www.watpho.com', '+66-2-226-0335', 13.7465, 100.4927)
        ]
        
        cursor.executemany(
            "INSERT INTO attractions (destination_id, attraction_name, attraction_type, description, address, opening_hours, admission_price, currency, rating, visit_duration_hours, best_time_to_visit, website, phone, latitude, longitude) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            additional_attractions
        )
        
        # Additional sample bookings for testing
        base_date = datetime.now() + timedelta(days=14)
        
        # Sample flight bookings
        sample_flight_bookings = [
            (1, 1, f'FL{datetime.now().strftime("%Y%m%d")}001', 2, 599.98, 'USD', 'CONFIRMED', '["12A", "12B"]', '[]'),
            (2, 5, f'FL{datetime.now().strftime("%Y%m%d")}002', 1, 649.99, 'USD', 'CONFIRMED', '["8F"]', '["Vegetarian meal"]'),
            (3, 10, f'FL{datetime.now().strftime("%Y%m%d")}003', 1, 299.99, 'USD', 'CONFIRMED', '["15C"]', '[]')
        ]
        
        cursor.executemany(
            "INSERT INTO flight_bookings (user_id, flight_id, booking_reference, passenger_count, total_price, currency, booking_status, seat_numbers, special_requests) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            sample_flight_bookings
        )
        
        # Sample hotel bookings
        check_in = base_date.strftime('%Y-%m-%d')
        check_out = (base_date + timedelta(days=3)).strftime('%Y-%m-%d')
        
        sample_hotel_bookings = [
            (1, 1, 1, f'HT{datetime.now().strftime("%Y%m%d")}001', check_in, check_out, 2, 1, 3, 450.00, 1350.00, 'USD', 'CONFIRMED', '[]', '[{"name": "John Doe", "age": 35}, {"name": "Jane Doe", "age": 32}]'),
            (2, 6, 7, f'HT{datetime.now().strftime("%Y%m%d")}002', check_in, check_out, 1, 1, 3, 89.00, 267.00, 'USD', 'CONFIRMED', '["Late checkout"]', '[{"name": "Jane Smith", "age": 33}]')
        ]
        
        cursor.executemany(
            "INSERT INTO hotel_bookings (user_id, hotel_id, room_type_id, booking_reference, check_in_date, check_out_date, guest_count, room_count, total_nights, price_per_night, total_price, currency, booking_status, special_requests, guest_names) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            sample_hotel_bookings
        )
        
        # Sample travel advisories
        sample_advisories = [
            (1, 'HEALTH', 'LOW', 'COVID-19 Guidelines', 'Follow local health guidelines and mask requirements in public transportation', '2024-01-01', None, 'CDC', 1),
            (3, 'SAFETY', 'LOW', 'General Safety', 'London is generally safe for tourists. Be aware of pickpockets in tourist areas', '2024-01-01', None, 'UK Government', 1),
            (12, 'HEALTH', 'MODERATE', 'Tropical Disease Prevention', 'Consider vaccination for hepatitis A and typhoid. Use mosquito repellent', '2024-01-01', '2024-12-31', 'WHO', 1),
            (7, 'VISA', 'HIGH', 'Visa Requirements', 'US citizens require visa for UAE. Apply at least 2 weeks in advance', '2024-01-01', None, 'UAE Embassy', 1)
        ]
        
        cursor.executemany(
            "INSERT INTO travel_advisories (destination_id, advisory_type, advisory_level, title, description, effective_date, expiry_date, source, active) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            sample_advisories
        )
        
        conn.commit()
        print("Additional sample data inserted successfully!")

def main():
    """Main function to insert additional sample data"""
    print("Inserting additional sample data for Travel Booking Multi-Agent System...")
    insert_additional_sample_data()
    print("Additional sample data insertion completed!")

if __name__ == "__main__":
    main()