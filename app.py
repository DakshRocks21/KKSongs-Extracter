from flask import Flask, request, render_template, redirect, url_for, send_file, session, flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from flask_bcrypt import Bcrypt
import os
from KKSongsPresentationCreator import KKSongsPresentationCreator
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
bcrypt = Bcrypt(app)
presentation_creator = KKSongsPresentationCreator(template_file=os.getenv('TEMPLATE_FILE'))

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

    if request.method == 'POST':
        url = request.form['url'].strip()
        if not presentation_creator.validate_url(url):
            return render_template('index.html', error="Invalid URL. Please ensure the URL is from 'https://kksongs.org/songs/' and ends with '.html'.")

        try:
            html_content = presentation_creator.fetch_html(url)
            title = presentation_creator.extract_title(html_content)
            lyrics, translations = presentation_creator.extract_lyrics_and_translation(html_content)
            output_file = f"extracted/{title}.pptx"
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            presentation_creator.create_ppt(lyrics, translations, output_file)

            return redirect(url_for('download_file', filename=title + '.pptx'))

        except Exception as e:
            return render_template('index.html', error=f"An error occurred: {e}")
    
    return render_template('index.html')

@app.route('/download/<filename>')
def download_file(filename):
    if not is_logged_in():
        return redirect(url_for('login'))
    return send_file(f'extracted/{filename}', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
