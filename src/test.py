import boto3, base64

keyid='' # removed for security reason

client = boto3.client(
    'kms',
    region_name='us-east-1',
    aws_access_key_id='',
    aws_secret_access_key='')

import time
t = time.time()
result = client.encrypt(KeyId=keyid, Plaintext='Hello there')
response = client.decrypt(CiphertextBlob=result['CiphertextBlob'])
print(time.time() - t)
print(response['Plaintext'].decode('utf-8'))

