#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
from models import db, app, Venue, Artist, Show
#import json
import sys
import dateutil.parser
import babel
from datetime import datetime
from flask import (
  render_template,
  request,
  Response,
  flash,
  redirect,
  url_for
)
import logging
from logging import Formatter, FileHandler
#from flask_wtf import Form
from forms import *



# TODO: connect to a local postgresql database


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format="EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format="EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')

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
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
    venues = Venue.query.distinct(Venue.state, Venue.city).all()
    data=[]
    for venue in venues:
        location = {
          'city': venue.city,
          'state': venue.state
        }
        venue_area = location
        venue_list = Venue.query.filter_by(city=venue.city, state=venue.state)
        venue_data=[]
        for venue in venue_list:
          details={
            'id': venue.id,
            'name': venue.name,
            'num_upcoming_shows': len(list(filter(lambda i: i.start_time > datetime.utcnow(), venue.shows)))
          }
          venue_data.append(details)
        venue_area['venues']= venue_data
        data.append(venue_area)
    return render_template('pages/venues.html', areas=data);




@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on venues with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

    search_term=request.form.get('search_term', '')
    venues = Venue.query.filter(Venue.name.ilike('%{}%'.format(search_term))).all()
    venue_data = []
    for venue in venues:
      venue_info = {
        'id': venue.id,
        'name': venue.name,
        'num_upcoming_shows': len(list(filter(lambda i: i.start_time > datetime.utcnow(), venue.shows)))
      }
      venue_data.append(venue_info)
    response={}
    response['count']= len(venues)
    response['data']= venue_data
    return render_template('pages/search_venues.html', results=response, search_term=search_term)



@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
    
    venue = Venue.query.get_or_404(venue_id)

    past_shows = []
    upcoming_shows = []

    for show in venue.shows:
        temp_show = {
            'artist_id': show.artist_id,
            'artist_name': show.artist.name,
            'artist_image_link': show.artist.image_link,
            'start_time': show.start_time.strftime("%m/%d/%Y, %H:%M")
        }
        if show.start_time <= datetime.now():
            past_shows.append(temp_show)
        else:
            upcoming_shows.append(temp_show)

    # object class to dict
    data = vars(venue)

    data['past_shows'] = past_shows
    data['upcoming_shows'] = upcoming_shows
    data['past_shows_count'] = len(past_shows)
    data['upcoming_shows_count'] = len(upcoming_shows)

    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # Set the FlaskForm
    form = VenueForm(request.form, meta={'csrf': False})
    # Validate all fields
    if form.validate():
        # Prepare for transaction
        try:
            venue = Venue(
                name=form.name.data,
                city=form.city.data,
                state=form.state.data,
                address=form.address.data,
                phone=form.phone.data,
                genres=form.genres.data,
                image_link=form.image_link.data,
                facebook_link=form.facebook_link.data,
                website=form.website_link.data,
                seeking_talent=form.seeking_talent.data,
                seeking_description=form.seeking_description.data
            )

            db.session.add(venue)
            db.session.commit()
            # flash success message
            flash('Venue'+' ' + request.form['name']+' ' + 'was successfully listed!')
        except ValueError as e:
            print(e)
            # If there is any error, roll back it
            db.session.rollback()
            # flash an error message
            flash('An error occurred.'+' ' + venue.name+' ' + 'Show could not be listed.')
        finally:
            # end the transaction
            db.session.close()
    else:
        message = []
        for field, err in form.errors.items():
            message.append(field + ' ' + '|'.join(err))
        flash('Errors ' + str(message))

    return render_template('pages/home.html')


# TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    error = False
    try:
        venue = Venue.query.filter_by(id=venue_id)
        db.session.delete(venue)
        db.session.commit()
    except:
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
        if error:
          flash('Venue '+' ' + venue.name +' ' + ' could not be successfully deleted!')
        else:
          flash('Venue '+' ' + venue.name +' ' + ' was successfully deleted!')

    return render_template('pages/home.html')


#  Update
#  ----------------------------------------------------------------

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    # TODO: populate form with values from venue with ID <venue_id>
    venue= Venue.query.get(venue_id)
    return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes

    # Set the FlaskForm
    form = VenueForm(request.form, meta={'csrf': False})
    # Validate all fields
    if form.validate():
        # Prepare for transaction
        try:
            venue = Venue.query.get(venue_id)

            venue.name = form.name.data
            venue.city=form.city.data
            venue.state=form.state.data
            venue.address=form.address.data
            venue.phone=form.phone.data
            venue.genres=form.genres.data
            venue.image_link=form.image_link.data
            venue.website=form.website_link.data
            venue.facebook_link=form.facebook_link.data
            venue.seeking_talent=form.seeking_talent.data
            venue.seeking_description=form.seeking_description.data

            db.session.add(venue)
            db.session.commit()
            # flash success message
            flash('Venue' +' ' + request.form['name'] +' ' + 'was successfully edited!')
        except ValueError as e:
            print(e)
            # If there is any error, roll back it
            db.session.rollback()
            # flash an error message
            flash('An error occurred.'+' ' + venue.name +' ' +  'could not be listed.')
        finally:
            # close the transaction
            db.session.close()
    else:
        message = []
        for field, err in form.errors.items():
            message.append(field + ' ' + '|'.join(err))
        flash('Errors ' + str(message))

    return redirect(url_for('show_venue', venue_id=venue_id))



