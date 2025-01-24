import requests
import time

# base_url = 'http://192.168.1.37:5000/post_param'
base_url = 'http://47.243.226.166:5000/post_param'
headers = {'content-type': 'application/json'}


def send_alert(payload, alert_type="lark", duration="false"):
    payload["alert_type"] = alert_type
    payload["duration"] = duration
    # print(payload)
    response = requests.post(url=base_url, headers=headers, json=payload, timeout=10)
    try:
        response = response.json()
        # print(response)
    except:
        response = None
    
    time.sleep(1)
    return response


def send_alert_get(payload):
    url = base_url + payload
    response = requests.get(url=url, headers=headers, timeout=10)
    try:
        response = response.json()
    except:
        response = None

    return response


if __name__ == '__main__':
    payload = {"name": "IRON_HEIGHT_BEHIND",
               "message": "iron同步高度落后大于5",
               "hostname": ["ironfish301207", "ironfish301208", "ironfish301209"],
               }
    send_alert(payload, "call")