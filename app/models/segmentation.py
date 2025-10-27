from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from . import Base
import enum

class SegmentType(str, enum.Enum):
    STATIC = "static"
    DYNAMIC = "dynamic"
    BEHAVIORAL = "behavioral"
    DEMOGRAPHIC = "demographic"

class SegmentRule(Base):
    __tablename__ = "segment_rules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    segment_type = Column(String, nullable=False)  # SegmentType
    conditions = Column(JSON, nullable=False)  # Store rule conditions
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="segment_rules")

class ContactSegment(Base):
    __tablename__ = "contact_segments"

    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    segment_id = Column(Integer, ForeignKey("segment_rules.id"), nullable=False)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    added_by_rule = Column(Boolean, default=True)  # True if added by rule, False if manual

    contact = relationship("Contact")
    segment = relationship("SegmentRule")

class ContactTag(Base):
    __tablename__ = "contact_tags"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    color = Column(String, nullable=True)  # Hex color code
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="contact_tags")

class ContactTagAssignment(Base):
    __tablename__ = "contact_tag_assignments"

    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    tag_id = Column(Integer, ForeignKey("contact_tags.id"), nullable=False)
    added_at = Column(DateTime(timezone=True), server_default=func.now())

    contact = relationship("Contact")
    tag = relationship("ContactTag")

class ContactBehavior(Base):
    __tablename__ = "contact_behaviors"

    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    behavior_type = Column(String, nullable=False)  # open, click, reply, unsubscribe, etc.
    behavior_data = Column(JSON, nullable=True)  # Store behavior-specific data
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    contact = relationship("Contact")
    campaign = relationship("Campaign")
    message = relationship("Message")

class ContactEngagement(Base):
    __tablename__ = "contact_engagement"

    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    total_messages_sent = Column(Integer, default=0)
    total_messages_delivered = Column(Integer, default=0)
    total_messages_opened = Column(Integer, default=0)
    total_messages_clicked = Column(Integer, default=0)
    total_replies = Column(Integer, default=0)
    last_activity = Column(DateTime(timezone=True), nullable=True)
    engagement_score = Column(Integer, default=0)  # 0-100 score
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    contact = relationship("Contact")
