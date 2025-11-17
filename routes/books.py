# routes/books.py - Complete CRUD routes for books
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from extensions import db
from models import Book
import os
from datetime import datetime

books_bp = Blueprint('books', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER = 'static/uploads/covers'


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# CREATE - Add new book


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

        # Validation
        if not title or not author:
            flash('Title and Author are required!', 'danger')
            return redirect(url_for('books.add_book'))

        # Handle cover image upload
        cover_image = 'default-cover.jpg'
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

        # Create new book
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

        try:
            db.session.add(new_book)
            db.session.commit()
            flash('Book added successfully!', 'success')
            return redirect(url_for('books.list_books'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding book: {str(e)}', 'danger')
            return redirect(url_for('books.add_book'))

    return render_template('books/add_book.html')

# READ - List all books


@books_bp.route('/books')
@login_required
def list_books():
    books = Book.query.filter_by(user_id=current_user.id).order_by(
        Book.date_added.desc()).all()
    return render_template('books/list_books.html', books=books)

# READ - View single book


@books_bp.route('/books/<int:book_id>')
@login_required
def view_book(book_id):
    book = Book.query.filter_by(
        id=book_id, user_id=current_user.id).first_or_404()
    return render_template('books/view_book.html', book=book)

# UPDATE - Edit book


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
        book.rating = int(request.form.get('rating')
                          ) if request.form.get('rating') else None
        book.notes = request.form.get('notes')

        # Handle cover image update
        if 'cover_image' in request.files:
            file = request.files['cover_image']
            if file and file.filename != '' and allowed_file(file.filename):
                # Delete old image if not default
                if book.cover_image and book.cover_image != 'default-cover.jpg':
                    old_file = os.path.join(UPLOAD_FOLDER, book.cover_image)
                    if os.path.exists(old_file):
                        os.remove(old_file)

                # Save new image
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                file.save(filepath)
                book.cover_image = filename

        try:
            db.session.commit()
            flash('Book updated successfully!', 'success')
            return redirect(url_for('books.view_book', book_id=book.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating book: {str(e)}', 'danger')

    return render_template('books/edit_book.html', book=book)

# DELETE - Remove book


@books_bp.route('/books/<int:book_id>/delete', methods=['POST'])
@login_required
def delete_book(book_id):
    book = Book.query.filter_by(
        id=book_id, user_id=current_user.id).first_or_404()

    # Delete cover image if not default
    if book.cover_image and book.cover_image != 'default-cover.jpg':
        cover_path = os.path.join(UPLOAD_FOLDER, book.cover_image)
        if os.path.exists(cover_path):
            try:
                os.remove(cover_path)
            except Exception as e:
                print(f"Error deleting image: {e}")

    try:
        db.session.delete(book)
        db.session.commit()
        flash('Book deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting book: {str(e)}', 'danger')

    return redirect(url_for('books.list_books'))
