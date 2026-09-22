class Config:
    # SECRET_KEY
    SECRET_KEY = "smart-ticket-secret-key"
    
    SQLALCHEMY_DATABASE_URI = (
        "mysql+pymysql://root:@localhost/smart_ticket_db"
    )
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False