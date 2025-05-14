import time
import requests
import datetime
def main():
  print("script is running at",datetime.datetime.now())
  payload = {
    "data":"came from server"
  }

  response = requests.post('https://webhook.site/abaaab82-edb7-4307-ad33-f5f39018747e',data=payload)

  if response.status_code == 200:
    print("cron job work successfull")
  else:
    print("cron job failed")

if __name__ == "__main__":
 main()