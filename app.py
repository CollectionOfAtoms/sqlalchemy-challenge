import numpy as np
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")
# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

#################################################
# Flask Setup
#################################################
app = Flask(__name__)
version = "v1.0"
prefix = f"/api/{version}"


#################################################
# Flask Routes
#################################################

@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"<a href='/api/v1.0/precipitation'>/api/v1.0/precipitation</a><br/>"
        f"<a href='/api/v1.0/stations'>/api/v1.0/stations</a><br/>"
        f"<a href='/api/v1.0/tobs'>/api/v1.0/tobs</a><br/>"
        f"<a href='/api/v1.0/2016-01-01'>/api/v1.0/start_date</a><br/>"
        f"<a href='/api/v1.0/<start>/<end>'>/api/v1.0/start_date/end_date</a><br/>"
    )

# Returns all precipitation data by date 
@app.route(f"{prefix}/precipitation")
def precipitation():

    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return all date and precipitation data"""
    # Query all Mesurement dates and precipitation data
    results = session.query(Measurement.date, Measurement.prcp).all()

    session.close()

    # Massage output into correct form
    output = {}
    for result in results:
        output[ result[0] ] = result[1]

    return jsonify(output)


@app.route(f"{prefix}/stations")
def stations():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a list of passenger data including the name, age, and sex of each passenger"""
    # Query all Stations
    results = session.query(Station).all()

    session.close()

    output=[]
    for result in results:
        datum = {
            'station': result.station,
            'name': result.name,
            'latitude': result.latitude,
            'longitude': result.longitude,
            'elevation': result.elevation
        }
        output.append(datum)

    # Create a dictionary from the row data and append to a list of all_passengers
    return jsonify(output)

#Returns a list of dates and temperature observations of the most active station for the last year of data.
@app.route(f"{prefix}/tobs")
def tobs():
    
    # Create our session (link) from Python to the DB
    session = Session(engine)

    ## Get the last date in the table 
    row = session.query(func.Max(Measurement.date)).first()
    last_date = row[0]

    # Build a new string with fourth digit made one lower
    # Will not work if the last_date occurs on the first year of a decade
    one_year_from_last = last_date[0:3] + str(int(last_date[3])-1) + last_date[4:]

    # Query all measurment from most active station during last year
    results = session.query(Measurement.date, Measurement.tobs)\
        .filter(Measurement.station == 'USC00519281')\
        .filter(Measurement.date > one_year_from_last)\
        .order_by(Measurement.date.asc())

    session.close()

    output = []
    for result in results: 
        output.append( {"date" : result[0],
                        "tobs" : result[1] })

    return jsonify(output)

#Calculates the max min and average of the first index of results
def calcStats(results):
    tobsMax = float('-inf')
    tobsMin = float('inf')
    numResults = 0
    runningTotal = 0
    for result in results: 
        numResults += 1
        if (result[0] > tobsMax):
            tobsMax = result[0] 
        if result[0] < tobsMin:
            tobsMin = result[0] 
        runningTotal += result[0]

    tobsAvg = runningTotal / numResults

    return { "TMAX" : tobsMax,
             "TMIN" : tobsMin,
             "TAVG" : tobsAvg}

#Return summary statistics for all TOBS from start date until end of set
@app.route(f"{prefix}/<start>/")
def start(start):

    session = Session(engine)

    results = session.query( Measurement.tobs)\
        .filter(Measurement.date > start)

    session.close()

    return calcStats(results)

#Return summary statistics for all tobs between provided start and end dates
@app.route(f"{prefix}/<start>/<end>")
def start_end(start, end):
    session = Session(engine)

    results = session.query( Measurement.tobs)\
        .filter(Measurement.date > start)\
        .filter(Measurement.date < end)

    session.close()

    return calcStats(results)    

if __name__ == '__main__':
    app.run(debug=True)
