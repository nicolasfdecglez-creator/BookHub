from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import Book
from extensions import db
from werkzeug.utils import secure_filename
from sqlalchemy import or_, func
import os
from datetime import datetime

books_bp = Blueprint('books', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER = 'static/uploads/covers'


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@books_bp.route('/books')
@login_required
def list_books():
    search_query = request.args.get('search', '').strip()
    genre_filter = request.args.get('genre', '')
    status_filter = request.args.get('status', '')
    rating_filter = request.args.get('rating', '')
    sort_by = request.args.get('sort', 'date_added')

    query = Book.query.filter_by(user_id=current_user.id)

    if search_query:
        query = query.filter(
            or_(
                Book.title.ilike(f'%{search_query}%'),
                Book.author.ilike(f'%{search_query}%')
            )
        )

    if genre_filter:
        query = query.filter(Book.genre == genre_filter)

    if status_filter:
        query = query.filter(Book.status == status_filter)

    if rating_filter:
        query = query.filter(Book.rating == int(rating_filter))


    if sort_by == 'title':
        query = query.order_by(func.lower(Book.title).asc())
    elif sort_by == 'author':
        query = query.order_by(func.lower(Book.author).asc())
    elif sort_by == 'rating':
        query = query.order_by(Book.rating.desc().nullslast())
    else:
        query = query.order_by(Book.date_added.desc())

    books = query.all()

    all_books = Book.query.filter_by(user_id=current_user.id).all()
    genres = sorted(set(book.genre for book in all_books if book.genre))
    statuses = ['To Read', 'Reading', 'Completed']

    return render_template('books/list_books.html',
                           books=books,
                           genres=genres,
                           statuses=statuses,
                           current_search=search_query,
                           current_genre=genre_filter,
                           current_status=status_filter,
                           current_rating=rating_filter,
                           current_sort=sort_by)


@books_bp.route('/books/add', methods=['GET', 'POST'])
@login_required
def add_book():
    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        genre = request.form.get('genre')
        status = request.form.get('status', 'To Read')
        rating = request.form.get('rating')
        notes = request.form.get('notes')

        cover_image = 'img/default-cover.jpg'
        if 'cover_image' in request.files:
            file = request.files['cover_image']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                file.save(filepath)
                cover_image = filename

        new_book = Book(
            title=title,
            author=author,
            genre=genre,
            status=status,
            rating=int(rating) if rating else None,
            notes=notes,
            cover_image=cover_image,
            user_id=current_user.id
        )

        db.session.add(new_book)
        db.session.commit()

        flash('Book added successfully!', 'success')
        return redirect(url_for('books.list_books'))

    return render_template('books/add_book.html')


@books_bp.route('/books/<int:book_id>')
@login_required
def view_book(book_id):
    book = Book.query.filter_by(
        id=book_id, user_id=current_user.id).first_or_404()
    return render_template('books/view_book.html', book=book)


@books_bp.route('/books/<int:book_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_book(book_id):
    book = Book.query.filter_by(
        id=book_id, user_id=current_user.id).first_or_404()

    if request.method == 'POST':
        book.title = request.form.get('title')
        book.author = request.form.get('author')
        book.genre = request.form.get('genre')
        book.status = request.form.get('status')
        rating = request.form.get('rating')
        book.rating = int(rating) if rating else None
        book.notes = request.form.get('notes')

        if 'cover_image' in request.files:
            file = request.files['cover_image']
            if file and file.filename != '' and allowed_file(file.filename):
                if book.cover_image != 'img/default-cover.jpg':
                    old_filepath = os.path.join(
                        UPLOAD_FOLDER, book.cover_image)
                    if os.path.exists(old_filepath):
                        os.remove(old_filepath)

                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                file.save(filepath)
                book.cover_image = filename

        db.session.commit()
        flash('Book updated successfully!', 'success')
        return redirect(url_for('books.view_book', book_id=book.id))

    return render_template('books/edit_book.html', book=book)


@books_bp.route('/books/<int:book_id>/delete', methods=['POST'])
@login_required
def delete_book(book_id):
    book = Book.query.filter_by(
        id=book_id, user_id=current_user.id).first_or_404()

    if book.cover_image != 'img/default-cover.jpg':
        filepath = os.path.join(UPLOAD_FOLDER, book.cover_image)
        if os.path.exists(filepath):
            os.remove(filepath)

    db.session.delete(book)
    db.session.commit()

    flash('Book deleted successfully!', 'success')
    return redirect(url_for('books.list_books'))


@books_bp.route('/books/statistics')
@login_required
def statistics():
    books = Book.query.filter_by(user_id=current_user.id).all()

    total_books = len(books)
    completed_books = len([b for b in books if b.status == 'Completed'])
    reading_books = len([b for b in books if b.status == 'Reading'])
    to_read_books = len([b for b in books if b.status == 'To Read'])

    genre_counts = {}
    for book in books:
        if book.genre:
            genre_counts[book.genre] = genre_counts.get(book.genre, 0) + 1

    rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    rated_books = [b for b in books if b.rating]
    for book in rated_books:
        rating_counts[book.rating] = rating_counts.get(book.rating, 0) + 1

    avg_rating = sum(b.rating for b in rated_books) / \
        len(rated_books) if rated_books else 0

    top_rated = sorted([b for b in books if b.rating],
                       key=lambda x: x.rating, reverse=True)[:5]

    recent_books = sorted(books, key=lambda x: x.date_added, reverse=True)[:5]

    return render_template('books/statistics.html',
                           total_books=total_books,
                           completed_books=completed_books,
                           reading_books=reading_books,
                           to_read_books=to_read_books,
                           genre_counts=genre_counts,
                           rating_counts=rating_counts,
                           avg_rating=avg_rating,
                           top_rated=top_rated,
                           recent_books=recent_books)
