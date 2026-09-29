from app import db
from datetime import datetime, timezone

class Watchlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), nullable=False)
    company_name = db.Column(db.String(100))
    exchange = db.Column(db.String(50))
    currency = db.Column(db.String(10))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'symbol', name='unique_user_symbol'),
    )

    def __repr__(self):
        return f'<Watchlist {self.symbol} for User {self.user_id}>'

class SearchHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    searched_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<SearchHistory {self.symbol} at {self.searched_at}>'

class LoginHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    login_time = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(256))

    def __repr__(self):
        return f'<LoginHistory User {self.user_id} at {self.login_time}>'

class PortfolioItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    company_name = db.Column(db.String(100))
    quantity = db.Column(db.Float, nullable=False)
    purchase_price = db.Column(db.Float, nullable=False)
    purchase_date = db.Column(db.Date, nullable=True)
    currency = db.Column(db.String(10), default='USD')
    added_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<PortfolioItem {self.quantity} of {self.symbol} for User {self.user_id}>'

class PortfolioTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    portfolio_item_id = db.Column(db.Integer, db.ForeignKey('portfolio_item.id', ondelete='SET NULL'), nullable=True)
    symbol = db.Column(db.String(20), nullable=False)
    transaction_type = db.Column(db.String(10), nullable=False) # 'BUY' or 'SELL'
    quantity = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    transaction_date = db.Column(db.Date, nullable=False)
    realized_pl = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    condition = db.Column(db.String(20), nullable=False) # 'above' or 'below'
    target_price = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    triggered_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<Alert {self.symbol} {self.condition} {self.target_price} for User {self.user_id}>'


class VirtualAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    initial_balance = db.Column(db.Numeric(20, 2), nullable=False, default=1000000.00)
    current_cash = db.Column(db.Numeric(20, 2), nullable=False, default=1000000.00)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class VirtualPosition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('virtual_account.id', ondelete='CASCADE'), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Numeric(20, 4), nullable=False, default=0)
    avg_price = db.Column(db.Numeric(20, 2), nullable=False, default=0)
    
    __table_args__ = (
        db.UniqueConstraint('account_id', 'symbol', name='unique_account_symbol'),
    )

class VirtualOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('virtual_account.id', ondelete='CASCADE'), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    order_type = db.Column(db.String(10), nullable=False) # \'BUY\' or \'SELL\'
    quantity = db.Column(db.Numeric(20, 4), nullable=False)
    execution_price = db.Column(db.Numeric(20, 2), nullable=False)
    transaction_value = db.Column(db.Numeric(20, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='COMPLETED')
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class StockCache(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), nullable=False, unique=True, index=True)
    company_name = db.Column(db.String(100), nullable=True)
    exchange = db.Column(db.String(20), nullable=True, index=True)
    sector = db.Column(db.String(50), nullable=True, index=True)
    
    price = db.Column(db.Numeric(20, 2), nullable=True)
    market_cap = db.Column(db.Numeric(30, 2), nullable=True, index=True)
    pe_ratio = db.Column(db.Numeric(10, 2), nullable=True, index=True)
    volume = db.Column(db.BigInteger, nullable=True, index=True)
    
    last_updated = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class UserSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    preferred_currency = db.Column(db.String(10), default='USD')
    theme = db.Column(db.String(20), default='auto')
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class FinancialGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    target_amount = db.Column(db.Numeric(20, 2), nullable=False)
    current_savings = db.Column(db.Numeric(20, 2), default=0.0)
    monthly_contribution = db.Column(db.Numeric(20, 2), default=0.0)
    target_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class CMSContent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    title = db.Column(db.String(200), nullable=True)
    value = db.Column(db.Text, nullable=True)
    is_published = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class VirtualWalletTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('virtual_account.id', ondelete='CASCADE'), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False) # DEPOSIT, WITHDRAWAL, ADJUSTMENT
    amount = db.Column(db.Numeric(20, 2), nullable=False)
    resulting_balance = db.Column(db.Numeric(20, 2), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class PlatformSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    maintenance_mode = db.Column(db.Boolean, default=False, nullable=False)
    ai_analyst_enabled = db.Column(db.Boolean, default=True, nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    @classmethod
    def get_settings(cls):
        settings = cls.query.get(1)
        if not settings:
            settings = cls(id=1)
            db.session.add(settings)
            db.session.commit()
        return settings

