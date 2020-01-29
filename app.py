#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
from datetime import datetime
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import sys

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    genre = db.Column(db.ARRAY(db.String(120)))
    address = db.Column(db.String(120))
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500), nullable=True)
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120), nullable=True)
    seeking_talent = db.Column(db.Boolean, nullable=True, default=False)
    seeking_description = db.Column(db.String, nullable=True)
    show = db.relationship('Show', backref='venue', cascade='all, delete-orphan', lazy=True)

class Artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String(120)))
    image_link = db.Column(db.String(500), nullable=True)
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120), nullable=True)
    seeking_venue = db.Column(db.Boolean, nullable=True, default=False)
    seeking_description = db.Column(db.String, nullable=True)
    show = db.relationship('Show', backref='artist', cascade='all, delete-orphan', lazy=True)

class Show(db.Model):
    __tablename__ = 'show'

    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime(), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), nullable=False)


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  error = False
  try:
    areas = db.session.query(Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()
    shows = Show.query.all()
    data = []
    today = datetime.today()
    upcomingShows = []
    for show in shows: 
      if show.start_time >= today:
        upcomingShows.append(show)
    for area in areas:
      venues = Venue.query.filter(Venue.city == area.city, Venue.state == area.state).all()
      record = {
        'city': area.city,
        'state': area.state,
        'venues': []
      }
      for venue in venues:
        record['venues'].append({
          "id": venue.id,
          "name": venue.name,
          "num_upcoming_show": len(upcomingShows)
        })
      data.append(record)
  except:
    error = True
  finally:
    return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # search for venues using search_term
  error = False
  try:
    search_term=request.form.get('search_term', '')
    venues = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()
    numResults = len(venues)
    shows = Show.query.all()
    data = []
    today = datetime.today()
    upcomingShows = []
    for show in shows: 
      if show.start_time >= today:
        upcomingShows.append(show)
    data = []
    response=({
        "count": numResults,
        "data": data
    })
    for venue in venues:
      data.append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": len(upcomingShows)
      })
  except:
    error = True
    flash(f'Connection to database failed.')
  finally:
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  error = False
  try:
    venue = Venue.query.get(venue_id)
    shows = Show.query.filter_by(venue_id=venue_id).join('artist').all()
    today = datetime.today()
    upcomingShows = []
    pastShows = []
    upcomingShowsList = []
    pastShowsList = []
    for show in shows: 
      if show.start_time >= today:
        upcomingShows.append(show)
      elif show.start_time < today:
        pastShows.append(show)
    for show in upcomingShows:
      upcomingShowsList.append({
        'artist_id': show.artist_id,
        'artist_name': show.artist.name,
        'artist_image_link': show.artist.image_link,
        'start_time': str(show.start_time)
      })
    for show in pastShows:
      pastShowsList.append({
        'artist_id': show.artist_id,
        'artist_name': show.artist.name,
        'artist_image_link': show.artist.image_link,
        'start_time': str(show.start_time)
      })
    details = { 'id': venue.id, 'name': venue.name, 'genres': venue.genre, 
    'city': venue.city, 'state': venue.state, 'address': venue.address, 'phone': venue.phone, 
    'website': venue.website, 'facebook_link': venue.facebook_link, 
    'seeking_talent': venue.seeking_talent, 'seeking_description': venue.seeking_description,
    'image_link': venue.image_link, 'upcoming_shows_count': len(upcomingShows), 
    'past_shows_count': len(pastShows), 'upcoming_shows': upcomingShowsList, 
    'past_shows': pastShowsList
    }
    db.session.commit()
  except:
    error = True
    flash('Connection to database failed.')
  finally:
    db.session.close()
    return render_template('pages/show_venue.html', venue=details)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm()
  error = False
  try:
    if form.validate_on_submit():
      name = request.form['name']
      city = request.form['city']
      state = request.form['state']
      address = request.form['address']
      phone = request.form['phone']
      genre = request.form.getlist('genres')
      facebook_link = request.form['facebook_link']
      venue = Venue(name=name, city=city, state=state, address=address, phone=phone, genre=genre, facebook_link=facebook_link)
      db.session.add(venue)
      db.session.commit()
    # on successful db insert, flash success
      flash('Venue ' + name + ' was successfully listed!')
    else:
      error = True
      errorMessage=[]
      for key, value in form.errors.items():
        errorMessage.append(key + ':')
        errorMessage.append(value[0])
      # on unsuccessful db insert, flash an error instead.
      flash(f'Error: {errorMessage} Venue could not be created.')
  finally:
    db.session.close()
    if error == False:
      return render_template('pages/home.html')
    else:
      return render_template('forms/new_venue.html', form=form)
    

@app.route('/venues/<venue_id>/delete', methods=['DELETE', 'POST'])
def delete_venue(venue_id):
  error = False
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
  except:
    error = True
    flash({{venue.name}} + 'could not be deleted.')
  finally:
    return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  return render_template('pages/artists.html', artists=Artist.query.order_by('id').all())

