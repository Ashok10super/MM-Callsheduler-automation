import getaccesstoken
import callscheduler
import callmonitoragent

def main():#This main function is the top level function in the function chain will execute the sub functions
   token = getaccesstoken.get_access_token()
   callscheduler.delete_last_hr_data()
   callscheduler.get_untoced_leads(token)
   #callmonitoragent.monitor_and_send_notification()


if __name__ == "__main__":
   main()