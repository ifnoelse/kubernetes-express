import socket, os, sys
from os import system

master_hostname = sys.argv[1]

hostname = sys.argv[2]

etcd_setting = {'path': '/etc/etcd', 'filename': 'etcd.conf',
                'config_map': {'ETCD_LISTEN_CLIENT_URLS': '"http://0.0.0.0:2379"',
                               'ETCD_ADVERTISE_CLIENT_URLS': '"http://0.0.0.0:2379"'}}

apiserver_setting = {'path': '/etc/kubernetes', 'filename': 'apiserver',
                     'config_map': {'KUBE_API_ADDRESS': '"--insecure-bind-address=0.0.0.0"',
                                    'KUBE_API_PORT': '"--port=8080"',
                                    'KUBE_ETCD_SERVERS': '"--etcd-servers=http://%s:2379"' % hostname,
                                    'KUBE_SERVICE_ADDRESSES': '"--service-cluster-ip-range=168.168.0.0/16"',
                                    'KUBE_ADMISSION_CONTROL': '"--admission-control=NamespaceLifecycle,NamespaceExists,LimitRanger,SecurityContextDeny,ResourceQuota"'}}

config_setting = {'path': '/etc/kubernetes', 'filename': 'config',
                  'config_map': {'KUBE_MASTER': '"--master=http://%s:8080"' % master_hostname}}

kubelet_setting = {'path': '/etc/kubernetes', 'filename': 'kubelet',
                   'config_map': {'KUBELET_ADDRESS': '"--address=0.0.0.0"',
                                  'KUBELET_HOSTNAME': '"%s"' % hostname,
                                  'KUBELET_ARGS': '--cluster-dns=168.168.0.100 --cluster-domain=cluster.local. --allow-privileged=true',
                                  'KUBELET_API_SERVER': '"--api-servers=http://%s:8080"' % master_hostname}}

flanneld_setting = {'path': '/etc/sysconfig', 'filename': 'flanneld',
                    'config_map': {'FLANNEL_ETCD_ENDPOINTS': '"http://%s:2379"' % master_hostname,
                                   'FLANNEL_ETCD_PREFIX': '"/atomic.io/network"',
                                   'FLANNEL_OPTIONS': '"--iface=enp0s8"'}}

docker_setting = {'path': '/etc/sysconfig', 'filename': 'docker',
                  'config_map': {
                      'OPTIONS': "'--selinux-enabled=false --insecure-registry registry.access.redhat.com --log-driver=journald --signature-verification=false'"}}


def config(setting):
    path = setting.get('path')
    filename = setting.get('filename')
    config_map = setting.get('config_map')
    file = path + '/' + filename
    backup_file = '/vagrant/.k8s/.backup/' + hostname  + file
    system('mkdir -p /vagrant/.k8s/.backup/%s%s' % (hostname, path))
    system('cp %s /vagrant/.k8s/.backup/%s%s' % (file, hostname, path))
    with open(backup_file) as fin, open(file, 'w') as conf:
        for ln in fin:
            match_key = set()
            for key, val in config_map.items():
                if ln.startswith(key):
                    match_key.add(key)
                    conf.write(key + '=' + val + os.linesep)
                    break
            else:
                conf.write(ln)
            config_map = {k: v for k, v in config_map.items() if k not in match_key}
        for key, val in config_map.items():
            conf.write(key + '=' + val + os.linesep)


if hostname == master_hostname:
    system('yum install -y kubernetes')
    system('yum install -y etcd')
    system('yum install -y flannel')
    config(etcd_setting)
    config(apiserver_setting)
    config(config_setting)
    config(flanneld_setting)
    config(docker_setting)
    system('systemctl daemon-reload')
    system('systemctl enable kube-apiserver')
    system('systemctl enable kube-controller-manager')
    system('systemctl enable kube-scheduler')
    system('systemctl enable etcd')
    system('systemctl enable flanneld')
    system('systemctl restart etcd')
    system('etcdctl set /atomic.io/network/config \'{ "Network": "10.0.0.0/16" }\'')
    system('systemctl restart flanneld')
    system('systemctl restart kube-apiserver')
    system('systemctl restart kube-controller-manager')
    system('systemctl restart kube-scheduler')
    # system('kubectl create -f /vagrant/kubernetes/dns')
    # system('kubectl create -f /vagrant/kubernetes/dashboard')
else:
    system('yum install -y kubernetes')
    system('yum install -y flannel')
    config(config_setting)
    config(kubelet_setting)
    config(flanneld_setting)
    config(docker_setting)
    system('systemctl daemon-reload')
    system('systemctl enable docker')
    system('systemctl enable kubelet')
    system('systemctl enable kube-proxy')
    system('systemctl enable flanneld')
    system('systemctl restart flanneld')
    system('systemctl restart docker')
    system('systemctl restart kubelet')
    system('systemctl restart kube-proxy')
