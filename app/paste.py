from flask import render_template, request, redirect, url_for, flash, session
from flask_login import current_user, login_required

from . import app, db, limiter
from .models import Paste

@app.route('/paste', methods=['GET', 'POST'])
@limiter.limit('30/minute')
def create_paste():
    if request.method == 'POST':
        content = request.form['content']
        p = Paste(content=content)
        if current_user.is_authenticated:
            p.owner = current_user
        else:
            p.session_id = session.get('sid')
        db.session.add(p)
        db.session.commit()
        return redirect(url_for('view_paste', paste_id=p.id))
    return render_template('paste.html')

@app.route('/paste/<int:paste_id>', methods=['GET', 'POST'])
def view_paste(paste_id):
    p = Paste.query.get_or_404(paste_id)
    if request.method == 'POST':
        if can_edit(p):
            p.content = request.form['content']
            db.session.commit()
            flash('Updated')
        else:
            flash('Access denied')
    return render_template('view_paste.html', paste=p)

@app.route('/paste/<int:paste_id>/delete')
@login_required
def delete_paste(paste_id):
    p = Paste.query.get_or_404(paste_id)
    if not can_edit(p):
        flash('Access denied')
    else:
        db.session.delete(p)
        db.session.commit()
        flash('Deleted')
    return redirect(url_for('index'))


def can_edit(paste):
    return current_user.is_authenticated and (paste.owner == current_user or current_user.is_admin)
