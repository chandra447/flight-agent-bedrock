-- Travel Booking Multi-Agent System Database Schema
-- SQLite Database for storing travel booking information

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Users table for customer information
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    date_of_birth DATE,
    passport_number TEXT,
    nationality TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Airlines table for flight carriers
CREATE TABLE IF NOT EXISTS airlines (
    airline_id INTEGER PRIMARY KEY AUTOINCREMENT,
    airline_code TEXT UNIQUE NOT NULL,
    airline_name TEXT NOT NULL,
    country TEXT,
    active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Airports table for flight locations
CREATE TABLE IF NOT EXISTS airports (
    airport_id INTEGER PRIMARY KEY AUTOINCREMENT,
    airport_code TEXT UNIQUE NOT NULL,
    airport_name TEXT NOT NULL,
    city TEXT NOT NULL,
    country TEXT NOT NULL,
    timezone TEXT,
    latitude REAL,
    longitude REAL,
    active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Flights table for available flights
CREATE TABLE IF NOT EXISTS flights (
    flight_id INTEGER PRIMARY KEY AUTOINCREMENT,
    flight_number TEXT NOT NULL,
    airline_id INTEGER NOT NULL,
    origin_airport_id INTEGER NOT NULL,
    destination_airport_id INTEGER NOT NULL,
    departure_time TIMESTAMP NOT NULL,
    arrival_time TIMESTAMP NOT NULL,
    aircraft_type TEXT,
    total_seats INTEGER DEFAULT 0,
    available_seats INTEGER DEFAULT 0,
    base_price DECIMAL(10,2) NOT NULL,
    currency TEXT DEFAULT 'USD',
    flight_status TEXT DEFAULT 'SCHEDULED',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (airline_id) REFERENCES airlines(airline_id),
    FOREIGN KEY (origin_airport_id) REFERENCES airports(airport_id),
    FOREIGN KEY (destination_airport_id) REFERENCES airports(airport_id)
);

-- Flight bookings table
CREATE TABLE IF NOT EXISTS flight_bookings (
    booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    flight_id INTEGER NOT NULL,
    booking_reference TEXT UNIQUE NOT NULL,
    passenger_count INTEGER NOT NULL DEFAULT 1,
    total_price DECIMAL(10,2) NOT NULL,
    currency TEXT DEFAULT 'USD',
    booking_status TEXT DEFAULT 'CONFIRMED',
    seat_numbers TEXT, -- JSON array of seat assignments
    special_requests TEXT,
    booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (flight_id) REFERENCES flights(flight_id)
);

-- Hotels table for accommodation properties
CREATE TABLE IF NOT EXISTS hotels (
    hotel_id INTEGER PRIMARY KEY AUTOINCREMENT,
    hotel_name TEXT NOT NULL,
    hotel_chain TEXT,
    address TEXT NOT NULL,
    city TEXT NOT NULL,
    country TEXT NOT NULL,
    postal_code TEXT,
    phone TEXT,
    email TEXT,
    website TEXT,
    star_rating INTEGER CHECK (star_rating >= 1 AND star_rating <= 5),
    guest_rating DECIMAL(3,1) CHECK (guest_rating >= 0 AND guest_rating <= 10),
    total_rooms INTEGER DEFAULT 0,
    amenities TEXT, -- JSON array of amenities
    check_in_time TIME DEFAULT '15:00',
    check_out_time TIME DEFAULT '11:00',
    latitude REAL,
    longitude REAL,
    active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Room types table for hotel room categories
CREATE TABLE IF NOT EXISTS room_types (
    room_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
    hotel_id INTEGER NOT NULL,
    room_type_name TEXT NOT NULL,
    room_description TEXT,
    max_occupancy INTEGER NOT NULL DEFAULT 2,
    bed_type TEXT,
    room_size_sqm INTEGER,
    amenities TEXT, -- JSON array of room-specific amenities
    base_price_per_night DECIMAL(10,2) NOT NULL,
    currency TEXT DEFAULT 'USD',
    total_rooms INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hotel_id) REFERENCES hotels(hotel_id)
);

-- Hotel bookings table
CREATE TABLE IF NOT EXISTS hotel_bookings (
    booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    hotel_id INTEGER NOT NULL,
    room_type_id INTEGER NOT NULL,
    booking_reference TEXT UNIQUE NOT NULL,
    check_in_date DATE NOT NULL,
    check_out_date DATE NOT NULL,
    guest_count INTEGER NOT NULL DEFAULT 1,
    room_count INTEGER NOT NULL DEFAULT 1,
    total_nights INTEGER NOT NULL,
    price_per_night DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    currency TEXT DEFAULT 'USD',
    booking_status TEXT DEFAULT 'CONFIRMED',
    special_requests TEXT,
    guest_names TEXT, -- JSON array of guest information
    booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (hotel_id) REFERENCES hotels(hotel_id),
    FOREIGN KEY (room_type_id) REFERENCES room_types(room_type_id)
);

-- Car rental companies table
CREATE TABLE IF NOT EXISTS car_rental_companies (
    company_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    company_code TEXT UNIQUE NOT NULL,
    website TEXT,
    phone TEXT,
    email TEXT,
    active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Car rental locations table
CREATE TABLE IF NOT EXISTS car_rental_locations (
    location_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    location_name TEXT NOT NULL,
    location_type TEXT NOT NULL, -- AIRPORT, CITY_CENTER, HOTEL, etc.
    address TEXT NOT NULL,
    city TEXT NOT NULL,
    country TEXT NOT NULL,
    airport_code TEXT, -- If at airport
    phone TEXT,
    operating_hours TEXT,
    latitude REAL,
    longitude REAL,
    active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES car_rental_companies(company_id)
);

-- Vehicle categories table
CREATE TABLE IF NOT EXISTS vehicle_categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name TEXT NOT NULL, -- Economy, Compact, Mid-size, Full-size, SUV, Luxury
    category_description TEXT,
    typical_models TEXT, -- Examples of vehicles in this category
    passenger_capacity INTEGER NOT NULL,
    luggage_capacity INTEGER,
    transmission_type TEXT, -- Manual, Automatic, Both
    fuel_type TEXT, -- Gasoline, Diesel, Hybrid, Electric
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Available vehicles table
CREATE TABLE IF NOT EXISTS available_vehicles (
    vehicle_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    location_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    make TEXT NOT NULL,
    model TEXT NOT NULL,
    year INTEGER NOT NULL,
    license_plate TEXT,
    color TEXT,
    mileage INTEGER DEFAULT 0,
    fuel_type TEXT NOT NULL,
    transmission TEXT NOT NULL,
    features TEXT, -- JSON array of vehicle features
    daily_rate DECIMAL(10,2) NOT NULL,
    currency TEXT DEFAULT 'USD',
    availability_status TEXT DEFAULT 'AVAILABLE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES car_rental_companies(company_id),
    FOREIGN KEY (location_id) REFERENCES car_rental_locations(location_id),
    FOREIGN KEY (category_id) REFERENCES vehicle_categories(category_id)
);

-- Car rental bookings table
CREATE TABLE IF NOT EXISTS car_rental_bookings (
    booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    vehicle_id INTEGER NOT NULL,
    pickup_location_id INTEGER NOT NULL,
    dropoff_location_id INTEGER NOT NULL,
    booking_reference TEXT UNIQUE NOT NULL,
    pickup_date TIMESTAMP NOT NULL,
    dropoff_date TIMESTAMP NOT NULL,
    rental_days INTEGER NOT NULL,
    daily_rate DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    currency TEXT DEFAULT 'USD',
    booking_status TEXT DEFAULT 'CONFIRMED',
    driver_license_number TEXT NOT NULL,
    additional_drivers TEXT, -- JSON array of additional driver info
    insurance_options TEXT, -- JSON array of selected insurance
    special_equipment TEXT, -- JSON array of requested equipment
    booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (vehicle_id) REFERENCES available_vehicles(vehicle_id),
    FOREIGN KEY (pickup_location_id) REFERENCES car_rental_locations(location_id),
    FOREIGN KEY (dropoff_location_id) REFERENCES car_rental_locations(location_id)
);

-- Destinations table for travel planning
CREATE TABLE IF NOT EXISTS destinations (
    destination_id INTEGER PRIMARY KEY AUTOINCREMENT,
    destination_name TEXT NOT NULL,
    country TEXT NOT NULL,
    region TEXT,
    destination_type TEXT, -- City, Beach, Mountain, Historical, etc.
    description TEXT,
    best_time_to_visit TEXT,
    average_temperature_celsius REAL,
    currency TEXT,
    language TEXT,
    timezone TEXT,
    visa_required BOOLEAN DEFAULT 0,
    safety_rating INTEGER CHECK (safety_rating >= 1 AND safety_rating <= 5),
    cost_level TEXT, -- Budget, Moderate, Expensive, Luxury
    latitude REAL,
    longitude REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Attractions table for points of interest
CREATE TABLE IF NOT EXISTS attractions (
    attraction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    destination_id INTEGER NOT NULL,
    attraction_name TEXT NOT NULL,
    attraction_type TEXT NOT NULL, -- Museum, Park, Monument, Restaurant, etc.
    description TEXT,
    address TEXT,
    opening_hours TEXT,
    admission_price DECIMAL(10,2),
    currency TEXT DEFAULT 'USD',
    rating DECIMAL(3,1) CHECK (rating >= 0 AND rating <= 5),
    visit_duration_hours REAL,
    best_time_to_visit TEXT,
    website TEXT,
    phone TEXT,
    latitude REAL,
    longitude REAL,
    active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (destination_id) REFERENCES destinations(destination_id)
);

-- Travel itineraries table
CREATE TABLE IF NOT EXISTS travel_itineraries (
    itinerary_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    destination_id INTEGER NOT NULL,
    itinerary_name TEXT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    duration_days INTEGER NOT NULL,
    budget_amount DECIMAL(10,2),
    currency TEXT DEFAULT 'USD',
    travel_style TEXT, -- Adventure, Relaxation, Cultural, Business, etc.
    group_size INTEGER DEFAULT 1,
    itinerary_data TEXT, -- JSON with detailed day-by-day plans
    status TEXT DEFAULT 'DRAFT',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (destination_id) REFERENCES destinations(destination_id)
);

-- Travel advisories table
CREATE TABLE IF NOT EXISTS travel_advisories (
    advisory_id INTEGER PRIMARY KEY AUTOINCREMENT,
    destination_id INTEGER NOT NULL,
    advisory_type TEXT NOT NULL, -- HEALTH, SAFETY, VISA, WEATHER, etc.
    advisory_level TEXT NOT NULL, -- LOW, MODERATE, HIGH, CRITICAL
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    effective_date DATE,
    expiry_date DATE,
    source TEXT, -- Government agency, WHO, etc.
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (destination_id) REFERENCES destinations(destination_id)
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_flights_route_date ON flights(origin_airport_id, destination_airport_id, departure_time);
CREATE INDEX IF NOT EXISTS idx_flights_airline ON flights(airline_id);
CREATE INDEX IF NOT EXISTS idx_flight_bookings_user ON flight_bookings(user_id);
CREATE INDEX IF NOT EXISTS idx_flight_bookings_reference ON flight_bookings(booking_reference);

CREATE INDEX IF NOT EXISTS idx_hotels_location ON hotels(city, country);
CREATE INDEX IF NOT EXISTS idx_hotel_bookings_user ON hotel_bookings(user_id);
CREATE INDEX IF NOT EXISTS idx_hotel_bookings_dates ON hotel_bookings(check_in_date, check_out_date);
CREATE INDEX IF NOT EXISTS idx_hotel_bookings_reference ON hotel_bookings(booking_reference);

CREATE INDEX IF NOT EXISTS idx_vehicles_location_category ON available_vehicles(location_id, category_id);
CREATE INDEX IF NOT EXISTS idx_car_bookings_user ON car_rental_bookings(user_id);
CREATE INDEX IF NOT EXISTS idx_car_bookings_dates ON car_rental_bookings(pickup_date, dropoff_date);
CREATE INDEX IF NOT EXISTS idx_car_bookings_reference ON car_rental_bookings(booking_reference);

CREATE INDEX IF NOT EXISTS idx_attractions_destination ON attractions(destination_id);
CREATE INDEX IF NOT EXISTS idx_itineraries_user ON travel_itineraries(user_id);
CREATE INDEX IF NOT EXISTS idx_advisories_destination ON travel_advisories(destination_id);

-- Triggers for updating timestamps
CREATE TRIGGER IF NOT EXISTS update_users_timestamp 
    AFTER UPDATE ON users
    BEGIN
        UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE user_id = NEW.user_id;
    END;

CREATE TRIGGER IF NOT EXISTS update_flights_timestamp 
    AFTER UPDATE ON flights
    BEGIN
        UPDATE flights SET updated_at = CURRENT_TIMESTAMP WHERE flight_id = NEW.flight_id;
    END;

CREATE TRIGGER IF NOT EXISTS update_flight_bookings_timestamp 
    AFTER UPDATE ON flight_bookings
    BEGIN
        UPDATE flight_bookings SET updated_at = CURRENT_TIMESTAMP WHERE booking_id = NEW.booking_id;
    END;

CREATE TRIGGER IF NOT EXISTS update_hotels_timestamp 
    AFTER UPDATE ON hotels
    BEGIN
        UPDATE hotels SET updated_at = CURRENT_TIMESTAMP WHERE hotel_id = NEW.hotel_id;
    END;

CREATE TRIGGER IF NOT EXISTS update_hotel_bookings_timestamp 
    AFTER UPDATE ON hotel_bookings
    BEGIN
        UPDATE hotel_bookings SET updated_at = CURRENT_TIMESTAMP WHERE booking_id = NEW.booking_id;
    END;

CREATE TRIGGER IF NOT EXISTS update_vehicles_timestamp 
    AFTER UPDATE ON available_vehicles
    BEGIN
        UPDATE available_vehicles SET updated_at = CURRENT_TIMESTAMP WHERE vehicle_id = NEW.vehicle_id;
    END;

CREATE TRIGGER IF NOT EXISTS update_car_bookings_timestamp 
    AFTER UPDATE ON car_rental_bookings
    BEGIN
        UPDATE car_rental_bookings SET updated_at = CURRENT_TIMESTAMP WHERE booking_id = NEW.booking_id;
    END;

CREATE TRIGGER IF NOT EXISTS update_destinations_timestamp 
    AFTER UPDATE ON destinations
    BEGIN
        UPDATE destinations SET updated_at = CURRENT_TIMESTAMP WHERE destination_id = NEW.destination_id;
    END;

CREATE TRIGGER IF NOT EXISTS update_itineraries_timestamp 
    AFTER UPDATE ON travel_itineraries
    BEGIN
        UPDATE travel_itineraries SET updated_at = CURRENT_TIMESTAMP WHERE itinerary_id = NEW.itinerary_id;
    END;