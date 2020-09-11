import logging
import os
import time
import commands
import datetime
import graphyte
import threading
import socket

from colorlog import ColoredFormatter

LOG_LEVEL = logging.DEBUG
LOGFORMAT = "%(asctime)s %(log_color)s%(levelname)-8s%(reset)s %(log_color)s%(message)s%(reset)s"

logging.root.setLevel(LOG_LEVEL)
formatter = ColoredFormatter(LOGFORMAT)
stream = logging.StreamHandler()
stream.setLevel(LOG_LEVEL)
stream.setFormatter(formatter)
log = logging.getLogger('pythonConfig')
log.setLevel(LOG_LEVEL)
log.addHandler(stream)

COMMAND_BASE = 'ssh -o StrictHostKeyChecking=no root@127.0.0.1 '


def get_keep_peer_count(PROJECT):
    keep_project = COMMAND_BASE + """docker logs --tail 400 %s 2>&1 |grep 'connected peers'|tail -n1""" % (PROJECT)
    RECODE, OUTPUT = commands.getstatusoutput(keep_project)
    # montior if container is down
    container_monitor = COMMAND_BASE + """docker ps | grep %s | grep -v Restarting""" % (PROJECT)
    RECODE1, OUTPUT1 = commands.getstatusoutput(container_monitor)
    log.info("{} RECODE1: {}, OUTPUT1: {}.".format(container_monitor, RECODE1, OUTPUT1))

    if RECODE1 == 0 and OUTPUT1 != '':
        log.info("{} RECODE: {}, OUTPUT: {}.".format(keep_project, RECODE, OUTPUT))
        if RECODE == 0 and OUTPUT != '':
            PEERS = OUTPUT.split('[[')
            PEERS = PEERS[1]
            PEERS = PEERS.split(']]')
            PEERS = PEERS[0]
            PEERS = PEERS.split()
            PEERSCOUNT = len(PEERS) + 1
        elif RECODE == 0 and OUTPUT == '':
            PEERSCOUNT = -2
        else:
            PEERSCOUNT = 0
    else:
        PEERSCOUNT = -1
    return PEERSCOUNT


def send_to_graphite(host, path, metric, prefix):
    graphyte.init(host, prefix=prefix)
    log.info("sending graphite data path: {}, metric: {}".format(path, metric))
    try:
        graphyte.send(path, metric)
    except Exception as e:
        log.error("{}".format(e))


def send_to_slack(slack_web_hook, title, color, message):
    '''color: good warning danger'''
    web = "https://dashboard.test.keep.network"
    ts = time.time()
    send_message = """curl -s -X POST -H 'Content-type: application/json' --data \
    '{
        "attachments": [
            {
                "color": "%s",
                "title": "%s",
                "title_link": "%s",
                "text": "%s",
                "image_url": "http://my-website.com/path/to/image.jpg",
                "thumb_url": "http://example.com/path/to/thumb.png",
                "footer": "Slack API",
                "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png",
                "ts": '%s'
            }
        ]
    }' %s""" % (color, title, web, message, ts, slack_web_hook)
    RECODE, OUTPUT = commands.getstatusoutput(send_message)
    log.info("{} RECODE: {}, OUTPUT: {}, message: {}.".format(send_to_slack.__name__, RECODE, OUTPUT, message))


def judge_peer_count(hostname, container, target_server):
    # get peers
    global thread_list
    ALERT_STATUS = False
    ERROR_COUNT = 0
    while True:
        PEERS_COUNT = get_keep_peer_count(container)
        if PEERS_COUNT == -2:
            # no log
            pass
        elif PEERS_COUNT == -1 and ALERT_STATUS is False:
            # container down
            mess_error = "Error, container {} is down.".format(container, PEERS_COUNT)
            send_to_slack(slack_web_hook, "{} alert".format(container), "danger", mess_error)
            ALERT_STATUS = True
        elif PEERS_COUNT < 10 and PEERS_COUNT != 0 and ALERT_STATUS is False and slack_web_hook != '' and ERROR_COUNT >= 3:
            mess_error = "Error, {} peers is less than {} for 3 minutes.".format(container, PEERS_COUNT)
            send_to_slack(slack_web_hook, "{} alert".format(container), "danger", mess_error)
            ALERT_STATUS = True
        else:
            ERROR_COUNT += 1

        if PEERS_COUNT > 10 and ALERT_STATUS is True and slack_web_hook != '':
            mess_ok = "Ok, {} peers {} is ok.".format(container, PEERS_COUNT)
            send_to_slack(slack_web_hook, "{} ok".format(container), "good", mess_ok)
            ALERT_STATUS = False
            ERROR_COUNT = 0

        if target_server != '' and PEERS_COUNT != -2:
            path = "{}.{}.{}.{}".format(PROJECT, NET, container + "_peers", hostname)
            send_to_graphite(target_server, path, PEERS_COUNT, 'pos')

        time.sleep(60)


if __name__ == "__main__":
    hostname = socket.gethostname()
    slack_web_hook = "SLACK_WEB_HOOK"
    target_server = "GRAPHITE_URL"
    PROJECT = 'keep'
    NET = 'testnet'
    container_list = ["CONTAINER_BEACON", "CONTAINER_ECDSA"]

    if slack_web_hook != '':
        log.info("{}, {} peers monitor start.".format(hostname, container_list))
        send_to_slack(slack_web_hook, "keep info", "good", "{}, {} peers monitor start.".format(hostname, container_list))

    thread_list = []
    while True:
        log.info("main current thread_list: {}".format(thread_list))
        for container in container_list:
            if container != '' and container not in thread_list:
                try:
                    thread_container_peer_count = threading.Thread(target=judge_peer_count, args=(hostname, container, target_server))
                    thread_container_peer_count.start()
                    thread_list.append(container)
                    log.info("main current thread_list: {}".format(thread_list))
                except:
                    log.error("Error. unable to start thread for {}.".format(container))
        time.sleep(300)
