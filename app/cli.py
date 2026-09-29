import click
from flask.cli import with_appcontext
from app import db
from app.models.user import User

@click.command('make-admin')
@click.argument('email')
@with_appcontext
def make_admin_command(email):
    """Elevate an existing user to Super Admin status."""
    user = User.query.filter_by(email=email).first()
    if not user:
        click.echo(f"Error: User with email '{email}' not found.")
        return
    
    if user.is_admin:
        click.echo(f"User '{email}' is already an admin.")
        return
        
    user.is_admin = True
    db.session.commit()
    click.echo(f"Success: User '{email}' has been elevated to Super Admin.")
