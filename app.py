# 필요한 모듈 추가
from flask import Flask, render_template, request, redirect, url_for, session, abort, flash
from flask_sqlalchemy import SQLAlchemy

# Flask 애플리케이션 설정
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 세션용 시크릿 키
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'  # 데이터베이스 URI 설정
db = SQLAlchemy(app)

# 데이터베이스 모델 정의
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('posts', lazy=True))
    upvotes = db.Column(db.Integer, default=0)  # 추천 수 컬럼 추가
    downvotes = db.Column(db.Integer, default=0)  # 비추천 수 컬럼 추가

    def __repr__(self):
        return '<Post %r>' % self.title

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('comments', lazy=True))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    post = db.relationship('Post', backref=db.backref('comments', lazy=True))
    upvotes = db.Column(db.Integer, default=0)  # 추천 횟수
    downvotes = db.Column(db.Integer, default=0)  # 비추천 횟수

    def __repr__(self):
        return '<Comment %r>' % self.text

# 게시물 수정 페이지 라우트
@app.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
def edit_post(post_id):
    if 'username' not in session:
        return redirect(url_for('login'))  # 로그인되어 있지 않은 경우 로그인 페이지로 리디렉션
    post = Post.query.get_or_404(post_id)
    if post.user.username != session['username'] and session['username'] != 'admin':
        abort(403)  # 게시물 작성자 또는 어드민 계정이 아닌 경우 403 에러 반환
    
    if request.method == 'POST':
        post.title = request.form['title']
        post.content = request.form['content']
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('edit_post.html', post=post)

# 로그인
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None  # 에러 메시지 변수 추가
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['username'] = user.username
            return redirect(url_for('index'))
        else:
            error = '유저 이름 또는 비밀번호가 틀렸습니다'  # 로그인 실패시 에러 메시지 설정
            flash(error, 'error')  # 로그인 실패시 플래시 메시지 설정
    return render_template('login.html', error=error)  # 에러 메시지 전달

# 회원가입
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('이미 존재하는 유저 이름입니다', 'error')
            return redirect(url_for('register'))
        else:
            user = User(username=username, password=password)
            db.session.add(user)
            db.session.commit()
            flash('회원가입이 완료되었습니다', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

# 로그아웃
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

# 어드민 계정 추가
@app.route('/add_admin')
def add_admin():
    admin_username = 'admin'
    admin_password = 'admin_password'
    existing_admin = User.query.filter_by(username=admin_username).first()
    if existing_admin:
        flash('어드민 계정이 이미 존재합니다.', 'error')
    else:
        admin = User(username=admin_username, password=admin_password)
        db.session.add(admin)
        db.session.commit()
        flash('어드민 계정이 추가되었습니다.', 'success')
    return redirect(url_for('login'))

# 마이페이지 - 로그인한 사용자 정보 조회 및 수정
@app.route('/mypage', methods=['GET', 'POST'])
def mypage():
    if 'username' not in session:
        return redirect(url_for('login'))
    user = User.query.filter_by(username=session['username']).first()
    if request.method == 'POST':
        user.username = request.form['username']
        user.password = request.form['password']
        db.session.commit()
        return redirect(url_for('mypage'))
    return render_template('mypage.html', user=user)

# 메인 페이지 - 여행 기록 조회
@app.route('/')
def index():
    posts = Post.query.all()
    return render_template('index.html', posts=posts)

# 여행 기록 작성
@app.route('/write', methods=['GET', 'POST'])
def write():
    if 'username' not in session:
        return redirect(url_for('login'))  # 로그인되어 있지 않은 경우 로그인 페이지로 리디렉션
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        user = User.query.filter_by(username=session['username']).first()
        if user:  # 로그인된 사용자가 있을 경우에만 게시물 작성
            post = Post(title=title, content=content, user_id=user.id)  # user_id 추가
            db.session.add(post)
            db.session.commit()
            return redirect(url_for('index'))
    return render_template('write.html')

# 게시물 상세 보기 및 댓글 작성
@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def post(post_id):
    post = Post.query.get(post_id)
    if request.method == 'POST':
        if 'username' not in session:
            return redirect(url_for('login'))
        comment_text = request.form['comment']
        if comment_text.strip():  # 댓글이 공백이 아닌 경우에만 추가
            user = User.query.filter_by(username=session['username']).first()
            comment = Comment(text=comment_text, user=user, post_id=post.id)  # post_id를 post.id로 수정
            db.session.add(comment)
            db.session.commit()
        return redirect(url_for('post', post_id=post_id))
    return render_template('post.html', post=post)

# 게시물 삭제
@app.route('/post/<int:post_id>/delete', methods=['POST'])
def delete_post(post_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    post = Post.query.get_or_404(post_id)
    if post.user.username != session['username'] and session['username'] != 'admin':
        abort(403)  # 권한이 없는 경우 403 에러 반환
    
    # 해당 게시글에 연결된 모든 댓글을 삭제
    comments = Comment.query.filter_by(post_id=post_id).all()
    for comment in comments:
        db.session.delete(comment)
    db.session.commit()

    # 게시글 삭제
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('index'))

# 댓글 삭제
@app.route('/comment/<int:comment_id>/delete', methods=['POST'])  # POST 메소드로 변경
def delete_comment(comment_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    comment = Comment.query.get_or_404(comment_id)
    if comment.user.username != session['username'] and session['username'] != 'admin':
        abort(403)  # 권한이 없는 경우 403 에러 반환
    db.session.delete(comment)
    db.session.commit()
    flash('댓글이 삭제되었습니다.', 'success')
    return redirect(url_for('post', post_id=comment.post_id))

# 댓글 수정
@app.route('/comment/<int:comment_id>/edit', methods=['POST'])
def edit_comment(comment_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    comment = Comment.query.get_or_404(comment_id)
    if comment.user.username != session['username']:
        abort(403)  # 권한이 없는 경우 403 에러 반환
    edited_comment_text = request.form['edited_comment']
    comment.text = edited_comment_text
    db.session.commit()
    return redirect(url_for('post', post_id=comment.post_id))

# 게시글 추천 기능
@app.route('/post/<int:post_id>/upvote', methods=['POST'])
def upvote_post(post_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    post = Post.query.get_or_404(post_id)
    post.upvotes += 1
    db.session.commit()
    return redirect(request.referrer)  # 이전 페이지로 리디렉션

# 게시글 비추천 기능
@app.route('/post/<int:post_id>/downvote', methods=['POST'])
def downvote_post(post_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    post = Post.query.get_or_404(post_id)
    post.downvotes += 1
    db.session.commit()
    return redirect(request.referrer)  # 이전 페이지로 리디렉션

# 댓글 추천 기능
@app.route('/comment/<int:comment_id>/upvote', methods=['POST'])
def upvote_comment(comment_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    comment = Comment.query.get_or_404(comment_id)
    comment.upvotes += 1
    db.session.commit()
    return redirect(url_for('post', post_id=comment.post_id))

# 댓글 비추천 기능
@app.route('/comment/<int:comment_id>/downvote', methods=['POST'])
def downvote_comment(comment_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    comment = Comment.query.get_or_404(comment_id)
    comment.downvotes += 1
    db.session.commit()
    return redirect(url_for('post', post_id=comment.post_id))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
