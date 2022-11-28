DEFAULT_SVC = {
    'api_version': 'v1',
    'kind': 'Service',
    'metadata': {'name': 'test-svc'},
    'spec': {
        'ports': [
            {
                'name': 'svc-port',
                'port': 80,
                'protocol': 'TCP',
                'targetPort': 80
            }
        ],
        'selector': {'app': 'test'}
    }
}

POD_WITH_ONE_CONTAINER = {
    'apiVersion': 'v1',
    'kind': 'Pod',
    'metadata': {
        'name': 'test-pod-one-container'
    },
    'spec': {
        'containers': [
            {
                'env': [{'name': 'TEXT', 'value': 'Servizio A'}],
                'image': 'local/test-image:latest',
                'name': 'container-a',
                'ports': [
                    {
                        'containerPort': 8000
                    },
                    {
                        'name': 'ottanta',
                        'containerPort': 80,
                        'protocol': 'TCP'
                    }
                ]
            }
        ]
    },
    'status': None}

POD_WITH_TWO_CONTAINER = {
    'apiVersion': 'v1',
    'kind': 'Pod',
    'metadata': {
        'labels': {'app': 'pod-a'},
        'name': 'test-pod-two-container'
    },
    'spec': {
        'containers': [
            {
                'env': [{'name': 'TEXT', 'value': 'Servizio A'}],
                'image': 'local/test-image:latest',
                'name': 'container-a',
                'ports': [
                    {'containerPort': 8000}
                ]
            },
            {
                'env': [{'name': 'TEXT', 'value': 'Servizio B'}],
                'image': 'local/test-image:latest',
                'name': 'container-b',
                'ports': [
                    {'containerPort': 8000}
                ]
            }
        ]
    },
    'status': None}

DEPLOYMENT_WITH_ONE_CONTAINER = {
    'apiVersion': 'extensions/v1beta1',
    'kind': 'Deployment',
    'metadata': {
        'labels': {'application': 'ftgo'},
        'name': "test-deployment"
    },
    'spec': {
        'replicas': 1,
        'selector': '',
        'strategy': {'rollingUpdate': {'maxUnavailable': 0}},
        'template': {
            'metadata': {
                'labels': {'svc': 'ftgo-cdc-service'},
                'name': "pod-c"
            },
            'spec': {
                'containers': [
                    {
                        'command': ['bash', '-c', 'java -Dsun.net.inetaddr.ttl=30 -jar *.jar'],
                        'image': 'eventuateio/eventuate-cdc-service:0.4.0.RELEASE',
                        'name': 'container-c',
                        'ports': [{'containerPort': 8080, 'name': 'httpport'}]}]
            }
        }
    }
}

DEPLOYMENT_WITH_TWO_CONTAINER = {
    'apiVersion': 'extensions/v1beta1',
    'kind': 'Deployment',
    'metadata': {
        'labels': {'application': 'ftgo'},
        'name': "test-deployment"
    },
    'spec': {
        'replicas': 1,
        'selector': '',
        'strategy': {'rollingUpdate': {'maxUnavailable': 0}},
        'template': {
            'metadata': {
                'labels': {'svc': 'ftgo-cdc-service'},
                'name': "container-c"
            },
            'spec': {
                'containers': [
                    {
                        'command': ['bash', '-c', 'java -Dsun.net.inetaddr.ttl=30 -jar *.jar'],
                        'image': 'eventuateio/eventuate-cdc-service:0.4.0.RELEASE',
                        'name': 'container-c',
                        'ports': [{'containerPort': 8080, 'name': 'httpport'}]
                    },
                    {
                        'image': 'eventuateio/eventuate-cdc-service:0.4.0.RELEASE',
                        'name': 'container-d',
                        'ports': [{'containerPort': 8080, 'name': 'httpport'}]
                    }
                ]
            }
        }
    }
}

REPLICASET_WITH_ONE_CONTAINER = {
    'apiVersion': 'apps/v1',
    'kind': 'ReplicaSet',
    'metadata': {
        'labels': {'app': 'guestbook', 'tier': 'frontend'},
        'name': 'frontend'
    },
    'spec': {
        'replicas': 3,
        'selector': {'matchLabels': {'tier': 'frontend'}},
        'template': {
            'metadata': {
                'labels': {'tier': 'frontend'},
                'name': 'test-replicaset'
            },
            'spec': {
                'containers': [{
                    'image': 'gcr.io/google_samples/gb-frontend:v3',
                    'name': 'php-redis',
                }],
            }
        }
    },
    'status': None
}

STATEFULSET_WITH_ONE_CONTAINER = {
    'apiVersion': 'apps/v1',
    'kind': 'StatefulSet',
    'metadata': {'name': 'test-statefulset'},
    'spec': {
        'minReadySeconds': 10,
        'replicas': 3,
        'selector': {'matchLabels': {'app': 'nginx'}},
        'serviceName': 'nginx',
        'template': {
            'metadata': {'labels': {'app': 'nginx'}},
            'spec': {
                'containers': [
                    {
                        'image': 'registry.k8s.io/nginx-slim:0.8',
                        'name': 'nginx',
                        'ports': [{'containerPort': 80, 'name': 'web'}],
                        'volumeMounts': [{'mountPath': '/usr/share/nginx/html', 'name': 'www'}]
                    }
                ],
            }},
        'volumeClaimTemplates': [{
            'metadata': {'name': 'www'},
            'spec': {
                'accessModes': ['ReadWriteOnce'],
                'resources': {'requests': {'storage': '1Gi'}},
                'storageClassName': 'my-storage-class'}}]},
    'status': None}


DEFAULT_SVC_INGRESS = {
    "apiVersion": "networking.k8s.io/v1",
    "kind": "Ingress",
    "metadata": {
        "name": "minimal - ingress"
    },
    "spec": {
        "ingressClassName": "nginx - example",
        "rules": [
            {
                "http" : {
                    "paths" : [
                        {
                            "path": "/testpath",
                            "pathType": "Prefix",
                            "backend" : {
                                "service" : {
                                    "name" : "test",
                                    "port" : {
                                        "number" : 80
                                    }
                                }
                            }
                        }
                    ]
                }
            }
        ]
    }
}