@app.route('/artists/search', methods=['POST'])
def search_artists():
  error = False
  try:
    search_term=request.form.get('search_term', '')
    artists = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()
    numResults = len(artists)
    shows = Show.query.all()
    data = []
    today = datetime.today()
    upcomingShows = []
    for show in shows: 
      if show.start_time >= today:
        upcomingShows.append(show)
    data = []
    response=({
        "count": numResults,
        "data": data
    })
    for artist in artists:
      data.append({
        "id": artist.id,
        "name": artist.name,
        "num_upcoming_shows": len(upcomingShows)
      })
  except:
    error = True
    flash(f'Connection to database failed.')
  finally:
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  error = False
  try:
    artist = Artist.query.get(artist_id)
    shows = Show.query.filter_by(artist_id=artist_id).join('venue')
    upcomingShows = []
    pastShows = []
    today = datetime.today()
    upcomingShowsList = []
    pastShowsList = []
    for show in shows:
      if show.start_time >= today:
        upcomingShows.append(show)
      elif show.start_time < today:
        pastShows.append(show)
    for show in upcomingShows:
      upcomingShowsList.append({
        'venue_id': show.venue_id,
        'venue_name': show.venue.name,
        'venue_image_link': show.venue.image_link,
        'start_time': str(show.start_time)
      })
    for show in pastShows:
      pastShowsList.append({
        'venue_id': show.venue_id,
        'venue_name': show.venue.name,
        'venue_image_link': show.venue.image_link,
        'start_time': str(show.start_time)
      })

    details = { 'id': artist.id, 'name': artist.name, 'genres': artist.genres, 
    'city': artist.city, 'state': artist.state, 'phone': artist.phone, 
    'website': artist.website, 'facebook_link': artist.facebook_link, 
    'seeking_venue': artist.seeking_venue, 'seeking_description': artist.seeking_description,
    'image_link': artist.image_link, 'upcoming_shows_count': len(upcomingShows), 
    'past_shows_count': len(pastShows), 
    'upcoming_shows': upcomingShowsList, 'past_shows': pastShowsList
    }
    db.session.commit()
  except:
    error = True
    flash('Connection to database failed.')
  finally:
    db.session.close()
    return render_template('pages/show_artist.html', artist=details)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  error = False
  try:
    form = ArtistForm()
    artist=Artist.query.get(artist_id)
  except:
    error = True
    return redirect(url_for('show_artist'), artist_id=artist_id)
    flash('Unable to edit ' + artist.name)
  finally:
    return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  error = False
  try: 
    artist = Artist.query.get(artist_id)
    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.genres = request.form.get('genres')
    artist.facebook_link = request.form['facebook_link']
    db.session.commit()
  except:
    error = True
    return redirect(url_for('show_artist'), artist_id=artist_id)
    flash('Unable to update ' + artist.name)
  finally:
    return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  # populate form with values from venue with ID <venue_id>
  error = True
  try:
    form = VenueForm()
    venue=Venue.query.get(venue_id)
  except:
    error = False
    return redirect(url_for('show_venue'), venue_id=venue_id)
    flash('Unable to edit ' +  venue.name)
  finally:
    return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  error = False
  try: 
    venue = Venue.query.get(venue_id)
    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.address = request.form['address']
    venue.state = request.form['state']
    venue.phone = request.form['phone']
    venue.genre = request.form.getlist('genres')
    venue.facebook_link = request.form['facebook_link']
    db.session.commit()
  except:
    error = True
    redirect(url_for('show_venue', venue_id=venue_id))
    flash('Unable to update ' + venue.name)
  finally:
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  form = ArtistForm()
  error = False
  try:
    if form.validate_on_submit():
      name = request.form['name']
      city = request.form['city']
      state = request.form['state']
      phone = request.form['phone']
      genres = request.form.getlist('genres')
      facebook_link = request.form['facebook_link']
      artist = Artist(name=name, city=city, state=state, phone=phone, genres=genres, facebook_link=facebook_link)
      db.session.add(artist)
      db.session.commit()
    # on successful db insert, flash success
      flash('Artist ' + name + ' was successfully listed!')
    else:
      error = True
      errorMessage=[]
      for key, value in form.errors.items():
        errorMessage.append(key + ':')
        errorMessage.append(value[0])
    # if unsuccesful, flash error
      flash(f'Error: {errorMessage} Artist could not be created.')
  finally:
    db.session.close()
    if error == False:
      return render_template('pages/home.html')
    else:
      return render_template('forms/new_artist.html', form=form)

@app.route('/artists/<artist_id>/delete', methods=['DELETE', 'POST'])
def delete_artist(artist_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  error = False
  try:
    artist = Artist.query.get(artist_id)
    db.session.delete(artist)
    db.session.commit()
  except:
    error = True
    flash({{artist.name}} + 'could not be deleted.')
  finally:
    return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  error = False
  try:
    shows = Show.query.join('artist').join('venue').all()
    data=[]
    for show in shows:
      data.append({
      "venue_id": show.venue.id,
      "venue_name": show.venue.name,
      "artist_id": show.artist.id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": str(show.start_time)
      })
  except:
    error = True
    flash('Error: shows are not found.')
    return render_template('pages/home.html')
  finally:
    return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  error = False
  try:
    artist_id = request.form['artist_id']
    venue_id = request.form['venue_id']
    start_time = request.form['start_time']
    show = Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)
    db.session.add(show)
    db.session.commit()
  # on successful db insert, flash success
    flash('Show was successfully listed!')
  except:
    error = True
  # on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close()
    return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
