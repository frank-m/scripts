import json, requests, sys

URL = ""

data = "testing"
response = requests.post(URL, data)
print("%s/%s\n" % (URL, response.text))