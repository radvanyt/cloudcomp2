import boto3, base64

keyid='arn:aws:kms:us-east-1:465869454039:key/f2d0202f-1cf9-4a1b-9b19-ed1d0d7d8996'
c_akey = 'AKIAJ3SPDQTN4PDUSY5A'
c_sakey = 'oMT/BBNC2EWcuOb4/FEUW+Lnw4Et6yKkddAypX48'
c_keyid = 'arn:aws:kms:us-east-1:465869454039:key/c0eb351c-0b88-4a04-883e-ae206d1dcdf3'

client = boto3.client(
    'kms',
    region_name='us-east-1',
    aws_access_key_id='AKIAJNJKBXAHZ5HLGDHA',
    aws_secret_access_key='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')

import time
t = time.time()
result = client.encrypt(KeyId=keyid, Plaintext='Hello there')
response = client.decrypt(CiphertextBlob=result['CiphertextBlob'])
print(time.time() - t)
print(response['Plaintext'].decode('utf-8'))

