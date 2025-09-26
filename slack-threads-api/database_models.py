from datetime import datetime
from sqlalchemy import create_engine, Column, String, Text, DateTime, Boolean, Float, JSON, Index, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import Config

Base = declarative_base()

class SlackMessage(Base):
    __tablename__ = 'slack_messages'

    ts = Column(String(20), primary_key=True, index=True)
    channel_id = Column(String(20), nullable=False, index=True)
    thread_ts = Column(String(20), index=True)
    user_id = Column(String(20), index=True)
    username = Column(String(100))
    text = Column(Text)
    improved_message = Column(Text)  # Enhanced prompt with critical thinking elements
    message_type = Column(String(20))

    sent_timestamp = Column(Float, nullable=False)
    sent_datetime = Column(DateTime, nullable=False)

    retrieved_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    processed = Column(Boolean, default=False, index=True)
    processed_at = Column(DateTime)

    report_generated = Column(Boolean, default=False, index=True)
    report_generated_at = Column(DateTime)
    report_content = Column(Text)

    report_sent_to_slack = Column(Boolean, default=False, index=True)
    report_sent_at = Column(DateTime)
    report_thread_ts = Column(String(20))

    attachments = Column(JSON)
    blocks = Column(JSON)
    files = Column(JSON)
    reactions = Column(JSON)

    is_bot = Column(Boolean, default=False, index=True)
    bot_id = Column(String(20))

    edited_ts = Column(String(20))
    edited_user = Column(String(20))

    reply_count = Column(Integer, default=0)
    reply_users_count = Column(Integer, default=0)

    raw_data = Column(JSON)

    __table_args__ = (
        Index('idx_channel_thread', 'channel_id', 'thread_ts'),
        Index('idx_sent_datetime', 'sent_datetime'),
        Index('idx_retrieved_processed', 'retrieved_at', 'processed'),
        Index('idx_report_status', 'report_generated', 'report_sent_to_slack'),
    )

    def __repr__(self):
        return f"<SlackMessage(ts={self.ts}, user={self.username}, text={self.text[:50]}...)>"


class MessageRetrievalLog(Base):
    __tablename__ = 'message_retrieval_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    retrieval_started_at = Column(DateTime, nullable=False)
    retrieval_completed_at = Column(DateTime)

    channel_id = Column(String(20))

    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)

    total_messages_found = Column(Integer, default=0)
    new_messages_added = Column(Integer, default=0)
    duplicate_messages_skipped = Column(Integer, default=0)
    bot_messages_filtered = Column(Integer, default=0)

    status = Column(String(20))
    error_message = Column(Text)

    def __repr__(self):
        return f"<RetrievalLog(id={self.id}, channel={self.channel_id}, new={self.new_messages_added})>"


def get_database_engine():
    return create_engine(Config.SQLALCHEMY_DATABASE_URI, echo=False)

def get_session():
    engine = get_database_engine()
    Session = sessionmaker(bind=engine)
    return Session()

def init_database():
    engine = get_database_engine()
    Base.metadata.create_all(engine)
    print("Database tables created successfully")

if __name__ == "__main__":
    init_database()