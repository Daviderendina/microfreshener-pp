import enum


class PENDING_OPS(enum.Enum):
    REMOVE_WORKLOAD_HOST_NETWORK = lambda x: x.set_host_network(False)
