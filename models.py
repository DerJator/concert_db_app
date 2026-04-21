from sqlalchemy import Column, Integer, String, Date, ForeignKey, Boolean
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Artist(Base):
    __tablename__ = "artist"

    artist_id = Column(Integer, primary_key=True)
    name = Column(String(255))
    genre = Column(String(100))
    gigs = relationship("Gig", back_populates="artist")

class Gig(Base):
    __tablename__ = "gigs"

    gig_id = Column(Integer, primary_key=True)
    artist_id = Column(Integer, ForeignKey("artist.artist_id"), nullable=False)
    date = Column(Date)
    location_id = Column(Integer, ForeignKey("locations.location_id"))
    setlist_id = Column(Integer)
    artist = relationship("Artist", back_populates="gigs")
    location = relationship("Location", back_populates="gigs")

class Location(Base):
    __tablename__ = "locations"

    location_id = Column(Integer, primary_key=True)
    name = Column(String(30))
    city = Column(String(30))
    type = Column(String(10))
    stage = Column(String(25), nullable=True)
    open_air = Column(Boolean)
    tag = Column(String(5), unique=True)
    gigs = relationship("Gig", back_populates="location")