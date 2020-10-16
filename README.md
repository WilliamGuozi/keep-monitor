## Introduction


* Keep-monitor is monitoring tool for keep node
* It can monitor whether the container is down and the amount of peers in the container log
* The collected data can be saved to `graphite` , display alert through  `grafana` , and can be sent directly to Slack
* If you want to save to `graphite`, you can building `graphite` and `grafana` with my another blog: [https://www.cnblogs.com/William-Guozi/p/grafana-monitor.html](https://www.cnblogs.com/William-Guozi/p/grafana-monitor.html)

## Environmental preparation


* Generate the public and private keys on the server, and add them to the local authorization file
* The purpose of this operation is to facilitate in-container access to out-of-container commands
* If you already have a private key, you don't need to regenerate it

>Generate the public-private key pair and return it directly

```plain
ssh-keygen
```

>Add the public key to the local authorization file

```bash
cat .ssh/id_rsa.pub >> .ssh/authorized_keys
```

## Command for activate


* You need to change the following environment variables to start the script
* Replace `GRAPHITE_URL` with the value of your `graphite` address, which can be left blank
* Replace `SLACK_WEB_HOOK` with the value of your slack web hook address, which can be left blank
* Replace `CONTAINER_BEACON`  with the value of your beacon container name,  which can be left blank
* Replace `CONTAINER_ECDSA` with the value of your ECDSA container name, which can be left blank

>Start script  `start_keep-monitor.sh`

```bash
#!/bin/bash
#
# Created by William Guozi
#
# Get the docker image
DOCKER_IMAGE="${1:-williamguozi/keep-monitor:latest}"

# Determines if the container exists and deletes it
docker pull $DOCKER_IMAGE && \
docker ps -a | awk -F' ' '{print $NF}' | grep "keep-monitor" && \
docker stop "keep-monitor" &&
docker rm -f "keep-monitor" || \
echo "Image $DOCKER_IMAGE pull failed or No container keep-monitor."


docker run -d \
--name keep-monitor \
--restart always \
--network host \
-v /root/.ssh/id_rsa:/root/.ssh/id_rsa:ro \
-e GRAPHITE_URL="graphite.example.com" \
-e SLACK_WEB_HOOK="https://hooks.slack.com/services/xxxxxxxxx" \
-e CONTAINER_BEACON="keep-beacon" \
-e CONTAINER_ECDSA="keep-ecdsa" \
$DOCKER_IMAGE
```
* The peer count is detected three times by default, and slack alerts if it falls below 10

## Effect presentation
* The contents of the log
```
2020-09-11 09:19:13,872 INFO     main current thread_list: ['keep-beacon', 'keep-ecdsa']
2020-09-11 09:19:22,869 INFO     ssh -o StrictHostKeyChecking=no root@127.0.0.1 docker ps | grep keep-ecdsa | grep -v Restarting RECODE1: 0, OUTPUT1: a5ec9acd0bb2        keepnetwork/keep-ecdsa-client:v1.2.0-rc.4                               "/usr/local/bin/keep…"   24 hours ago        Up 2 hours          0.0.0.0:3920->3919/tcp                                          keep-ecdsa.
2020-09-11 09:19:22,870 INFO     ssh -o StrictHostKeyChecking=no root@127.0.0.1 docker logs --tail 400 keep-ecdsa 2>&1 |grep 'connected peers'|tail -n1 RECODE: 0, OUTPUT: 2020-09-11T09:18:51.197Z
2020-09-11 09:19:22,870 INFO     sending graphite data path: keep.testnet.keep-ecdsa_peers.pos-test-hk-02, metric: 248
2020-09-11 09:19:22,957 INFO     ssh -o StrictHostKeyChecking=no root@127.0.0.1 docker ps | grep keep-beacon | grep -v Restarting RECODE1: 0, OUTPUT1: c274f7bfc378        keepnetwork/keep-client:v1.3.0-rc.3                                     "/usr/local/bin/keep…"   8 days ago          Up 8 days           0.0.0.0:3919->3919/tcp                                          keep-beacon.
2020-09-11 09:19:22,957 INFO     ssh -o StrictHostKeyChecking=no root@127.0.0.1 docker logs --tail 400 keep-beacon 2>&1 |grep 'connected peers'|tail -n1 RECODE: 0, OUTPUT: 2020-09-11T09:19:21.953Z
2020-09-11 09:19:22,957 INFO     sending graphite data path: keep.testnet.keep-beacon_peers.pos-test-hk-02, metric: 190
```
* grafana data presentation
![img-w500](/images/202009111728.png)


* Alert message received by Slack
![img-w500](/images/202009111726.png)
