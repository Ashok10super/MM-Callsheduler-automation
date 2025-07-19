import getaccesstoken
import callscheduler



def main():#This main function is the top level function in the function chain will execute the sub functions
    token = getaccesstoken.get_access_token()
    callscheduler.get_untoced_leads(token)
    callscheduler.schedule_call_for_accounts(token)

if __name__ == "__main__":
   main()