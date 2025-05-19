# import getaccesstoken
#production main file
import requests
import db
import datetime
from datetime import timedelta
from zoneinfo import ZoneInfo
session = requests.session()


def get_untoced_leads(access_token):
    sales_Manager_names = [  #this list holds all the  sales manager names
    'Amare Gowda',
    'Ayush Dingane',
    'Digamber Pandey',
    'Pallavi Gattu',
    'Honnappa Dinni',
    'Kavya K B', 
    'Sandip Kumar Jena',
    'Sonu Sathyan']
    token = access_token
    for sales_manger in sales_Manager_names: 
        counter = 0 #initalize counter to zero
       
        sm_outstanding_call_count =  get_call_history(access_token=token,sm_name=sales_manger)
        print(sales_manger,'=>',sm_outstanding_call_count)
        
        if sm_outstanding_call_count > 9:
            print("sm already have full call count continue")
            continue
        remaining_call_bandwidth = 10-sm_outstanding_call_count 
        print("remaining bandwith->",remaining_call_bandwidth)
        url = f"https://www.zohoapis.com/crm/v7/Leads/search?criteria=(Owner:equals:{sales_manger})and(Lead_Status:in:Yet to be dialed)&per_page={remaining_call_bandwidth}&page=1"

        headers = {
        "Authorization":f"Zoho-oauthtoken {access_token}",
        }
        try:
            response = session.get(url=url,headers=headers)
            if response.status_code==204:
                print("pass")
                continue
            og_reesponse = response.json()
            data_list = og_reesponse['data']
            initial_date = datetime.datetime.now() #initalizing the initial call start time for the sm
            print("Lenght of lead list",len(data_list))
            for lead in data_list:
                if counter == 0 :            
                    prev_time = schedule_call(lead_id=lead['id'],lead_name=lead['Company'],owner_id=(lead['Owner'])['id'],token=token,date=initial_date)
                else:
                    prev_time =  schedule_call(lead_id=lead['id'],lead_name=lead['Company'],owner_id=(lead['Owner'])['id'],token=token,date=prev_time)
                counter+=1
            db.get_current_call_hsitory_collection().insert_one({"sm_name":sales_manger,"No_calls_scheduled":counter,"time":initial_date})
            print("No call scheduled for",sales_manger,counter)
            
        except Exception as e:
            print("error here->",e)
        print(' ')              


def get_call_history(access_token,sm_name):#this method will get the total scheduled call count and update it to the db
    url = f"https://www.zohoapis.com/crm/v2/Calls/search?criteria=Owner:equals:{sm_name}&per_page=100&page=1"
    headers = {
        "Authorization":f"Zoho-oauthtoken {access_token}"
    }
    call_history_dict = dict() #store the history of the past 4 hours consumed by monitoring system
    try:
        response = requests.get(url=url,headers=headers)
        if response.status_code == 204:
            return 0
        else:
            og_response = response.json().get('data')
            print(og_response)
            scheduled_call_count = 0
            overdue_call_count = 0
            overdue_call_list = list()
            completed_calls_count =0
            for call in og_response:
                if call.get('Call_Status') == "Scheduled":
                    scheduled_call_count+=1
                elif call.get('Call_Status') == "Overdue":
                    print("Im executing")
                    overdue_call_count+=1
                    overdue_call_list.append(call.get('What_Id')) 
                    print("This is the whatid",call.get('What_Id'))
                elif call.get('Call_Status') == "Completed":
                    completed_calls_count+=1
            utc = datetime.datetime.fromisoformat(str(datetime.datetime.now()))
            zone = utc.astimezone(ZoneInfo('Asia/Kolkata'))        
            call_history_dict.update({"sm_name":sm_name,"scheduled_call_count":scheduled_call_count,"overdue":{"overdue_call_count":overdue_call_count,"lead":overdue_call_list},"completed_calls_count":completed_calls_count,"date":zone.isoformat()})
            db.get_call_history_collection().insert_one(call_history_dict)
            print("Last 1 hour Call hsitory stored for processing Execution at",zone.isoformat())        
            return scheduled_call_count
    except Exception as e:
        print(e)

def schedule_call(lead_id,lead_name,owner_id,token,date):
    
    url = "https://www.zohoapis.com.zoho.com/crm/v2/Calls"
    time_delta = date+timedelta(minutes=25)# add the previous call date with 25 minutes
    utc = datetime.datetime.fromisoformat(str(time_delta))
    call_date = utc.astimezone(ZoneInfo('Asia/kolkata'))
    dt = call_date.replace(microsecond=0)
    payload = {
        "data": [
            {
            "Event_Title": "Call to be made",
            "Subject": f"call scheduled with client {lead_name}",
            "What_Id": lead_id,
            "Call_Type": "Outbound",
            "Call_Start_Time": str(dt.isoformat()),
            "Call_Purpose": "Prospecting",
            "Send_Notification": True,
            "$se_module": "Leads",
            "Owner": {
                "id":owner_id,
            }
            }
        ]
        }  
    header ={
        "Authorization":f"Zoho-oauthtoken {token}"
    }
        
    try:
         response = session.post(url=url,headers=header,json=payload)
         return dt  
    except Exception as e:
        print(e) 

def delete_last_hr_data():
    try:
        db.get_call_history_collection().delete_many({})
        print("deleted last hr call data")
    except Exception as e:
        print(e) 