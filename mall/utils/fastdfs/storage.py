from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from fdfs_client.client import Fdfs_client
from mall import settings


@deconstructible
class FastDFSStorage(Storage):
    """
    自定义文件上传类
    """


def __init__(self, conf_path=None,ip=None):
    if conf_path is None:
        conf_path = settings.FDFS_CLIENT_CONF
    self.conf_path = conf_path

    if ip is None:
        ip = settings.FDFS_URL
    self.ip = ip


def _open(self, name, mode='rb'):
    pass


def _save(self, name, content, max_length=None):

    # 创建client对象
    client = Fdfs_client(self.conf_path)
    # 获取文件
    file_data = content.read()
    # 上传
    result = client.upload_by_buffer(file_data)
    # 判断上传结果
    if result.get('Status') == 'Upload successed.':
        # 返回上传的字符串
        return result.get('Remote file_id')
    else:
        raise Exception('上传失败')


def exists(self, name):
    # 判断文件是否存在，FastDFS可以自行解决文件的重名问题
    # 所以此处返回False，告诉Django上传的都是新文件
    return False


def url(self, name):
    # 返回文件的完整URL路径
    return self.ip + name
