import boto3 

session = boto3.session.Session(profile_name='tdouglas')
s3 = session.client('s3')

bucket = 'dev-use2-tedsand-raw-data-s3'
prefix = 'openpowerlifting'

response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)

keys = [x['Key'] for x in response['Contents']]

for key in keys:
    year_val, month_val, day_val = key.split('-')[1:4]
    new_key = f"openpowerlifting/year={year_val}/month={month_val}/day={day_val}/{key.split('/')[1]}"
    copy_response = s3.copy_object(
        Bucket=bucket,
        Key=new_key,
        CopySource=f"/{bucket}/{key}"
    )
    print(key, "->", new_key)