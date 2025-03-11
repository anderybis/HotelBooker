import os
from datetime import datetime
from app import app, db
from models import User, Room, Booking
from werkzeug.security import generate_password_hash

def seed_rooms():
    """Add sample rooms to the database."""
    # Check if rooms already exist and delete them
    if Room.query.count() > 0:
        print("Deleting existing rooms...")
        Room.query.delete()
        db.session.commit()
        print("All existing rooms deleted.")
    
    # Sample rooms data
    rooms = [
        {
            "room_number": "101",
            "room_type": "standard",
            "capacity": 2,
            "price_per_night": 99.99,
            "description": "Comfortable standard room with a queen-sized bed, flat-screen TV, and desk. Perfect for solo travelers or couples on a budget. Complimentary Wi-Fi included.",
            "amenities": "Queen Bed, Free Wi-Fi, Flat-screen TV, Air Conditioning, Work Desk, Coffee Maker, En-suite Bathroom",
            "image_url": "https://images.unsplash.com/photo-1566665797739-1674de7a421a?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2274&q=80"
        },
        {
            "room_number": "102",
            "room_type": "standard",
            "capacity": 2,
            "price_per_night": 109.99,
            "description": "Bright and airy standard room with two twin beds, perfect for friends or business associates traveling together. Includes a work area and coffee station.",
            "amenities": "Twin Beds, Free Wi-Fi, Flat-screen TV, Air Conditioning, Work Desk, Coffee Maker, En-suite Bathroom",
            "image_url": "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80"
        },
        {
            "room_number": "201",
            "room_type": "deluxe",
            "capacity": 3,
            "price_per_night": 169.99,
            "description": "Spacious deluxe room featuring a king-sized bed, seating area, and premium amenities. Enjoy extra space and comfort during your stay. Perfect for extended visits.",
            "amenities": "King Bed, Free Wi-Fi, 50-inch TV, Mini-fridge, Lounge Area, Coffee Machine, Premium Toiletries, Rainfall Shower",
            "image_url": "https://images.unsplash.com/photo-1591088398332-8a7791972843?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2274&q=80"
        },
        {
            "room_number": "202",
            "room_type": "deluxe",
            "capacity": 3,
            "price_per_night": 179.99,
            "description": "Modern deluxe room with a queen-sized bed and pull-out sofa. Perfect for small families or those who need extra sleeping space. Includes additional amenities.",
            "amenities": "Queen Bed, Sofa Bed, Free Wi-Fi, 55-inch Smart TV, Mini-fridge, Work Area, Coffee Machine, Premium Toiletries, Bathrobes",
            "image_url": "https://images.unsplash.com/photo-1618773928121-c32242e63f39?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80"
        },
        {
            "room_number": "301",
            "room_type": "suite",
            "capacity": 4,
            "price_per_night": 289.99,
            "description": "Luxurious suite with a separate bedroom and living area. This spacious accommodation includes a king-sized bed, sofa bed, and upgraded amenities for ultimate comfort.",
            "amenities": "King Bed, Sofa Bed, Free Wi-Fi, Two 55-inch Smart TVs, Kitchenette, Dining Area, Coffee Machine, Mini-bar, Premium Toiletries, Soaking Tub, Bathrobes, Slippers",
            "image_url": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80"
        },
        {
            "room_number": "302",
            "room_type": "suite",
            "capacity": 5,
            "price_per_night": 329.99,
            "description": "Premium family suite with two bedrooms - one with a king-sized bed and one with two twin beds. Includes a living area with sofa bed, kitchenette, and dining space.",
            "amenities": "King Bed, Two Twin Beds, Sofa Bed, Free Wi-Fi, Three TVs, Full Kitchenette, Dining Area, Espresso Machine, Premium Toiletries, Jacuzzi Tub, Bathrobes, Slippers",
            "image_url": "https://images.unsplash.com/photo-1578683010236-d716f9a3f461?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80"
        }
    ]
    
    try:
        for room_data in rooms:
            room = Room(**room_data)
            db.session.add(room)
        
        db.session.commit()
        print(f"Successfully added {len(rooms)} sample rooms to the database.")
    except Exception as e:
        db.session.rollback()
        print(f"Error adding rooms: {str(e)}")

def seed_users():
    """Add admin and regular users for testing."""
    # Delete any existing users
    if User.query.count() > 0:
        print("Deleting existing users...")
        User.query.delete()
        db.session.commit()
        print("All existing users deleted.")
    
    # Create admin user
    admin = User(
        username="admin",
        email="admin@luxuryhotel.com",
        password_hash=generate_password_hash("admin123"),
        is_admin=True
    )
    
    # Create regular user
    user = User(
        username="testuser",
        email="user@example.com",
        password_hash=generate_password_hash("password123"),
        is_admin=False
    )
    
    try:
        db.session.add(admin)
        db.session.add(user)
        db.session.commit()
        print("Admin and regular users created successfully.")
    except Exception as e:
        db.session.rollback()
        print(f"Error creating users: {str(e)}")

if __name__ == "__main__":
    with app.app_context():
        seed_rooms()
        seed_users()
        print("Database seeding completed.")