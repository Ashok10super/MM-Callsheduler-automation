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
        if sales_manger == 'Pallavi Gattu':
            continue
        print(sales_manger) 
        ignore_lead_dict = get_call_history(token,sales_manger)#call and get the history of calls before scehduling the calls
        print("Ignored_lead_length",len(ignore_lead_dict))
        url = f"https://crm.zoho.com/crm/v2/Leads/search?criteria=((Owner:equals:{sales_manger})and(Lead_Status:in:Yet to be dialed))&per_page=200&page=1"
        headers = {
            "Authorization":f"Zoho-oauthtoken {access_token}",
            }
        try:
            response = session.get(url=url,headers=headers)
            if response.status_code==204:
                print("No lead found for this sales manager")
                continue
            og_response = response.json()
            data_list = og_response['data']#After getting all the leads check wheather they are already scheduled or overdued
            initial_date = datetime.datetime.now(tz=ZoneInfo('Asia/Kolkata'))#sets the inital date to now
            counter = 0 #initalize the  page to one
            print("Fetched lead len->",len(data_list))
            already_scheduled_count = 0
            lead_id_list = list()#stores all the call scheduled lead ids
            for lead in data_list:
                if  lead['id'] in ignore_lead_dict:
                    already_scheduled_count+=1
                else:
                    if counter == 0:
                        lead_id_list.append(lead['id'])
                        prev_time = schedule_call(id=lead['id'],name=lead['Company'],module='Leads',owner_id=(lead['Owner'])['id'],token=token,date=initial_date)
                        counter+=1
                    else:
                        if prev_time.hour >= 13:
                            print("scheduled call went over 1pm ")
                            break
                        lead_id_list.append(lead['id'])
                        prev_time = schedule_call(id=lead['id'],name=lead['Company'],module='Leads',owner_id=(lead['Owner'])['id'],token=token,date=prev_time)
                        counter+=1
            db.get_current_call_hsitory_collection().insert_one({"sm_name":sales_manger,"lead_id_list":lead_id_list,"No_calls_scheduled":counter,"time":initial_date})
            print("No call scheduled for",sales_manger,counter)
            print("Already scheduled count",already_scheduled_count)
            print("Last call scheduled time",prev_time)
        except Exception as e:
            print("error here->",e)
            print(' ')                         

def schedule_call_for_accounts(token):
    sales_Manager_names = [  #this list holds all the  sales manager names
    'Amare Gowda',
    'Ayush Dingane',
    'Digamber Pandey',
    'Pallavi Gattu',
    'Honnappa Dinni',
    'Kavya K B', 
    'Sandip Kumar Jena',
    'Sonu Sathyan']

    for salesmanger in sales_Manager_names:
        if salesmanger == 'Pallavi Gattu':
            continue
        ignore_account_id = get_call_history(access_token=token,sm_name=salesmanger)
        print("salesmanger",salesmanger)
        print("No of ignored calls-> ",len(ignore_account_id))
        now = f"{datetime.datetime.now().date().isoformat()}T14:00:00+05:30"
        url = f"https://crm.zoho.com/crm/v2/Accounts/search?criteria=((Owner:equals:{salesmanger})and(Status:in:Awareness,Attention,Assessment))&per_page=200&page=1"
        headers = {
        "Authorization":f"Zoho-oauthtoken {token}"
    }
        try:
           response = requests.get(url=url,headers=headers)
           if response.status_code == 204:
               print("No Account found for this manager",salesmanger)
               continue
           json_response = response.json()
           data = json_response['data']
           already_scheduled_call = 0
           initial_date = now#sets the initial date to now
           counter = 0
           l=0
           for account in data:
             call_back_time = account.get('Call_Back_Date_Time')
             if call_back_time!=None:
                time = datetime.datetime.now().date()
                call_back_time =datetime.datetime.fromisoformat(str(account.get('Call_Back_Date_Time'))).date()
                if call_back_time < time:
                    id = account.get('id')
                    if id in ignore_account_id:
                        already_scheduled_call+=1
                        continue
                    else:
                        if counter == 0:
                            prev_time = schedule_call(id=id,name=account['Account_Name'],module='Accounts',owner_id=(account['Owner'])['id'],token=token,date=datetime.datetime.fromisoformat(initial_date))
                            counter+=1
                        elif prev_time.hour >= 16:
                            print("scheduled call went over 6pm")
                            break
                        else:
                         prev_time = schedule_call(id=id,name=account['Account_Name'],module='Accounts',owner_id=(account['Owner'])['id'],token=token,date=prev_time)
                         counter+=1
           print("No of accounts fetched",len(data))   
           print("Already scheduled call count",already_scheduled_call)
           print("Scheduled call count",counter)         
        except Exception as e:
            print(e)
def get_call_history(access_token,sm_name):#this method will get the total scheduled call count and update it to the db
    url = f"https://www.zohoapis.com/crm/v2/Calls/search?criteria=(Owner:equals:{sm_name})and((Call_Status:equals:Overdue)or(Call_Status:equals:Scheduled))&per_page=200&page=1"
    headers = {
        "Authorization":f"Zoho-oauthtoken {access_token}"
    }
    try:
        response = requests.get(url=url,headers=headers)
        if response.status_code == 204:
            return {}# returning empty dictionary because no call found
        else:
            og_response = response.json().get('data')
            overdue_scheduled_call_dict = dict()
            overdue_call_list=list()
            for call in og_response:
                if call.get('Call_Status') == "Scheduled":
                    scheduled_call_id = call.get('What_Id').get('id')
                    overdue_scheduled_call_dict[scheduled_call_id] = sm_name
                elif call.get('Call_Status') == "Overdue":
                    overdue_call_id = call.get('What_Id').get('id')
                    overdue_scheduled_call_dict[overdue_call_id] = sm_name
            print("Last day scheduled completed and overdue calls id's saved for processing")
            return overdue_scheduled_call_dict     
    except Exception as e:
        print(e)

def schedule_call(id,name,owner_id,module,token,date):
    
    url = "https://www.zohoapis.com/crm/v2/Calls"
    time_delta = date+timedelta(minutes=10)# add the previous call date with 25 minutes
    utc = datetime.datetime.fromisoformat(str(time_delta))
    call_date = utc.astimezone(ZoneInfo('Asia/Kolkata'))
    dt = call_date.replace(microsecond=0)
    payload = {
        "data": [
            {
            "Event_Title": "Call to be made",
            "Subject": f"call scheduled with client {name}",
            "Call_Type": "Outbound",
            "Call_Start_Time": str(dt.isoformat()),
            "Call_Purpose": "Prospecting",
            "Send_Notification": True,
            "$se_module": module,
            "What_Id": id,
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