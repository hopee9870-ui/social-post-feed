from flask import Flask, render_template, redirect, url_for, request, session, flash
import json
import os
import markdown
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this in production

# Ensure data directory exists
os.makedirs('data', exist_ok=True)

# Initialize data files if they don't exist
if not os.path.exists('data/accounts.json'):
    with open('data/accounts.json', 'w') as f:
        json.dump({}, f)

if not os.path.exists('data/posts.json'):
    with open('data/posts.json', 'w') as f:
        json.dump([], f)

# Helper functions
def load_accounts():
    with open('data/accounts.json', 'r') as f:
        return json.load(f)

def save_accounts(accounts):
    with open('data/accounts.json', 'w') as f:
        json.dump(accounts, f)

def load_posts():
    with open('data/posts.json', 'r') as f:
        return json.load(f)

def save_posts(posts):
    with open('data/posts.json', 'w') as f:
        json.dump(posts, f)

# Routes
@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard', username=session['username']))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        accounts = load_accounts()
        
        if username in accounts and accounts[username]['password'] == password:
            session['username'] = username
            return redirect(url_for('dashboard', username=username))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        accounts = load_accounts()
        
        if username in accounts:
            flash('Username already exists')
        elif password != confirm_password:
            flash('Passwords do not match')
        else:
            accounts[username] = {
                'password': password,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            save_accounts(accounts)
            flash('Account created successfully')
            return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/<username>/dashboard')
def dashboard(username):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if session['username'] != username:
        flash('You do not have permission to access this dashboard')
        return redirect(url_for('dashboard', username=session['username']))
    
    posts = load_posts()
    user_posts = [post for post in posts if post['author'] == username]
    
    return render_template('dashboard.html', 
                          username=username, 
                          posts=user_posts, 
                          total_posts=len(user_posts))

@app.route('/<username>/editor/<post_id>', methods=['GET', 'POST'])
def editor(username, post_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if session['username'] != username:
        flash('You do not have permission to edit this post')
        return redirect(url_for('dashboard', username=session['username']))
    
    posts = load_posts()
    post = None
    
    # Find the post to edit
    for p in posts:
        if p['id'] == post_id:
            post = p
            break
    
    if post is None and post_id != 'new':
        flash('Post not found')
        return redirect(url_for('dashboard', username=username))
    
    if request.method == 'POST':
        if post_id == 'new':
            # Create new post
            new_post = {
                'id': str(len(posts) + 1),
                'author': username,
                'title': request.form['title'],
                'content': request.form['content'],
                'likes': 0,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            posts.append(new_post)
            save_posts(posts)
            flash('Post created successfully')
            return redirect(url_for('view_post', post_id=new_post['id']))
        else:
            # Update existing post
            post['title'] = request.form['title']
            post['content'] = request.form['content']
            post['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            save_posts(posts)
            flash('Post updated successfully')
            return redirect(url_for('view_post', post_id=post_id))
    
    return render_template('editor.html', post=post, username=username)

@app.route('/<post_id>')
def view_post(post_id):
    posts = load_posts()
    post = None
    
    for p in posts:
        if p['id'] == post_id:
            post = p
            break
    
    if post is None:
        flash('Post not found')
        return redirect(url_for('index'))
    
    # Convert markdown to HTML
    content_html = markdown.markdown(post['content'])
    
    # Check if current user is the author
    is_author = 'username' in session and session['username'] == post['author']
    
    return render_template('post_view.html', 
                          post=post, 
                          content=content_html, 
                          is_author=is_author)

@app.route('/like/<post_id>', methods=['POST'])
def like_post(post_id):
    posts = load_posts()
    
    for post in posts:
        if post['id'] == post_id:
            post['likes'] += 1
            break
    
    save_posts(posts)
    return redirect(url_for('view_post', post_id=post_id))

if __name__ == '__main__':
    app.run(debug=True)