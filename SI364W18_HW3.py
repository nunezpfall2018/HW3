#** Nunez,Priscilla 
#** SI 364 - Fall 2018
#** HW 3

#####################
#** Note: Code is my own, any students I have tutored using my code must include that I have 
#** helped tutor them on ALL homework assignments using my code in SI 206, SI 339 and SI 364. 
#** Please notify our GSIs and Professors.
#** ---> Tutor: Nunez, Priscilla 
#** (Include what assignment number here, also include the lines of code and what you learned by the code used.)
#####################

#** Import statements
#####################
from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, ValidationError
from wtforms.validators import Required, Length
from flask_sqlalchemy import SQLAlchemy

#**  Application configurations
###############################
app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string from si364'
#** Final Postgres database has been set up with my uniqname, plus HW3
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://priscillamnunez@localhost:5432/priscillaHW3"
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


#** App setup 
#############
db = SQLAlchemy(app)                                               #** For database use


class Tweet(db.Model):                                             #** Set the Tweet class model
    __tablename__ = 'tweets'                          
    id = db.Column(db.Integer, primary_key=True)                   #** Place the id (identifier)
    text = db.Column(db.String(280))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))     #** This if for the user that saved the tweet

    def __repr__(self):
        return '<Tweet %r>' % self.text

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username =  db.Column(db.String(64))
    display_name = db.Column(db.String(124))         

    def __repr__(self):
        return '<User %r>' % self.username


#** Set up Forms 
################
#** Set up a custom validation as requested
def two_words_check(form, field):
    if len(field.data.split(' ')) < 2:
        raise ValidationError('Display name is not at least 2 words.')

def not_start_with_check(form, field):
    if field.data[0] == "@":
        raise ValidationError('Username begins with @ sign -- leave off the @ for username!')


class TweetEntryForm(FlaskForm):
    text = StringField('Enter the text of the tweet (no more than 280 chars):',  validators=[Required(), Length(1, 280)])
    username = StringField('Enter the username of the twitter user (no "@"!):', validators=[Required(),  Length(1, 64), not_start_with_check])
    display_name = StringField('Enter the display name for the twitter user (must be at least 2 words)', validators=[Required(), Length(3, 124), two_words_check])
    submit = SubmitField('Submit')


#** Routes & view functions 
###########################
#** Error handling routes - included
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

#** Main route
##############

@app.route('/', methods=['GET', 'POST'])
def index():
    #** Initialize the form
    form = TweetEntryForm()

    #** Get the number of Tweets
    tweets = Tweet.query.all()
    num_tweets = len(tweets)                                              #** Used len as the builtin function that returns the length of the object.

    if request.method == 'POST' and form.validate_on_submit():
        username = form.username.data
        text = form.text.data
        display_name = form.display_name.data
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(username=username, display_name=display_name)
            
            try:
                db.session.add(user)
                db.session.commit()
            except SQLAlchemyError:
                db.session.rollback()

        existingTweet = Tweet.query.filter_by(user_id=user.id).filter_by(text= text).first()

        if existingTweet:
            flash("*** That tweet already exists from that user! ***")
            return redirect(url_for("see_all_tweets"))
        tweet = Tweet(text=text, user_id=user.id)
        
        try:
            db.session.add(tweet)
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()

        flash("Tweet successfully added")
        return redirect('/')                                              #** Alternative is the url_name redirect


    errors = [v for v in form.errors.values()]
    if len(errors) > 0:
        flash("!!!! ERRORS IN FORM SUBMISSION - " + str(errors))          #** Flash example Troy gave in class
    return render_template('index.html',form=form, num_tweets=num_tweets) #** Arguments to the render_template invocation to send data to index.html

@app.route('/all_tweets')
def see_all_tweets():
    all_tweets = []
    tweets = Tweet.query.all()                                           #** Pass all tweets. Troy suggested in Lecture.

    for tweet in tweets:
        user = User.query.filter_by(id=tweet.user_id).first()            #** Created a query for th tweets
        all_tweets.append([tweet.text, user.username])                   #** As well as username
    return render_template('all_tweets.html', all_tweets= all_tweets if len(all_tweets) else 0) #** Alternative would be all_tweets=tweets_users 

@app.route('/all_users')
def see_all_users():
    users = User.query.all()
    return render_template('all_users.html', users= users if len(users) else 0)   #** This view function successfully renders the template all_users.html, which is provided.

@app.route('/longest_tweet')                                             #** Created another route (no scaffolding provided) at /longest_tweet with a view function get_longest_tweet
def get_longest_tweet():

    longest_tweet = None
    tweets = Tweet.query.all()                                           #** Access object property by using print [tweet.text] (Troy)
    def extractText(elem):
        return len(elem.text)
    
    sorted_tweets = sorted(tweets, key=extractText, reverse=True)        #** Referenced lecture 5 for sorting
    
    if sorted_tweets[0]:
        user = User.query.filter_by(id=sorted_tweets[0].user_id).first()
        longest_tweet = {
            "tweet": sorted_tweets[0].text,
            "username": user.username,
            "display_name": user.display_name
        }
    return render_template('longest_tweet.html', longest_tweet=longest_tweet)


if __name__ == '__main__':
    db.create_all()                                                     #** Creates any defined models when you run the application
    app.run(use_reloader=True,debug=True) 
