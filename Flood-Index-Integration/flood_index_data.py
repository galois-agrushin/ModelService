import boto3
import os
import redis
import configparser
from hashlib import sha256
import json
from collections import OrderedDict

config = configparser.ConfigParser()
config.read('../REST-Server/config.ini')

r = redis.Redis(host=config['REDIS']['HOST'],
                port=config['REDIS']['PORT'],
                db=config['REDIS']['DB'])

profile = "wmuser"
bucket = "world-modelers"

session = boto3.Session(profile_name=profile)
s3 = session.resource("s3")
s3_client = session.client("s3")
s3_bucket= s3.Bucket(bucket)

def gen_run(input_file, output):
    model_name = 'flood_index_model'
    model_config = {
                    'config': {
                    },
                    'name': model_name
                   }

    model_config = sortOD(OrderedDict(model_config))

    run_id = sha256(json.dumps(model_config).encode('utf-8')).hexdigest()
    print(model_config)
    # Add to model set in Redis
    r.sadd(model_name, run_id)
    
    run_obj = {'status': 'SUCCESS',
     'name': model_name,
     'config': model_config,
     'bucket': bucket,
     'key': f"results/flood_index_model/{output}"
    }

    run_obj['config']['run_id'] = run_id
    run_obj['config'] = json.dumps(run_obj['config'])
    
    # Upload file to S3
    print(f"Uploading {run_obj['key']}...")
    s3_bucket.upload_file(input_file, run_obj['key'], ExtraArgs={'ACL':'public-read'})

    # Create Redis object
    r.hmset(run_id, run_obj)


def sortOD(od):
    res = OrderedDict()
    for k, v in sorted(od.items()):
        if isinstance(v, dict):
            res[k] = sortOD(v)
        else:
            res[k] = v
    return res    

if __name__ == "__main__":

    # Wipe runs for the model
    r.delete('flood_index_model')

    input_file = f"floodIndex-78318c49e3646c852483accdeb818081"
    output = "floodIndex-78318c49e3646c852483accdeb818081.nc"
    gen_run(input_file, output)