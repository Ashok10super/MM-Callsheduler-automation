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
    delete_last_hr_data()
    for sales_manger in sales_Manager_names:
        print(sales_manger) 
        ignore_lead_dict = get_call_history(token,sales_manger)#call and get the history of calls before scehduling the calls
        print("Ignored_lead_list",ignore_lead_dict)
        url = f"https://crm.zoho.com/crm/v2/Leads/search?criteria=((Owner:equals:{sales_manger})and(Lead_Status:in:Yet to be dialed))&per_page=200&page=1"
        headers = {
            "Authorization":f"Zoho-oauthtoken {access_token}",
            }
        try:
            response = session.get(url=url,headers=headers)
            if response.status_code==204:
                print("No lead found for this sales manager")
                continue
            og_reesponse = response.json()
            data_list = og_reesponse['data']#After getting all the leads check wheather they are already scheduled or overdued
            initial_date = datetime.datetime.now(tz=ZoneInfo('Asia/Kolkata'))#sets the inital date to now
            counter = 0 #initalize the  page to one
            print("Lead len->",len(data_list))
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
                    elif prev_time.hour > 17:
                        print("scheduled call went over 17 hours")
                        break
                    else:
                        lead_id_list.append(lead['id'])
                        prev_time = schedule_call(id=lead['id'],lead_name=lead['Company'],owner_id=(lead['Owner'])['id'],token=token,date=prev_time)
                        counter+=1
            db.get_current_call_hsitory_collection().insert_one({"sm_name":sales_manger,"lead_id_list":lead_id_list,"No_calls_scheduled":counter,"time":initial_date})
            print("No call scheduled for",sales_manger,counter)
            print("already scheduled count",already_scheduled_count)
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
        ignore_account_id = get_call_history(access_token=token,sm_name=salesmanger)
        print(ignore_account_id)
        now = datetime.datetime.now().astimezone(ZoneInfo('Asia/Kolkata')).replace(microsecond=0).isoformat()
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
           initial_date = datetime.datetime.now(tz=ZoneInfo('Asia/Kolkata'))#sets the inital date to now
           counter = 0
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
                            prev_time = schedule_call(id=id,name=account['Account_Name'],module='Accounts',owner_id=(account['Owner'])['id'],token=token,date=initial_date)
                            counter+=1
                        elif prev_time.hour > 17:
                            print("scheduled call went over 17 hours")
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
    call_history_dict = dict() #store the history of the past 4 hours consumed by monitoring system
    try:
        response = requests.get(url=url,headers=headers)
        if response.status_code == 204:
            return {}# returning empty dictionary because no call found
        else:
            og_response = response.json().get('data')
            scheduled_call_count = 0
            overdue_call_count = 0
            overdue_scheduled_call_dict = dict()
            overdue_call_list=list()
            completed_calls_count =0
            for call in og_response:
                if call.get('Call_Status') == "Scheduled":
                    scheduled_call_count+=1
                    scheduled_call_id = call.get('What_Id').get('id')
                    overdue_scheduled_call_dict[scheduled_call_id] = sm_name
                elif call.get('Call_Status') == "Overdue":
                    overdue_call_count+=1
                    overdue_call_id = call.get('What_Id').get('id')
                    overdue_scheduled_call_dict[overdue_call_id] = sm_name
                    overdue_call_list.append(overdue_call_id)
                elif call.get('Call_Status') == "Completed":
                    completed_calls_count+=1
            ist_time = datetime.datetime.now(ZoneInfo("Asia/Kolkata")).replace(microsecond=0)

            # Convert to UTC (if you want to store in MongoDB)
            utc_time = ist_time.astimezone(ZoneInfo("UTC"))

            call_history_dict.update({"sm_name":sm_name,"scheduled_call_count":scheduled_call_count,"overdue_call":{"overdue_call_count":overdue_call_count,"overdue_call_id":overdue_call_list},"completed_calls_count":completed_calls_count,"time":utc_time})        
            db.get_call_history_collection().insert_one(call_history_dict)
            print("Last 1 hour Call history stored for processing Execution at",utc_time)  
            return overdue_scheduled_call_dict     
    except Exception as e:
        print(e)



def schedule_call(id,name,owner_id,module,token,date):
    
    url = "https://www.zohoapis.com/crm/v2/Calls"
    time_delta = date+timedelta(minutes=25)# add the previous call date with 25 minutes
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