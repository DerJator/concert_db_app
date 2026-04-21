
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import func, extract
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request

from database import Queries, get_db
from models import Artist, Gig, Location
from rag_chat import RAGChatbot
import helpers


app = FastAPI()
templates = Jinja2Templates(directory="templates")

# TODO: adapt rank regarding ties
@app.get("/")
def root(request: Request):
    return templates.TemplateResponse(request, "index.html")

@app.get("/artists")
def get_artists(db: Session = Depends(get_db), ):
    query_manager = Queries(db=db)
    return query_manager.get_artists_ordered_by_time()

@app.get("/artists/ranked")
def get_artists_ranked(db: Session = Depends(get_db), ):
    query_manager = Queries(db=db)
    return query_manager.get_artists_ordered_by_most_concerts()

@app.get("/artists/{artist_name}")
def get_artist_by_name(artist_name: str, db: Session = Depends(get_db)):
    query_manager = Queries(db=db)
    artist = query_manager.get_artist_from_name(artist_name)
    if not artist:
        raise HTTPException(status_code=404, detail=f"Artist {artist_name} not found")
    return artist

@app.get("/gigs")
def get_gigs(db: Session = Depends(get_db)):
    query_manager = Queries(db=db)
    return query_manager.get_gigs_as_list()

@app.get("/gigs/artist/{artist_name}")
def get_gigs_by_artist_name(artist_name: str, db: Session = Depends(get_db)):
    query_manager = Queries(db=db)
    artist = query_manager.get_artist_from_name(artist_name)
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")
    gigs = query_manager.get_gigs_from_artist_id(artist.artist_id)
    if not gigs:
        raise HTTPException(status_code=404, detail=f"No gigs found for artist {artist.name}")
    
    return gigs

@app.get("/gigs/year/{year}")
def get_gigs_by_year(year: int, db: Session = Depends(get_db)):
    query_manager = Queries(db=db)
    gigs = query_manager.get_gigs_by_year(year)
    if not gigs:
        raise HTTPException(status_code=404, detail=f"No gigs found for year {year}")
    return gigs  # TODO: Would be nice if location and artist are shown with name, but first implement relationship for that 

@app.get("/gigs/month/{month}")
def get_gigs_by_month(month: int, db: Session = Depends(get_db)):
    query_manager = Queries(db=db)
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")
    gigs = query_manager.get_gigs_by_month(month)
    if not gigs:
        raise HTTPException(status_code=404, detail="No gigs found for this month")
    return gigs

@app.get("/locations")
def get_locations(db: Session = Depends(get_db)):
    query_manager = Queries(db=db)
    return query_manager.get_locations_unordered()

@app.get("/locations/ranked")
def get_locations_ranked(db: Session = Depends(get_db)):
    query_manager = Queries(db=db)
    return query_manager.get_locations_ranked_by_most_visits()

@app.get("/locations/{location_name}")
def get_location_by_name(location_name: str, db: Session = Depends(get_db)):
    query_manager = Queries(db=db)
    location = query_manager.get_location_by_name(location_name)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location

@app.get("/test")
def get_test(db: Session = Depends(get_db)):
    query_manager = Queries(db=db)
    methods_list = [method for method in dir(Queries) if callable(
    getattr(Queries, method)) and not (method.startswith("__") or method == "close")]
    print(f"{methods_list}")
    gig = query_manager.get_gigs_as_list()[0]
    print(gig.artist.name)       # directly access artist
    print(gig.location.city)     # directly access location

    # and from the other direction
    artist = query_manager.get_artists_ordered_by_time()[0]
    for gig in artist.gigs:      # all gigs for that artist
        print(gig.date)

@app.get("/locations/city/{city}/ranked")
def get_locations_by_city_ranked(city: str, db: Session = Depends(get_db)):
    query_manager = Queries(db=db)
    results = query_manager.get_top_locations_from_city(city)
    if not results:
        raise HTTPException(status_code=404, detail="No locations found for this city")
    return [
        {
            "rank": i + 1,
            "gig_count": count,
            "location_id": location.location_id,
            "name": location.name,
            "city": location.city,
            "type": location.type,
            "stage": location.stage,
            "open_air": location.open_air,
            "tag": location.tag,
        }
        for i, (location, count) in enumerate(results)
    ]

@app.get("/question")
def question(text: str, db: Session = Depends(get_db)):
    chat = RAGChatbot(db=db)
    response = chat.answer_query(text)
    return response

# ---- STATS ----
@app.get("/stats/busiest-year")
def get_busiest_year(db: Session = Depends(get_db)):
    query_manager = Queries(db=db)
    results = query_manager.get_years_ranked_by_most_concerts()
    return [{"year": int(r.year), "gig_count": r.gig_count, "rank": i + 1} for i, r in enumerate(results)]

@app.get("/stats/busiest-month")
def get_busiest_month(db: Session = Depends(get_db)):
    query_manager = Queries(db=db)
    results = query_manager.get_months_ranked_by_most_concerts()
    months = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]
    return [{"month": months[int(r.month) - 1], "gig_count": r.gig_count, "rank": i + 1} for i, r in enumerate(results)]

# GET /stats/artist/{artist_name}/cities
@app.get("/stats/artist/{artist_name}/cities")
def get_artist_cities_ranked(artist_name: str, db: Session = Depends(get_db)):
    query_manager = Queries(db=db)
    artist = query_manager.get_artist_from_name(artist_name)
    if not artist:
        raise HTTPException(status_code=404, detail=f"Artist {artist_name} not found")
    results = query_manager.get_city_count_from_artist(artist)
    return [{"city": city, "gig_count": count} for city, count in results]

@app.get("/stats/locations/{location_tag}/artists")
def get_artists_by_location_tag_ranked(location_tag: str, db: Session = Depends(get_db)):
    query_manager = Queries(db=db)
    location = query_manager.get_location_by_tag(location_tag)
    if not location:
        raise HTTPException(status_code=404, detail="Location with tag '{location_tag}' not found")
    results = query_manager.get_top_artists_from_location_tag(location)

    return {
        "location": location.name,
        "city": location.city,
        "artists": [{"rank": i + 1, "artist": name, "gig_count": count} for i, (name, count) in enumerate(results)]
        
    }
