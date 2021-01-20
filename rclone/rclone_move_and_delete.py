import argparse
from datetime import date
from os import system
import http.client
import urllib
import requests


def getArgs(argv=None):
    parser = argparse.ArgumentParser(
        description='Move Takeout file from source to target with Rclone and remove old file from b2')
    parser.add_argument(
        "-source", help="Please specifiy the source folder.", required=True)
    parser.add_argument(
        "-target", help="Please specify the target folder", required=True)
    parser.add_argument(
        "-logpath", help="Please specify the path to save the log in, not the logname", required=True)
    parser.add_argument(
        "-pasteurl", help="Please specify the url to the pastebin server", required=True)
    parser.add_argument(
        "-pushover_appkey", help="Please specify the url to the pushover.net appkey", required=True)
    parser.add_argument(
        "-pushover_userkey", help="Please specify the url to the pushover.net userkey", required=True)
    return parser.parse_args(argv)


def rclone_move_file(source, target, log):
    command = "rclone move %s %s --transfers 32 --log-level INFO --log-file %s" % (
        source, target, log)
    rclone_move = system(command)
    return rclone_move


def rclone_delete_old_files(remote, log):
    command = "rclone delete --min-age 30d %s --log-level INFO --log-file %s" % (
        remote, log)
    rclone_delete = system(command)
    return rclone_delete


def upload_logfile_pastebin(url, log):
    with open(log, 'r') as file:
        logfile = file.read()
    response = requests.post(url, logfile)
    return response.text


def create_message(source, target, pastebin_url, exitcode):
    message = "rclone_move_and_delete.py tried to move files from %s to %s. The execution ended with exit code %s. Please find the full logfile here: %s" % (
        source, target, exitcode, pastebin_url)
    return message


def send_push_message(message, pushover_appkey, pushover_userkey):
    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
                 urllib.parse.urlencode({
                     "token": pushover_appkey,
                     "user": pushover_userkey,
                     "message": message,
                 }), {"Content-type": "application/x-www-form-urlencoded"})
    conn.getresponse()


if __name__ == "__main__":
    args = getArgs()

    exitcode = 0
    date_today = date.today().strftime("%Y-%m-%d")
    log = args.logpath.rstrip('/') + "/%s_to_%s_%s.log" % (
        args.source.split(':', 1)[0], args.target.split(':', 1)[0], date_today)

    rclone_move_exitcode = rclone_move_file(args.source, args.target, log)

    if rclone_move_exitcode == 0:
        rclone_delete_exitcode = rclone_delete_old_files(args.target, log)
        if rclone_delete_exitcode == 1:
            exitcode = 1
    else:
        exitcode = 1

    pastebin_url = upload_logfile_pastebin(args.pasteurl, log)
    message = create_message(args.source, args.target, pastebin_url, exitcode)
    send_push_message(message, args.pushover_appkey, args.pushover_userkey)
