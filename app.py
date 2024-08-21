from flask import Flask, request, render_template, redirect, url_for, send_file, session, flash, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from flask_bcrypt import Bcrypt
import os
from KKSongsPresentationCreator import KKSongsPresentationCreator
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import json
import urllib.parse

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
bcrypt = Bcrypt(app)
presentation_creator = KKSongsPresentationCreator(template_file=os.getenv('TEMPLATE_FILE'))

SONGS_JSON_FILE = 'songs.json'

# Load dummy user data from environment variables
USER_DATA = {
    "username": os.getenv('USERNAME'),
    "password": bcrypt.generate_password_hash(os.getenv('PASSWORD')).decode('utf-8')
}

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

def is_logged_in():
    return session.get('logged_in')

def scrape_songs():
    base_url = "https://kksongs.org/songs/song_"
    urls = [f"{base_url}{chr(i)}.html" for i in range(ord('a'), ord('z') + 1)]
    songs = []
    
    for url in urls:
        print(f"Scraping {url}...")
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        for link in soup.find_all('a', href=True):
            print(link['href'])
            if link['href'].startswith("http://kksongs.org/songs/"):
                print(f"Found song: {link.text.strip()}")
                song_title = link.text.strip()
                songs.append({"title": song_title, "url": link['href']})

    print(f"Scraped {len(songs)} songs.")
    
    with open(SONGS_JSON_FILE, 'w') as f:
        json.dump(songs, f)
    
    return songs

def load_songs():
    if os.path.exists(SONGS_JSON_FILE):
        with open(SONGS_JSON_FILE, 'r') as f:
            return json.load(f)
    return scrape_songs()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if is_logged_in():
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        if username == USER_DATA['username'] and bcrypt.check_password_hash(USER_DATA['password'], password):
            session['logged_in'] = True
            flash('You are now logged in!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def index():
    if not is_logged_in():
        return redirect(url_for('login'))

    songs = load_songs()
    
    if request.method == 'POST':
        url = request.form.get('url')
        song_url = request.form.get('song_url')

        if url:
            song_url = url.strip()

        if song_url:
            print(f"Song URL: {song_url}")
            # Encode the song URL to make it safe for passing as a query parameter
            song_url_encoded = urllib.parse.quote(song_url, safe='')
            return redirect(url_for('create_presentation', song_url=song_url_encoded))

    return render_template('index.html', songs=songs)

@app.route('/download/<filename>')
def download_file(filename):
    if not is_logged_in():
        return redirect(url_for('login'))
    return send_file(f'extracted/{filename}', as_attachment=True)

@app.route('/create_presentation', methods=['GET','POST'])
def create_presentation():
    # Get the encoded song URL from the query parameters
    song_url_encoded = request.args.get('song_url')
    print(f"Creating presentation for song URL: {song_url_encoded}")
    # Decode the song URL to its original form
    song_url = urllib.parse.unquote(song_url_encoded)
    print(f"Decoded song URL: {song_url}")

    try:
        html_content = presentation_creator.fetch_html(song_url)
        title = presentation_creator.extract_title(html_content)
        lyrics, translations = presentation_creator.extract_lyrics_and_translation(html_content)
        output_file = f"extracted/{title}.pptx"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        presentation_creator.create_ppt(lyrics, translations, output_file)

        return redirect(url_for('download_file', filename=title + '.pptx'))

    except Exception as e:
        print(e)
        return render_template('index.html', songs=load_songs(), error=f"An error occurred: {e}")

if __name__ == '__main__':
    load_songs()
    app.run(debug=True)
