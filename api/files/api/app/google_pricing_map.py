from app import app
from flask import request, jsonify
import google_storage
import itertools

storage_classes = [
    'storage_standard',
    'storage_dra',
    'storage_nearline',
]

pretty_storage_classes = {
    'storage_standard': 'Standard storage',
    'storage_dra': 'DRA storage',
    'storage_nearline': 'Nearline storage',
}

zones = {
    'us-east1': {
        'location': 'US East (South Carolina)',
    },
    'us-central1': {
        'location': 'US Central (Iowa)',
    },
    'europe-west1': {
        'location': 'EU (Belgium)',
    },
    'asia-east1': {
        'location': 'Asia Pacific (Taiwan)',
    },
}

def storage_estimate(volume):
    estimate = google_storage.current_model(**{
        storage_class: volume for storage_class in storage_classes
    })
    return {
        storage_class: estimate['detail'][storage_class] for storage_class in storage_classes
    }

@app.route('/gcloud/map', methods=['GET'])
def gcloud_map():
    if request.args.get('gigabytes'):
        gigabytes = int(request.args.get('gigabytes'))
        volume = google_storage.apply_unit(gigabytes, 'gb')
        estimate = storage_estimate(volume)
        rounded_estimate = {
            storage_class: round(estimate[storage_class] / 1000.0, 2) for storage_class in estimate
        }
        map_estimate = {
            'prices':
                [
                    {
                        'storageClass': pretty_storage_classes[storage_class],
                        'location': zones[zone]['location'],
                        'volumeType': pretty_storage_classes[storage_class],
                        'cost': rounded_estimate[storage_class],
                        'availability': 'N/A',
                        'durability': 'N/A',
                    } for zone, storage_class in itertools.product(zones, rounded_estimate)
                ]
        }
        return jsonify(map_estimate), 200