#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
    artists = Artist.query.all()
    data = artists
    return render_template('pages/artists.html', artists=data)


# TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band"

@app.route('/artists/search', methods=['POST'])
def search_artists():
	search_term=request.form.get('search_term', '')
	artists = Artist.query.filter(Artist.name.ilike('%{}%'.format(search_term))).all()
	artist_data = []
	
	for artist in artists:
		artist_info = {
		'id': artist.id,
		'name': artist.name,
		'num_upcoming_shows': len(list(filter(lambda i: i.start_time > datetime.utcnow(), artist.shows)))
		}
		artist_data.append(artist_info)
	
	response={}
	response['count']= len(artists)
	response['data']= artist_data
	
	return render_template('pages/search_artists.html', results=response, search_term=search_term)


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id

    artist = Artist.query.get_or_404(artist_id)

    past_shows = []
    upcoming_shows = []

    for show in artist.shows:
        temp_show = {
            'venue_id': show.venue_id,
            'venue_name': show.venue.name,
            'venue_image_link': show.venue.image_link,
            'start_time': show.start_time.strftime("%m/%d/%Y, %H:%M")
        }
        if show.start_time <= datetime.now():
            past_shows.append(temp_show)
        else:
            upcoming_shows.append(temp_show)

    # object class to dict
    data = vars(artist)

    data['past_shows'] = past_shows
    data['upcoming_shows'] = upcoming_shows
    data['past_shows_count'] = len(past_shows)
    data['upcoming_shows_count'] = len(upcoming_shows)
    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    # TODO: populate form with fields from artist with ID <artist_id>
    artist=Artist.query.get(artist_id)
    return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes

    # Set the FlaskForm
    form = ArtistForm(request.form, meta={'csrf': False})
    # Validate all fields
    if form.validate():
        # Prepare for transaction
        try:
            artist = Artist.query.get(artist_id)

            artist.name = form.name.data
            artist.city=form.city.data
            artist.state=form.state.data
            artist.phone=form.phone.data
            artist.genres=form.genres.data
            artist.image_link=form.image_link.data
            artist.website=form.website_link.data
            artist.facebook_link=form.facebook_link.data
            artist.seeking_venue=form.seeking_venue.data
            artist.seeking_description=form.seeking_description.data

            db.session.add(artist)
            db.session.commit()
            # flash success message
            flash('Artist' +' '+ request.form['name']+' '+ 'was successfully edited!')
        except ValueError as e:
            print(e)
            # If there is any error, roll back it
            db.session.rollback()
            # flash an error message
            flash('An error occurred.'+' ' + artist.name + ' ' + 'could not be edited.')
        finally:
            # close the transaction
            db.session.close()
    else:
        message = []
        for field, err in form.errors.items():
            message.append(field + ' ' + '|'.join(err))
        flash('Errors ' + str(message))

    return redirect(url_for('show_artist', artist_id=artist_id))



#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # Set the FlaskForm
    form = ArtistForm(request.form, meta={'csrf': False})
    # Validate all fields
    if form.validate():
        # Prepare for transaction
        try:
            artist = Artist(
                name=form.name.data,
                city=form.city.data,
                state=form.state.data,
                phone=form.phone.data,
                genres=form.genres.data,
                image_link=form.image_link.data,
                facebook_link=form.facebook_link.data,
                website=form.website_link.data,
                seeking_venue=form.seeking_venue.data,
                seeking_description=form.seeking_description.data
            )

            db.session.add(artist)
            db.session.commit()
            # flash success message
            flash('Atist' + request.form['name'] + 'was successfully listed!')
        except ValueError as e:
            print(e)
            # If there is any error, roll back it
            db.session.rollback()
            # flash an error message
            flash('An error occurred.' + artist.name + 'could not be listed.')
        finally:
            #close the transaction
            db.session.close()
    else:
        message = []
        for field, err in form.errors.items():
            message.append(field + ' ' + '|'.join(err))
        flash('Errors ' + str(message))

    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    data=[]
    shows= Show.query.all()
    for show in shows:
        show_details = {
          'venue_id': show.venue.id,
          'venue_name': show.venue.name,
          'artist_id': show.artist.id,
          'artist_name': show.artist.name,
          'artist_image_link': show.artist.image_link,
          'start_time': show.start_time.isoformat()
        }
        data.append(show_details)

    return render_template('pages/shows.html', shows=data)



@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # Set the FlaskForm
    form = ShowForm(request.form, meta={'csrf': False})
    # Validate all fields
    if form.validate():
        # Prepare for transaction
        try:
            show = Show(
              venue_id=form.venue_id.data,
              artist_id=form.artist_id.data,
              start_time=form.start_time.data
            )

            db.session.add(show)
            db.session.commit()
            # flash success message
            flash('Show was successfully listed!')
        except ValueError as e:
            print(e)
            # If there is any error, roll back it
            db.session.rollback()
            # flash an error message
            flash('An error occurred. Show could not be listed.')
        finally:
            # close the transaction
            db.session.close()
    else:
        message = []
        for field, err in form.errors.items():
            message.append(field + ' ' + '|'.join(err))
        flash('Errors ' + str(message))

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
