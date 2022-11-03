from project.kmodel.istio import VirtualService
from tests.data.istio_objects_dict import VIRTUAL_SERVICE
#print(read_data_from_file("data/virtual_service.yaml"))

vservice = VirtualService.from_dict(VIRTUAL_SERVICE)
print(vservice.get_timeouts())

d = {
    'a':1, 'b':2,
    'nested':{
        'c':3,
        'd':4
    }
}

print(d.keys())