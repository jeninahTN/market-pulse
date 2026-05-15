from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, UniqueConstraint, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    fullname = Column(String, nullable=True)
    hashed_password = Column(String)
    is_new_user = Column(Boolean, default=True)
    google_id = Column(String, unique=True, index=True, nullable=True)

    monitored_crops = relationship("MonitoredCrop", back_populates="owner", cascade="all, delete-orphan")

class MonitoredCrop(Base):
    __tablename__ = "monitored_crops"

    id = Column(Integer, primary_key=True, index=True)
    crop_id = Column(String, index=True)
    region = Column(String, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="monitored_crops")

    # Prevent duplicate monitoring of same crop/region per user
    __table_args__ = (UniqueConstraint('crop_id', 'region', 'user_id', name='_user_crop_region_uc'),)

class MarketFeature(Base):
    __tablename__ = "market_features"

    date = Column(String, primary_key=True, index=True)
    temperature = Column(Integer)
    precipitation = Column(Integer)
    humidity = Column(Integer)
    sentiment_score = Column(Integer) # We'll store it as integer (score * 100) or Float if preferred. Float is better for sentiment.

class WeatherData(Base):
    __tablename__ = "weather_data"

    id = Column(Integer, primary_key=True, index=True)
    region = Column(String, index=True)
    temperature = Column(Float)
    humidity = Column(Float)
    precipitation = Column(Float)
    wind_speed = Column(Float, nullable=True)
    pressure = Column(Float, nullable=True)
    source = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    timestamp = Column(String, nullable=True)


class PriceObservation(Base):
    __tablename__ = "price_observations"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, index=True)
    crop = Column(String, index=True)
    market = Column(String, index=True)
    price = Column(Float)
    unit = Column(String, nullable=True)
    source = Column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint("date", "crop", "market", "source", name="_price_observation_uc"),
    )

class Price(Base):
    __tablename__ = "prices"

    id = Column(Integer, primary_key=True, index=True)
    crop_id = Column(String, index=True)
    region = Column(String, index=True)
    price = Column(Float)
    date = Column(String, index=True)
    source = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)

    __table_args__ = (
        UniqueConstraint("crop_id", "region", "date", "source", name="_price_uc"),
    )


class RegionalSignal(Base):
    __tablename__ = "regional_signals"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, index=True)
    region = Column(String, index=True)
    crop = Column(String, index=True)
    temperature = Column(Float)
    precipitation = Column(Float)
    humidity = Column(Float)
    sentiment_score = Column(Float)
    source = Column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint("date", "region", "crop", name="_regional_signal_uc"),
    )


class DataRefreshState(Base):
    __tablename__ = "data_refresh_state"

    name = Column(String, primary_key=True, index=True)
    refreshed_at = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, default="success")
    details = Column(String, nullable=True)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    token = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    contact = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False, index=True)
    used_at = Column(DateTime, nullable=True)


class SmsVerificationCode(Base):
    __tablename__ = "sms_verification_codes"

    phone = Column(String, primary_key=True, index=True)
    code = Column(String, nullable=False)
    attempts = Column(Integer, nullable=False, default=0)
    sent_count = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False, index=True)


class RateLimitCounter(Base):
    __tablename__ = "rate_limit_counters"

    key = Column(String, primary_key=True, index=True)
    count = Column(Integer, nullable=False, default=0)
    window_started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False, index=True)
