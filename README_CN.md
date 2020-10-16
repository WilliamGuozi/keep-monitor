## 简介
* keep-monitor 是一个keep 的监控工具
* 它可以监控容器是否挂掉，容器日志中的peer数量
* 可将收集的数据保存到 `graphite` 里，通过 `grafana` 展示报警，也可以直接报警发送到slack中
* 如需保存至 `graphite` ，可参考我的另一篇博客 <https://www.cnblogs.com/William-Guozi/p/grafana-monitor.html> 建立 `graphite` 和 `grafana`（可选）


## 环境准备

* 服务器上生成公私钥, 并将公钥加入到本机授权文件
* 操作目的是方便容器内访问容器外命令
* 如已有私钥，则无需重新生成

> 生成公私钥对, 直接回车即可

```bash
ssh-keygen
```

> 将公钥加入到本机授权文件

```bash
cat .ssh/id_rsa.pub >> .ssh/authorized_keys
```


## 启动命令

* 启动脚本需要更改如下环境变量内容

* 替换 `GRAPHITE_URL` 的值为自己的 `graphite` 地址，可留空
* 替换 `SLACK_WEB_HOOK` 的值为自己的 slack web hook 地址，可留空
* 替换 `CONTAINER_BEACON` 的值为自己的 beacon 容器名称，可留空
* 替换 `CONTAINER_ECDSA` 的值为自己的 ecdsa 容器名称，可留空

> 启动脚本内容 `start_keep-monitor.sh`
```bash
#!/bin/bash
#
# Created by William Guozi
#
# 获取镜像
DOCKER_IMAGE="${1:-williamguozi/keep-monitor:latest}"

# 判断容器是否存在，并将其删除
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
* 默认检测三次peer数量低于10 则会报警到slack

## 效果展示
* 日志内容
```
2020-09-11 09:19:13,872 INFO     main current thread_list: ['keep-beacon', 'keep-ecdsa']
2020-09-11 09:19:22,869 INFO     ssh -o StrictHostKeyChecking=no root@127.0.0.1 docker ps | grep keep-ecdsa | grep -v Restarting RECODE1: 0, OUTPUT1: a5ec9acd0bb2        keepnetwork/keep-ecdsa-client:v1.2.0-rc.4                               "/usr/local/bin/keep…"   24 hours ago        Up 2 hours          0.0.0.0:3920->3919/tcp                                          keep-ecdsa.
2020-09-11 09:19:22,870 INFO     ssh -o StrictHostKeyChecking=no root@127.0.0.1 docker logs --tail 400 keep-ecdsa 2>&1 |grep 'connected peers'|tail -n1 RECODE: 0, OUTPUT: 2020-09-11T09:18:51.197Z
2020-09-11 09:19:22,870 INFO     sending graphite data path: keep.testnet.keep-ecdsa_peers.pos-test-hk-02, metric: 248
2020-09-11 09:19:22,957 INFO     ssh -o StrictHostKeyChecking=no root@127.0.0.1 docker ps | grep keep-beacon | grep -v Restarting RECODE1: 0, OUTPUT1: c274f7bfc378        keepnetwork/keep-client:v1.3.0-rc.3                                     "/usr/local/bin/keep…"   8 days ago          Up 8 days           0.0.0.0:3919->3919/tcp                                          keep-beacon.
2020-09-11 09:19:22,957 INFO     ssh -o StrictHostKeyChecking=no root@127.0.0.1 docker logs --tail 400 keep-beacon 2>&1 |grep 'connected peers'|tail -n1 RECODE: 0, OUTPUT: 2020-09-11T09:19:21.953Z
2020-09-11 09:19:22,957 INFO     sending graphite data path: keep.testnet.keep-beacon_peers.pos-test-hk-02, metric: 190
```
* grafana 数据展示
![img-w500](/images/202009111728.png)


* slack 收到的报警消息
![img-w500](/images/202009111726.png)
