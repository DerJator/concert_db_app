
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Artist, Gig, Location
from sqlalchemy import func, extract
import json

import helpers

with open('credentials.json', 'r') as file:
    credentials = json.load(file)
DATABASE_URL = f"mysql+pymysql://{credentials['db_user']}:{credentials['password']}@localhost:{credentials['port']}/{credentials['db_name']}"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_size=5,
    max_overflow=10
    )
SessionLocal = sessionmaker(bind=engine)

# new
def get_db():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

class Queries:
    def __init__(self, db: Session):
        self.db = db

    def close(self):
        self.db.close()

    def get_artists_ordered_by_most_concerts(self) -> list[dict]:
        results = (
            self.db.query(Artist.name, func.count(Gig.gig_id).label("gig_count"))
            .join(Gig, Gig.artist_id == Artist.artist_id)
            .group_by(Artist.artist_id)
            .order_by(func.count(Gig.gig_id).desc())
            .all()
        )
        ordered_list = [{"artist": name, "gig_count": count} for i, (name, count) in enumerate(results)]
        ranked_list = helpers.rank_list(data=ordered_list, target_field='gig_count')
        return ranked_list

    def get_artists_ordered_by_time(self) -> list[Artist]:
        results = self.db.query(Artist).all()
        ordered_list = [
            {
                "name": artist.name,
                "genre": artist.genre,
            }
            for artist in results
        ]
        ordered_list = helpers.rank_list(ordered_list, target_field="name")
        return ordered_list

    def get_artist_from_name(self, artist_name: str) -> Artist:
        artist = self.db.query(Artist).filter(Artist.name == artist_name).first()
        return artist
    
    def get_top_artists_from_location_tag(self, location: Location) -> list[Artist]:

        results = (
            self.db.query(Artist.name, func.count(Gig.gig_id).label("gig_count"))
            .join(Gig, Gig.artist_id == Artist.artist_id)
            .filter(Gig.location_id == location.location_id)
            .group_by(Artist.artist_id)
            .order_by(func.count(Gig.gig_id).desc())
            .all()
        )
        return results
    
    def get_gigs_as_list(self) -> list[Gig]:
        return self.db.query(Gig).all()

    def get_gigs_from_artist_id(self, artist_id: int) -> list[Gig]:
        return self.db.query(Gig).filter(Gig.artist_id == artist_id).all()
    
    def get_gigs_by_month(self, month: int) -> list[Gig]:
        return self.db.query(Gig).filter(extract("month", Gig.date) == month).all()

    def get_gigs_by_year(self, year: int) -> list[Gig]:
        return self.db.query(Gig).filter(extract("year", Gig.date) == year).all()
    
    def get_locations_unordered(self) -> list[Location]:
        return self.db.query(Location).all()
    
    def get_locations_ranked_by_most_visits(self) -> list[Location]:
        ranking = (self.db.query(Location, func.count(Gig.gig_id).label("gig_count"))
        .join(Gig, Gig.location_id == Location.location_id)
        .group_by(Location.location_id)
        .order_by(func.count(Gig.gig_id).desc())
        .all()
        )
        ordered_list = [
            {
                "gig_count": count,
                "location_id": location.location_id,
                "name": location.name,
                "city": location.city,
                "type": location.type,
                "stage": location.stage,
                "open_air": location.open_air,
                "tag": location.tag,
            }
            for i, (location, count) in enumerate(ranking)
        ]
        ordered_list = helpers.rank_list(ordered_list, target_field="gig_count")
        return ordered_list

    def get_location_by_tag(self, tag: str) -> Location:
        return self.db.query(Location).filter(Location.tag == tag).first()
    
    def get_top_locations_from_city(self, city) -> list[Location]:
        ranking = (
        self.db.query(Location, func.count(Gig.gig_id).label("gig_count"))
        .join(Gig, Gig.location_id == Location.location_id)
        .filter(Location.city == city)
        .group_by(Location.location_id)
        .order_by(func.count(Gig.gig_id).desc())
        .all()
        )
        return ranking

    # --- STATS ---
    def get_months_ranked_by_most_concerts(self):
        results = (
            self.db.query(extract("month", Gig.date).label("month"), func.count(Gig.gig_id).label("gig_count"))
            .group_by("month")
            .order_by(func.count(Gig.gig_id).desc())
            .all()
        )
        ordered_list = [{"month": month, "gig_count": count} for (month, count) in results]
        ordered_list = helpers.rank_list(ordered_list, target_field="gig_count")
        return ordered_list

    def get_years_ranked_by_most_concerts(self) -> list[dict]:
        results = (
            self.db.query(extract("year", Gig.date).label("year"), func.count(Gig.gig_id).label("gig_count"))
            .group_by("year")
            .order_by(func.count(Gig.gig_id).desc())
            .all()
        )
        ordered_list = [{"year": year, "gig_count": count} for (year, count) in results]
        ordered_list = helpers.rank_list(ordered_list, target_field="gig_count")
        return ordered_list

    def get_city_count_from_artist(self, artist: Artist):
        results = (
            self.db.query(Location.city, func.count(Gig.gig_id).label("gig_count"))
            .join(Gig, Gig.location_id == Location.location_id)
            .filter(Gig.artist_id == artist.artist_id)
            .group_by(Location.city)
            .order_by(func.count(Gig.gig_id).desc())
            .all()
        )
        return results