# stdlib
import time
from hashlib import md5
import socket

# project
from checks import AgentCheck

# 3rd party
import simplejson as json
from httplib2 import Http, HttpLib2Error

class Riak(AgentCheck):
    SERVICE_CHECK_NAME = 'riak.can_connect'

    keys = [
        "vnode_gets",
        "vnode_puts",
        "vnode_index_reads",
        "vnode_index_writes",
        "vnode_index_deletes",
        "node_gets",
        "node_puts",
        "pbc_active",
        "pbc_connects",
        "memory_total",
        "memory_processes",
        "memory_processes_used",
        "memory_atom",
        "memory_atom_used",
        "memory_binary",
        "memory_code",
        "memory_ets",
        "read_repairs",
        "node_put_fsm_rejected_60s",
        "node_put_fsm_active_60s",
        "node_put_fsm_in_rate",
        "node_put_fsm_out_rate",
        "node_get_fsm_rejected_60s",
        "node_get_fsm_active_60s",
        "node_get_fsm_in_rate",
        "node_get_fsm_out_rate"
    ]

    stat_keys = [
        "node_get_fsm_siblings",
        "node_get_fsm_objsize",
        "node_get_fsm_time",
        "node_put_fsm_time"
      ]

    def __init__(self, name, init_config, agentConfig, instances=None):
        AgentCheck.__init__(self, name, init_config, agentConfig, instances)
        for k in ["mean", "median", "95", "99", "100"]:
            [self.keys.append(m + "_" + k) for m in self.stat_keys]

        self.prev_coord_redirs_total = -1

    def check(self, instance):
        url             = instance['url']
        default_timeout = self.init_config.get('default_timeout', 5)
        timeout         = float(instance.get('timeout', default_timeout))
        service_check_tags = ['url:%s' % url]

        try:
            h = Http(timeout=timeout)
            resp, content = h.request(url, "GET")
        except (socket.timeout, socket.error, HttpLib2Error) as e:
            self.service_check(self.SERVICE_CHECK_NAME, AgentCheck.CRITICAL,
                message="Unable to fetch Riak stats: %s" % str(e),
                tags=service_check_tags)

        if resp.status != 200:
            self.service_check(self.SERVICE_CHECK_NAME, AgentCheck.CRITICAL,
                tags=service_check_tags,
                message="Unexpected status of %s when fetching Riak stats, " \
                        "response: %s" % (resp.status, content))

        stats = json.loads(content)
        self.service_check(
            self.SERVICE_CHECK_NAME, AgentCheck.OK, tags=service_check_tags)

        [self.gauge("riak." + k, stats[k]) for k in self.keys if k in stats]

        coord_redirs_total = stats["coord_redirs_total"]
        if self.prev_coord_redirs_total > -1:
            count = coord_redirs_total - self.prev_coord_redirs_total
            self.gauge('riak.coord_redirs', count)

        self.prev_coord_redirs_total = coord_redirs_total
