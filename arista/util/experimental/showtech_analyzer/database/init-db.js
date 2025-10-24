// init-db.js

print('🚀 Starting database initialization...');

db.createCollection('sessions_metadata');
db.createCollection('session_data');

print('✅ Collections "sessions_metadata" and "session_data" created successfully.');
