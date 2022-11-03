VIRTUAL_SERVICE = {
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
