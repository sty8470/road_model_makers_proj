import boto3
from boto3.session import Session
import datetime
import os
import shutil
os.environ["NO_PROXY"] = 's3.amazoneaws.com'


def download_bucket(file_name, file_path, bucket_name):
    access_key = 'AKIAUNX7XU6MRV3R4KWV'
    secret_key = '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'

    folder_prefix = file_name
    credentials = file_name

    session = Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key
    )

    s3 = session.resource('s3')
    bucket = s3.Bucket(bucket_name)
    get_last_modified = lambda obj: int(obj.last_modified.strftime('%S'))
    objs = [obj for obj in bucket.objects.filter(Prefix=folder_prefix).all()]
    objs = [obj for obj in sorted(objs, key=get_last_modified)]

    for s3_file in objs:
        file_object = s3_file.key
        split_s3_file_path = file_object.split('/')
        if not '.zip' in split_s3_file_path[-1]:
            continue

        # if file_object == folder_prefix or folder_prefix in file_object:
        #     # os.makedirs(os.path.dirname(file_object), exist_ok= True)
        #     continue
        
        if len(split_s3_file_path) > 2:
            if split_s3_file_path[-1] == '':
                continue

            file_name = str(os.path.join(split_s3_file_path[1], split_s3_file_path[-1]))
            # file_name = str(split_s3_file_path[-1])
            folder_name = str(split_s3_file_path[1])
            folder_name = os.path.join(file_path, folder_name)
            if not os.path.isdir(folder_name):
                os.makedirs(folder_name, exist_ok= True)
            else:
                # 폴더안에 파일 있으면 전체 삭제
                modified_time = datetime.datetime.strptime(split_s3_file_path[-1].split('_')[-1].split('.')[0], '%Y%m%d%H%S%f')
                for fileName in os.listdir(folder_name):
                    if '.' in fileName:
                        if '.zip' in fileName:
                            time = datetime.datetime.strptime(fileName.split('_')[-1].split('.')[0], '%Y%m%d%H%S%f')
                            if modified_time >= time:
                                os.remove(os.path.join(folder_name, fileName))
                            else:
                                continue
                        else:
                            os.remove(os.path.join(folder_name, fileName))
                    else:
                        shutil.rmtree(os.path.join(folder_name, fileName))
        else:
            file_name = str(split_s3_file_path[-1])

        if file_name == None or file_name == '':
            continue

        download_path = os.path.join(file_path, file_name)
        # if len(os.listdir(os.path.join(file_path, folder_name))) > 1:
        #     continue

        print('Downloading file {} ...'.format(file_object))
        bucket.download_file(file_object, download_path)
        last_modified = None


def download_one_map_file(file_name, file_path, bucket_name):
    access_key = 'AKIAUNX7XU6MRV3R4KWV'
    secret_key = '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'

    folder_prefix = file_name
    credentials = file_name

    session = Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key
    )

    s3 = session.resource('s3')
    bucket = s3.Bucket(bucket_name)
    get_last_modified = lambda obj: int(obj.last_modified.strftime('%S'))

    objs = [obj for obj in bucket.objects.filter(Prefix=folder_prefix).all()]
    objs = [obj for obj in sorted(objs, key=get_last_modified)]


def upload_file(file_name, bucket_name, object_name=None, pulic_access = False):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """
    access_key = 'AKIAUNX7XU6MRV3R4KWV'
    secret_key = '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'

    session = Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key
    )

    s3 = session.resource('s3')
    bucket = s3.Bucket(bucket_name)

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    try:
        if pulic_access:
            response = bucket.upload_file(file_name, object_name, ExtraArgs = {'ACL': 'public-read'})
        else:
            response = bucket.upload_file(file_name, object_name)
        print('[INFO] Uploaded {} to S3 at {}'.format(bucket_name, file_name))
    except Exception as e:
        print(e)
        return False
    return True


if __name__ == u'__main__':
    # file_path = str.format('C:\MGeoEditor\Editor\{0}\{1}', 'test',  str(datetime.datetime.now()))
    # file_path = 'D:\s3_test\'
    
    file_path = 'd:\\road_model_maker\\src\\test_file_upload\\../../data/temp'
    # file_path = 'C:\\Users\\HI\\Desktop'
    bucket = 'morai-internal'
    # bucket = 'develop-morai-s3-bucket'
    
    key = 'morai_sim_map_repository/R_KR_PR_Naverlabs_Pangyo/'
    # file_name = 'map_editor_210727_PM020922_win.zip'
    file_name = 'C:\\Users\\HI\\Desktop\\test\\upload\\test.txt'
    download_bucket(key, file_path, bucket)
    # upload_file(file_name, bucket, 'map_editor_internal_use/test.txt')


    