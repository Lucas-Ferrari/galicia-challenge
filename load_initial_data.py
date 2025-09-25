#!/usr/bin/env python3
"""
Script for loading initial data from CSV/DAT files
Run from project root: python utils/load_initial_data.py
"""
import sys
from pathlib import Path

from app.services.data_loader import DataLoader
from app.database import engine
from app.database import Base

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def create_tables():
    """Create all tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully")


def main():
    """Main function"""
    print("🚀 Starting initial data load...")

    # Create tables
    create_tables()

    # Find data files
    data_dir = Path("data")
    airports_file = data_dir / "airports.dat"
    airlines_file = data_dir / "airlines.csv"
    routes_files = list(data_dir.glob("routes*.csv"))

    if not all([airports_file.exists(), airlines_file.exists(), routes_files]):
        print("❌ Missing data files")
        return

    print(f"✅ Found {len(routes_files)} route files")

    # Load data
    loader = DataLoader()

    try:
        # Load airports
        print("📊 Loading airports...")
        created, updated, errors = loader.load_airports_from_dat(str(airports_file))
        print(f"   Airports: {created} created, {updated} updated")

        # Load airlines
        print("📊 Loading airlines...")
        created, updated, errors = loader.load_airlines_from_csv(str(airlines_file))
        print(f"   Airlines: {created} created, {updated} updated")

        # Load routes
        total_routes = 0
        print("📊 Loading routes...")
        for routes_file in routes_files:
            created, errors = loader.load_routes_from_csv(str(routes_file))
            total_routes += created
            print(f"   {routes_file.name}: {created} routes")

        print(f"\n🎉 Loading completed! Total routes: {total_routes}")

    finally:
        loader.close()


if __name__ == "__main__":
    main()
