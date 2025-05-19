import pymongo
import dotenv
import os
dotenv.load_dotenv(override=True)

def get_db():
    try:
        mongo = pymongo.MongoClient(os.getenv("DATABASE_URL"))
        db = mongo['MMTESTDB']
        return db
    except Exception as e:
        print(e)    

def get_call_history_collection():
    try:
        db = get_db()
        coll = db['Callhistory']
        return coll
    except Exception as e:
        print(e)

def get_current_call_hsitory_collection():
    try:
        db = get_db()
        coll = db['currentcallhistory']
        return coll
    except Exception as e:
        print(e)  