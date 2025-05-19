import db

#not for production ryt now
def monitor_and_send_notification():
   try:
    sm_performance = db.get_call_history_collection().find({})
    for doc in sm_performance:
      overdue_count = (doc['overdue'])['overdue_call_count']
      if overdue_count>0:
       print(doc['sm_name'],overdue_count)  
   except Exception as e:
     print(e)

