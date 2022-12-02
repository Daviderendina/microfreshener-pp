# Template to which add metadata.name, metadata.labels, spec.ports, spec.selector
SERVICE_CLUSTERIP_TEMPLATE = {
    'api_version': 'v1',
    'kind': 'Service',
    'metadata': {
        # 'name': ?,
        # 'namespace' : ?
    },
    'spec': {
        'ports': [
            # {
            #    'name': ?,
            #    'port': ?,
            # }
        ],
        'selector': {
            # 'label'?: 'value'?
        }
    }
}

SERVICE_NODEPORT_TEMPLATE = {
    'api_version': 'v1',
    'kind': 'Service',
    'metadata': {
        # 'name': ?,
        # 'namespace' : ?
    },
    'spec': {
        'type': 'NodePort',
        'ports': [
            # {
            #    'name': ?,
            #    'port': ?,
            #    'targetPort': ? (uguale a port)
            #    'nodePort': ?
            # }
        ],
        'selector': {
            # 'label'?: 'value'?
        }
    }
}