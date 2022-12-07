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

ISTIO_VIRTUAL_SVC_TIMEOUT_TEMPLATE = {
    "apiVersion": "networking.istio.io/v1alpha3",
    "kind": "VirtualService",
    "metadata": {
        # "name": ?
        # "namespace": ?
    },
    "spec": {
        # "hosts": [?],  -  name of the service to which add timeout
        "http": [
            {
                "route": [
                    {
                        "destination": {
                            # "host": ?  -  same as name in hosts
                        },
                        # "timeout": ?  -  format: 0s, 1.5s, etc..
                    }
                ]
            }
        ]
    }
}