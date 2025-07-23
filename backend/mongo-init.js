// MongoDB Initialization Script
// This script will be executed when MongoDB starts for the first time

// Switch to the application database
db = db.getSiblingDB('pego_database');

// Create application user with read/write permissions
db.createUser({
  user: 'pego_user',
  pwd: 'pego_password_change_this',
  roles: [
    {
      role: 'readWrite',
      db: 'pego_database'
    }
  ]
});

// Create indexes for better performance
db.users.createIndex({ "id": 1 }, { unique: true });
db.users.createIndex({ "email": 1 }, { sparse: true });
db.users.createIndex({ "phone": 1 }, { sparse: true });
db.users.createIndex({ "username": 1 }, { unique: true });

db.videos.createIndex({ "id": 1 }, { unique: true });
db.videos.createIndex({ "user_id": 1 });
db.videos.createIndex({ "competition_round": 1 });
db.videos.createIndex({ "view_count": -1 });
db.videos.createIndex({ "upload_date": -1 });

db.admin_users.createIndex({ "id": 1 }, { unique: true });
db.admin_users.createIndex({ "username": 1 }, { unique: true });

db.competition_rounds.createIndex({ "id": 1 }, { unique: true });
db.competition_rounds.createIndex({ "is_active": 1 });

db.credit_transactions.createIndex({ "user_id": 1 });
db.credit_transactions.createIndex({ "created_at": -1 });

db.video_interactions.createIndex({ "video_id": 1 });
db.video_interactions.createIndex({ "user_id": 1 });
db.video_interactions.createIndex({ "created_at": -1 });

print('Database initialization completed successfully!');