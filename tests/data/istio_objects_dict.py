VIRTUAL_SERVICE_TIMEOUT = {
    'apiVersion': 'networking.istio.io/v1alpha3',
    'kind': 'VirtualService',
    'metadata': {'name': 'reviews'},
    'spec': {
        'hosts': ['host1', 'host2'],
        'http': [
            {
                'route': [{'destination': {'host': 'destination1', 'subset': 'v2'}}],
                'timeout': '0.5s'
            },
            {
                'route': [{'destination': {'host': 'destination2'}}],
                'timeout': '2s'
            }
        ]
    }
}

GATEWAY = {
    "apiVersion": "networking.istio.io/v1alpha3",
    "kind": "Gateway",
    "metadata": {"name": "my-gateway"},
    "spec": {
        "selector": {"app": "test"}, # Must match pod labels
        "servers":
            [
                {
                    "port" : {
                        "number": 80,
                        "name": "http",
                        "protocol": "HTTP"
                    },
                    "hosts": [] # Must match virtual service host
                },
            ]
    }
}

VIRTUAL_SERVICE_GATEWAY = {
    'apiVersion': 'networking.istio.io/v1alpha3',
    'kind': 'VirtualService',
    'metadata': {'name': 'reviews'},
    'spec': {
        'hosts': ['gateway-host'],
        'gateways': ["test-gateway"], # Must contains gateway name
        'http': [
            {
                'route': [{'destination': {'host': 'destination1', 'subset': 'v2'}}], # Host must match service name
                'timeout': '0.5s'
            },
            {
                'route': [{'destination': {'host': 'destination2'}}],
                'timeout': '2s'
            }
        ]
    }
}

DESTINATION_RULE_TIMEOUT = {
    "apiVersion": "networking.istio.io/v1alpha3",
    "kind": "DestinationRule",
    "metadata": {
        "name": "reviews-destination",
        "namespace": "foo"
    },
    "spec": {
        "trafficPolicy" : {
          "connectionPool" : {
              "tcp" : {
                  "connectionTimeout" : "5s"
              }
          }
        },
        "host": "reviews",
        "subsets": [
        {
            "name": "v1",
            "labels": {"version": "v1"}
        },
        {
            "name": "v2",
            "labels": {"version": "v2"}
         }
       ]
     }
}

DESTINATION_RULE_CIRCUIT_BREAKER = {
    "apiVersion": "networking.istio.io/v1alpha3",
    "kind": "DestinationRule",
    "metadata": {
        "name": "httpbin"
    },
    "spec": {
        "host": "httpbin",
        "trafficPolicy": {
            "connectionPool": {
                "tcp": {
                    "maxConnections": 1
                },
                "http": {
                    "http1MaxPendingRequests": 1,
                    "maxRequestsPerConnection": 1
                }
            },
            "outlierDetection": {
                "consecutive5xxErrors": 1,
                "interval": "1s",
                "baseEjectionTime": "3m",
                "maxEjectionPercent": 100
            }
        }
    }
}