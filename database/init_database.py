#!/usr/bin/env python3
"""
Travel Booking Multi-Agent System Database Initialization
Creates and initializes the SQLite database with schema and sample data
"""

import sqlite3
import os
import json
from datetime import datetime, timedelta
from pathlib import Path

def create_database(db_path="database/travel_booking.db"):
    """Create the database and initialize schema"""
    
    # Ensure database directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Connect to database (creates if doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Read and execute schema
    schema_path = Path(__file__).parent / "schema.sql"
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    
    # Execute schema creation
    cursor.executescript(schema_sql)
    
    print(f"Database created successfully at: {db_path}")
    return conn

def insert_sample_data(conn):
    """Insert sample data for testing and development"""
    cursor = conn.cursor()
    
    # Sample Airlines
    airlines_data = [
        ('AA', 'American Airlines', 'United States'),
        ('DL', 'Delta Air Lines', 'United States'),
        ('UA', 'United Airlines', 'United States'),
        ('BA', 'British Airways', 'United Kingdom'),
        ('LH', 'Lufthansa', 'Germany'),
        ('AF', 'Air France', 'France'),
        ('KL', 'KLM Royal Dutch Airlines', 'Netherlands'),
        ('EK', 'Emirates', 'United Arab Emirates'),
        ('QR', 'Qatar Airways', 'Qatar'),
        ('SQ', 'Singapore Airlines', 'Singapore')
    ]
    
    cursor.executemany(
        "INSERT INTO airlines (airline_code, airline_name, country) VALUES (?, ?, ?)",
        airlines_data
    )
    
    # Sample Airports
    airports_data = [
        ('JFK', 'John F. Kennedy International Airport', 'New York', 'United States', 'America/New_York', 40.6413, -73.7781),
        ('LAX', 'Los Angeles International Airport', 'Los Angeles', 'United States', 'America/Los_Angeles', 33.9425, -118.4081),
        ('LHR', 'London Heathrow Airport', 'London', 'United Kingdom', 'Europe/London', 51.4700, -0.4543),
        ('CDG', 'Charles de Gaulle Airport', 'Paris', 'France', 'Europe/Paris', 49.0097, 2.5479),
        ('FRA', 'Frankfurt Airport', 'Frankfurt', 'Germany', 'Europe/Berlin', 50.0379, 8.5622),
        ('AMS', 'Amsterdam Airport Schiphol', 'Amsterdam', 'Netherlands', 'Europe/Amsterdam', 52.3105, 4.7683),
        ('DXB', 'Dubai International Airport', 'Dubai', 'United Arab Emirates', 'Asia/Dubai', 25.2532, 55.3657),
        ('DOH', 'Hamad International Airport', 'Doha', 'Qatar', 'Asia/Qatar', 25.2731, 51.6080),
        ('SIN', 'Singapore Changi Airport', 'Singapore', 'Singapore', 'Asia/Singapore', 1.3644, 103.9915),
        ('NRT', 'Narita International Airport', 'Tokyo', 'Japan', 'Asia/Tokyo', 35.7720, 140.3929)
    ]
    
    cursor.executemany(
        "INSERT INTO airports (airport_code, airport_name, city, country, timezone, latitude, longitude) VALUES (?, ?, ?, ?, ?, ?, ?)",
        airports_data
    )
    
    # Sample Flights
    base_date = datetime.now() + timedelta(days=7)  # Flights starting next week
    flights_data = []
    
    # Generate sample flights for the next 30 days
    for day_offset in range(30):
        flight_date = base_date + timedelta(days=day_offset)
        
        # JFK to LAX flights
        flights_data.extend([
            (f'AA{100 + day_offset}', 1, 1, 2, flight_date.replace(hour=8, minute=0), flight_date.replace(hour=11, minute=30), 'Boeing 737', 180, 150, 299.99),
            (f'DL{200 + day_offset}', 2, 1, 2, flight_date.replace(hour=14, minute=0), flight_date.replace(hour=17, minute=30), 'Airbus A320', 160, 120, 349.99),
            (f'UA{300 + day_offset}', 3, 1, 2, flight_date.replace(hour=20, minute=0), flight_date.replace(hour=23, minute=30), 'Boeing 757', 200, 180, 279.99),
        ])
        
        # JFK to LHR flights
        flights_data.extend([
            (f'BA{400 + day_offset}', 4, 1, 3, flight_date.replace(hour=22, minute=0), (flight_date + timedelta(days=1)).replace(hour=10, minute=0), 'Boeing 777', 300, 250, 599.99),
            (f'AA{500 + day_offset}', 1, 1, 3, flight_date.replace(hour=18, minute=0), (flight_date + timedelta(days=1)).replace(hour=6, minute=0), 'Boeing 787', 280, 220, 649.99),
        ])
    
    cursor.executemany(
        "INSERT INTO flights (flight_number, airline_id, origin_airport_id, destination_airport_id, departure_time, arrival_time, aircraft_type, total_seats, available_seats, base_price) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        flights_data
    )
    
    # Sample Hotels
    hotels_data = [
        ('The Plaza Hotel', 'Luxury Collection', '768 5th Ave', 'New York', 'United States', '10019', '+1-212-759-3000', 'reservations@plaza.com', 'www.theplaza.com', 5, 8.5, 282, '["WiFi", "Spa", "Fitness Center", "Restaurant", "Room Service", "Concierge"]', 40.7648, -73.9754),
        ('The Beverly Hills Hotel', 'Dorchester Collection', '9641 Sunset Blvd', 'Los Angeles', 'United States', '90210', '+1-310-276-2251', 'info@beverlyhillshotel.com', 'www.beverlyhillshotel.com', 5, 9.0, 210, '["WiFi", "Pool", "Spa", "Fitness Center", "Restaurant", "Valet Parking"]', 34.0901, -118.4065),
        ('The Savoy', 'Fairmont Hotels', 'Strand', 'London', 'United Kingdom', 'WC2R 0EU', '+44-20-7836-4343', 'info@savoy.com', 'www.savoy.com', 5, 9.2, 267, '["WiFi", "Spa", "Fitness Center", "Restaurant", "Bar", "Concierge"]', 51.5104, -0.1201),
        ('Hotel Plaza Athénée', 'Dorchester Collection', '25 Avenue Montaigne', 'Paris', 'France', '75008', '+33-1-53-67-66-65', 'info@plaza-athenee-paris.com', 'www.plaza-athenee-paris.com', 5, 8.8, 154, '["WiFi", "Spa", "Fitness Center", "Restaurant", "Bar", "Room Service"]', 48.8656, 2.3047),
        ('Hotel Adlon Kempinski', 'Kempinski Hotels', 'Unter den Linden 77', 'Berlin', 'Germany', '10117', '+49-30-2261-0', 'hotel.adlon@kempinski.com', 'www.kempinski.com', 5, 8.7, 382, '["WiFi", "Spa", "Pool", "Fitness Center", "Restaurant", "Bar"]', 52.5163, 13.3777),
        ('Budget Inn Downtown', 'Independent', '123 Main St', 'New York', 'United States', '10001', '+1-212-555-0123', 'info@budgetinn.com', 'www.budgetinn.com', 2, 6.5, 120, '["WiFi", "24h Front Desk"]', 40.7505, -73.9934),
        ('City Center Hotel', 'Independent', '456 Hollywood Blvd', 'Los Angeles', 'United States', '90028', '+1-323-555-0456', 'reservations@citycenter.com', 'www.citycenterhotel.com', 3, 7.2, 85, '["WiFi", "Parking", "Restaurant"]', 34.1016, -118.3295),
        ('London Bridge Hotel', 'Independent', '8-18 London Bridge St', 'London', 'United Kingdom', 'SE1 9SG', '+44-20-7855-2200', 'info@londonbridgehotel.com', 'www.londonbridgehotel.com', 4, 8.1, 138, '["WiFi", "Restaurant", "Bar", "Fitness Center"]', 51.5045, -0.0865)
    ]
    
    cursor.executemany(
        "INSERT INTO hotels (hotel_name, hotel_chain, address, city, country, postal_code, phone, email, website, star_rating, guest_rating, total_rooms, amenities, latitude, longitude) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        hotels_data
    )
    
    # Sample Room Types
    room_types_data = [
        (1, 'Standard King Room', 'Elegant room with king bed and city view', 2, 'King', 35, '["WiFi", "TV", "Mini Bar", "Safe"]', 450.00, 1, 50),
        (1, 'Plaza Suite', 'Luxurious suite with separate living area', 4, 'King + Sofa Bed', 65, '["WiFi", "TV", "Mini Bar", "Safe", "Living Area", "Butler Service"]', 850.00, 1, 25),
        (2, 'Deluxe Room', 'Spacious room with garden view', 2, 'King', 40, '["WiFi", "TV", "Mini Bar", "Balcony"]', 380.00, 1, 80),
        (2, 'Bungalow Suite', 'Private bungalow with pool access', 2, 'King', 55, '["WiFi", "TV", "Mini Bar", "Private Pool", "Patio"]', 750.00, 1, 30),
        (3, 'Superior Room', 'Classic room with Thames view', 2, 'Queen', 30, '["WiFi", "TV", "Tea/Coffee", "River View"]', 320.00, 1, 120),
        (3, 'Royal Suite', 'Opulent suite with panoramic views', 4, 'King + Sofa Bed', 80, '["WiFi", "TV", "Mini Bar", "Butler Service", "Panoramic View"]', 1200.00, 1, 15),
        (6, 'Economy Room', 'Basic comfortable room', 2, 'Double', 20, '["WiFi", "TV"]', 89.00, 1, 80),
        (7, 'Standard Room', 'Comfortable room in city center', 2, 'Queen', 25, '["WiFi", "TV", "AC"]', 125.00, 1, 60),
        (8, 'Business Room', 'Modern room with work desk', 2, 'King', 28, '["WiFi", "TV", "Work Desk", "Coffee Machine"]', 180.00, 1, 90)
    ]
    
    cursor.executemany(
        "INSERT INTO room_types (hotel_id, room_type_name, room_description, max_occupancy, bed_type, room_size_sqm, amenities, base_price_per_night, currency, total_rooms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        room_types_data
    )
    
    # Sample Car Rental Companies
    car_companies_data = [
        ('Hertz', 'HTZ', 'www.hertz.com', '+1-800-654-3131', 'reservations@hertz.com'),
        ('Avis', 'AVS', 'www.avis.com', '+1-800-331-1212', 'reservations@avis.com'),
        ('Enterprise', 'ENT', 'www.enterprise.com', '+1-800-261-7331', 'reservations@enterprise.com'),
        ('Budget', 'BDG', 'www.budget.com', '+1-800-527-0700', 'reservations@budget.com'),
        ('Alamo', 'ALM', 'www.alamo.com', '+1-844-357-5138', 'reservations@alamo.com')
    ]
    
    cursor.executemany(
        "INSERT INTO car_rental_companies (company_name, company_code, website, phone, email) VALUES (?, ?, ?, ?, ?)",
        car_companies_data
    )
    
    # Sample Car Rental Locations
    locations_data = [
        (1, 'JFK Airport', 'AIRPORT', 'JFK International Airport Terminal 1', 'New York', 'United States', 'JFK', '+1-718-244-9500', '24/7', 40.6413, -73.7781),
        (1, 'Manhattan Downtown', 'CITY_CENTER', '350 W 31st St', 'New York', 'United States', None, '+1-212-563-3500', '7:00-19:00', 40.7505, -73.9934),
        (2, 'LAX Airport', 'AIRPORT', 'Los Angeles International Airport', 'Los Angeles', 'United States', 'LAX', '+1-310-568-5000', '24/7', 33.9425, -118.4081),
        (2, 'Hollywood', 'CITY_CENTER', '6801 Hollywood Blvd', 'Los Angeles', 'United States', None, '+1-323-467-8900', '8:00-18:00', 34.1016, -118.3295),
        (3, 'LHR Airport', 'AIRPORT', 'Heathrow Airport Terminal 2', 'London', 'United Kingdom', 'LHR', '+44-20-8897-2100', '24/7', 51.4700, -0.4543),
        (3, 'London City', 'CITY_CENTER', '207 Vauxhall Bridge Rd', 'London', 'United Kingdom', None, '+44-20-7834-6777', '8:00-18:00', 51.4893, -0.1334)
    ]
    
    cursor.executemany(
        "INSERT INTO car_rental_locations (company_id, location_name, location_type, address, city, country, airport_code, phone, operating_hours, latitude, longitude) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        locations_data
    )
    
    # Sample Vehicle Categories
    categories_data = [
        ('Economy', 'Small, fuel-efficient cars perfect for city driving', 'Nissan Versa, Chevrolet Spark, Mitsubishi Mirage', 4, 2, 'Both', 'Gasoline'),
        ('Compact', 'Comfortable cars with good fuel economy', 'Nissan Sentra, Ford Focus, Volkswagen Jetta', 5, 3, 'Both', 'Gasoline'),
        ('Mid-size', 'Spacious cars ideal for longer trips', 'Toyota Camry, Nissan Altima, Ford Fusion', 5, 4, 'Automatic', 'Gasoline'),
        ('Full-size', 'Large, comfortable cars with ample space', 'Chevrolet Impala, Ford Taurus, Nissan Maxima', 5, 4, 'Automatic', 'Gasoline'),
        ('SUV', 'Sport utility vehicles for versatile driving', 'Ford Escape, Jeep Cherokee, Toyota RAV4', 7, 6, 'Automatic', 'Gasoline'),
        ('Luxury', 'Premium vehicles with high-end features', 'BMW 3 Series, Mercedes C-Class, Audi A4', 5, 3, 'Automatic', 'Gasoline')
    ]
    
    cursor.executemany(
        "INSERT INTO vehicle_categories (category_name, category_description, typical_models, passenger_capacity, luggage_capacity, transmission_type, fuel_type) VALUES (?, ?, ?, ?, ?, ?, ?)",
        categories_data
    )
    
    # Sample Available Vehicles
    vehicles_data = [
        (1, 1, 1, 'Nissan', 'Versa', 2023, 'NY123ABC', 'White', 15000, 'Gasoline', 'Automatic', '["AC", "Radio", "USB Port"]', 35.99),
        (1, 1, 2, 'Ford', 'Focus', 2023, 'NY456DEF', 'Blue', 12000, 'Gasoline', 'Automatic', '["AC", "Radio", "Bluetooth", "USB Port"]', 42.99),
        (1, 1, 3, 'Toyota', 'Camry', 2023, 'NY789GHI', 'Silver', 8000, 'Gasoline', 'Automatic', '["AC", "Radio", "Bluetooth", "USB Port", "Backup Camera"]', 55.99),
        (1, 1, 5, 'Ford', 'Escape', 2023, 'NY012JKL', 'Black', 10000, 'Gasoline', 'Automatic', '["AC", "Radio", "Bluetooth", "USB Port", "AWD", "Backup Camera"]', 75.99),
        (2, 3, 1, 'Chevrolet', 'Spark', 2023, 'CA123MNO', 'Red', 18000, 'Gasoline', 'Manual', '["AC", "Radio"]', 32.99),
        (2, 3, 2, 'Volkswagen', 'Jetta', 2023, 'CA456PQR', 'Gray', 14000, 'Gasoline', 'Automatic', '["AC", "Radio", "Bluetooth", "USB Port"]', 45.99),
        (3, 5, 2, 'Ford', 'Focus', 2023, 'UK123STU', 'White', 16000, 'Gasoline', 'Manual', '["AC", "Radio", "Bluetooth"]', 38.99),
        (3, 5, 6, 'BMW', '3 Series', 2023, 'UK456VWX', 'Black', 5000, 'Gasoline', 'Automatic', '["AC", "Radio", "Bluetooth", "GPS", "Leather Seats", "Sunroof"]', 125.99)
    ]
    
    cursor.executemany(
        "INSERT INTO available_vehicles (company_id, location_id, category_id, make, model, year, license_plate, color, mileage, fuel_type, transmission, features, daily_rate) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        vehicles_data
    )
    
    # Sample Destinations
    destinations_data = [
        ('New York City', 'United States', 'Northeast', 'City', 'The city that never sleeps, famous for its skyline, Broadway shows, and cultural diversity', 'Year-round, best in spring and fall', 12.5, 'USD', 'English', 'America/New_York', 0, 4, 'Expensive', 40.7128, -74.0060),
        ('Los Angeles', 'United States', 'West Coast', 'City', 'Entertainment capital with Hollywood, beaches, and perfect weather', 'Year-round, best in spring and fall', 18.3, 'USD', 'English', 'America/Los_Angeles', 0, 4, 'Expensive', 34.0522, -118.2437),
        ('London', 'United Kingdom', 'Europe', 'City', 'Historic city with royal palaces, museums, and rich cultural heritage', 'May to September', 10.5, 'GBP', 'English', 'Europe/London', 0, 4, 'Expensive', 51.5074, -0.1278),
        ('Paris', 'France', 'Europe', 'City', 'City of Light known for art, fashion, gastronomy, and romance', 'April to October', 11.2, 'EUR', 'French', 'Europe/Paris', 0, 4, 'Expensive', 48.8566, 2.3522),
        ('Tokyo', 'Japan', 'Asia', 'City', 'Modern metropolis blending traditional culture with cutting-edge technology', 'March to May, September to November', 15.4, 'JPY', 'Japanese', 'Asia/Tokyo', 0, 5, 'Expensive', 35.6762, 139.6503),
        ('Bali', 'Indonesia', 'Southeast Asia', 'Beach', 'Tropical paradise with beautiful beaches, temples, and rich culture', 'April to October', 26.1, 'IDR', 'Indonesian', 'Asia/Makassar', 0, 4, 'Moderate', -8.3405, 115.0920),
        ('Dubai', 'United Arab Emirates', 'Middle East', 'City', 'Luxury destination with modern architecture, shopping, and desert adventures', 'November to March', 27.1, 'AED', 'Arabic', 'Asia/Dubai', 0, 4, 'Luxury', 25.2048, 55.2708)
    ]
    
    cursor.executemany(
        "INSERT INTO destinations (destination_name, country, region, destination_type, description, best_time_to_visit, average_temperature_celsius, currency, language, timezone, visa_required, safety_rating, cost_level, latitude, longitude) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        destinations_data
    )
    
    # Sample Attractions
    attractions_data = [
        (1, 'Statue of Liberty', 'Monument', 'Iconic symbol of freedom and democracy', 'Liberty Island', '9:30 AM - 5:00 PM', 25.00, 'USD', 4.5, 3.0, 'Year-round', 'www.nps.gov/stli', '+1-212-363-3200', 40.6892, -74.0445),
        (1, 'Central Park', 'Park', 'Large public park in Manhattan', '59th to 110th Street', '6:00 AM - 1:00 AM', 0.00, 'USD', 4.7, 2.0, 'Year-round', 'www.centralparknyc.org', '+1-212-310-6600', 40.7829, -73.9654),
        (1, 'Empire State Building', 'Building', 'Art Deco skyscraper with observation decks', '350 5th Ave', '8:00 AM - 2:00 AM', 42.00, 'USD', 4.3, 1.5, 'Year-round', 'www.esbnyc.com', '+1-212-736-3100', 40.7484, -73.9857),
        (2, 'Hollywood Walk of Fame', 'Attraction', 'Sidewalk with stars honoring entertainment celebrities', 'Hollywood Blvd', '24/7', 0.00, 'USD', 4.0, 1.0, 'Year-round', 'www.walkoffame.com', None, 34.1016, -118.3295),
        (2, 'Santa Monica Pier', 'Pier', 'Amusement park on a pier with rides and games', '200 Santa Monica Pier', '11:00 AM - 11:00 PM', 15.00, 'USD', 4.2, 3.0, 'Year-round', 'www.santamonicapier.org', '+1-310-458-8900', 34.0082, -118.4987),
        (3, 'Tower of London', 'Castle', 'Historic castle and home to the Crown Jewels', 'St Katharine\'s & Wapping', '9:00 AM - 5:30 PM', 29.90, 'GBP', 4.4, 3.0, 'Year-round', 'www.hrp.org.uk', '+44-20-3166-6000', 51.5081, -0.0759),
        (3, 'British Museum', 'Museum', 'World-famous museum with artifacts from around the globe', 'Great Russell St', '10:00 AM - 5:00 PM', 0.00, 'GBP', 4.6, 2.5, 'Year-round', 'www.britishmuseum.org', '+44-20-7323-8299', 51.5194, -0.1270),
        (4, 'Eiffel Tower', 'Monument', 'Iconic iron lattice tower and symbol of Paris', 'Champ de Mars', '9:30 AM - 11:45 PM', 29.40, 'EUR', 4.5, 2.0, 'Year-round', 'www.toureiffel.paris', '+33-8-92-70-12-39', 48.8584, 2.2945),
        (4, 'Louvre Museum', 'Museum', 'World\'s largest art museum', 'Rue de Rivoli', '9:00 AM - 6:00 PM', 17.00, 'EUR', 4.7, 4.0, 'Year-round', 'www.louvre.fr', '+33-1-40-20-50-50', 48.8606, 2.3376)
    ]
    
    cursor.executemany(
        "INSERT INTO attractions (destination_id, attraction_name, attraction_type, description, address, opening_hours, admission_price, currency, rating, visit_duration_hours, best_time_to_visit, website, phone, latitude, longitude) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        attractions_data
    )
    
    # Sample Users for testing
    users_data = [
        ('John', 'Doe', 'john.doe@email.com', '+1-555-0123', '1985-06-15', 'US123456789', 'United States'),
        ('Jane', 'Smith', 'jane.smith@email.com', '+1-555-0456', '1990-03-22', 'US987654321', 'United States'),
        ('Robert', 'Johnson', 'robert.johnson@email.com', '+44-20-7946-0958', '1978-11-08', 'UK123456789', 'United Kingdom'),
        ('Maria', 'Garcia', 'maria.garcia@email.com', '+33-1-42-86-83-26', '1992-09-14', 'FR123456789', 'France')
    ]
    
    cursor.executemany(
        "INSERT INTO users (first_name, last_name, email, phone, date_of_birth, passport_number, nationality) VALUES (?, ?, ?, ?, ?, ?, ?)",
        users_data
    )
    
    conn.commit()
    print("Sample data inserted successfully!")

def main():
    """Main function to initialize the database"""
    print("Initializing Travel Booking Multi-Agent System Database...")
    
    # Create database and schema
    conn = create_database()
    
    # Insert sample data
    insert_sample_data(conn)
    
    # Close connection
    conn.close()
    
    print("Database initialization completed successfully!")
    print("Database location: database/travel_booking.db")
    print("You can now use this database with the Lambda functions.")

if __name__ == "__main__":
    main()