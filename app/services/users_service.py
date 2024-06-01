from pymongo import MongoClient, errors
from bson import ObjectId
from werkzeug.security import generate_password_hash
from pydantic import BaseModel
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from werkzeug.security import check_password_hash

# Replace the following with your actual connection string
MONGO_CONNECTION_STRING = "mongodb+srv://Osuna:Dedobleuge0102%21@transcription.lrwmixp.mongodb.net/<TranscriptionsLocal>?retryWrites=true&w=majority"

client = MongoClient(MONGO_CONNECTION_STRING)
db = client.get_database('TranscriptionsLocal')
users_collection = db.get_collection('users')

class User(BaseModel):
    email: str
    username: str
    password: str

def create_user(user: User):
    user_data = user.dict()
    existing_user = users_collection.find_one({"$or": [{"username": user_data['username']}, {"email": user_data['email']}]})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already exists.")
    hashed_password = generate_password_hash(user_data['password'])
    user_data['password'] = hashed_password
    try:
        result = users_collection.insert_one(user_data)
        return JSONResponse(status_code=200, content={"message": "User created successfully", "id": str(result.inserted_id), "username": user_data['username']})
    except errors.PyMongoError as e:
        print(f"An error occurred while creating the user: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while creating the user.")
    
def update_user(user_id: str, user: User):
    user_data = user.dict()
    hashed_password = generate_password_hash(user_data['password'])
    user_data['password'] = hashed_password
    try:
        result = users_collection.update_one({"_id": ObjectId(user_id)}, {"$set": user_data})
        if result.modified_count:
            return JSONResponse(status_code=200, content={"message": "User updated successfully", "id": user_id, "username": user_data['username']})
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except errors.PyMongoError as e:
        print(f"An error occurred while updating the user: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while updating the user.")
    

def is_user_logged_in(username: str, password: str):
    user = users_collection.find_one({"username": username})
    if user and check_password_hash(user['password'], password):
        return True
    return False