from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.core.config import settings

# SQLAlchemy 2.0 Base class
class Base(DeclarativeBase):
    pass

# Create engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.DEBUG,  # Log SQL queries in debug mode
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database - create tables and enable pgvector"""
    from sqlalchemy import text
    from app.models.user import User
    from app.models.job import Job
    from app.models.resume import Resume
    
    # Create users table first (doesn't require pgvector)
    try:
        User.metadata.create_all(bind=engine, tables=[User.__table__])
        print("✅ Users table created/verified")
    except Exception as e:
        print(f"Note: Users table setup: {str(e)}")
    
    # Create jobs table (doesn't require pgvector)
    try:
        Job.metadata.create_all(bind=engine, tables=[Job.__table__])
        print("✅ Jobs table created/verified")
    except Exception as e:
        print(f"Note: Jobs table setup: {str(e)}")
    
    # Try to create resumes table - handle vector type gracefully
    try:
        # First try to enable pgvector extension
        with engine.connect() as conn:
            try:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()
                print("✅ pgvector extension enabled")
            except Exception as e:
                print(f"Note: pgvector extension not available: {str(e)}")
        
        # Try to create resumes table
        Resume.metadata.create_all(bind=engine, tables=[Resume.__table__])
        print("✅ Resumes table created/verified")
    except Exception as e:
        # If vector type doesn't exist, create table without vector column
        if "vector" in str(e).lower():
            print(f"Note: Creating resumes table without vector column (pgvector not available)")
            try:
                # Create a simplified version without vector column
                with engine.connect() as conn:
                    # First create the enum type if it doesn't exist
                    conn.execute(text("""
                        DO $$ BEGIN
                            CREATE TYPE resumestatus AS ENUM ('uploaded', 'parsing', 'parsed', 'processing', 'processed', 'error');
                        EXCEPTION
                            WHEN duplicate_object THEN null;
                        END $$;
                    """))
                    
                    # Check if table exists
                    table_exists = conn.execute(text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = 'resumes'
                        )
                    """)).scalar()
                    
                    if not table_exists:
                        # Create the table with JSONB embedding_vector (instead of vector type)
                        conn.execute(text("""
                            CREATE TABLE resumes (
                                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                                file_path VARCHAR(512) NOT NULL,
                                file_name VARCHAR(255) NOT NULL,
                                file_size VARCHAR(50),
                                file_type VARCHAR(50) NOT NULL,
                                parsed_data_json JSONB,
                                embedding_vector JSONB,
                                status resumestatus NOT NULL DEFAULT 'uploaded',
                                uploaded_by UUID NOT NULL REFERENCES users(id),
                                created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
                                updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
                            )
                        """))
                        print("✅ Resumes table created (with JSONB embedding_vector and enum type)")
                    else:
                        # Table exists, check if embedding_vector column exists
                        col_exists = conn.execute(text("""
                            SELECT EXISTS (
                                SELECT FROM information_schema.columns 
                                WHERE table_schema = 'public' 
                                AND table_name = 'resumes' 
                                AND column_name = 'embedding_vector'
                            )
                        """)).scalar()
                        
                        if not col_exists:
                            # Add embedding_vector as JSONB
                            conn.execute(text("ALTER TABLE resumes ADD COLUMN embedding_vector JSONB"))
                            print("✅ Added embedding_vector column as JSONB")
                    
                    conn.commit()
            except Exception as create_error:
                print(f"Error creating resumes table: {str(create_error)}")
        else:
            print(f"Error creating resumes table: {str(e)}")
    
    # Create all other tables (if any)
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Note: Some tables may require pgvector extension: {str(e)}")
