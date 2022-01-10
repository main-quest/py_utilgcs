import os
import stat
import tempfile
import yaml
from google.cloud import storage


_BUCKET_URL_PREFIX = 'gs://'


def get_bucket_name_from_url(url: str):
    if _BUCKET_URL_PREFIX not in url:
        return None

    url = url.replace(_BUCKET_URL_PREFIX, '')
    if '/' in url:
        url = url[:url.index('/')]
    return url


def get_blob_name_in_bucket_from_url(url: str):
    bucket_name = get_bucket_name_from_url(url)
    if bucket_name is None:
        return None

    bucket_url = get_bucket_url(bucket_name)
    url = url.replace(bucket_url, '')
    if url.startswith('/'):
        url = url[1:]

    return url


def get_bucket_url(bucket_name):
    return _BUCKET_URL_PREFIX + bucket_name


def replace_line_in_file(file_path, containing_substr, replacement_line, optional=False):
    with open(file_path, 'r') as f:
        lines = f.readlines()

    indices = [i for i, line in enumerate(lines) if line.startswith(containing_substr)]
    if len(indices) == 0:
        if optional:
            return None
        return f'Failed to find "{containing_substr}" to replace'

    idx = indices[0]
    lines[idx] = replacement_line
    with open(file_path, 'w') as f:
        f.writelines(lines)

    return None


def is_socket(socket_path):
    try:
        return stat.S_ISSOCK(os.stat(socket_path).st_mode)
    except Exception:
        return False


# TODO switch back to gsutil, as it's more convenient!
# TODO switch back to gsutil, as it's more convenient!
# TODO switch back to gsutil, as it's more convenient!
# TODO switch back to gsutil, as it's more convenient!

# TODO currently only works with files!


class GStorageUtil:
    def __init__(self, key_path: str):

        with open(key_path, 'r') as f:
            data = f.read()
        file_path = tempfile.NamedTemporaryFile(delete=False).name
        with open(file_path, 'w') as f:
            f.write(data)
        # self.client = storage.Client.from_service_account_json(file_path, project=get_env_project_id())
        self.client = storage.Client.from_service_account_json(file_path)

    # TODO add folder support (need to list blobs with a prefix and then download them all):
    #   https://stackoverflow.com/a/63992365

    def cp_wait_throw(self, src, dest):
        print(f'Copying "{src}" >> "{dest}"')

        if src == '.' or src == './':
            src = os.getcwd() + '/'
        if dest == '.' or dest == './':
            dest = os.getcwd() + '/'

        if src.endswith('/'):
            raise NotImplementedError('src folder')

        src_bucket_name = get_bucket_name_from_url(src)
        dest_bucket_name = get_bucket_name_from_url(dest)
        src_file_or_folder_name = os.path.basename(src)
        is_from_bucket = src_bucket_name is not None
        is_to_bucket = dest_bucket_name is not None
        # is_from_local = not is_from_bucket
        is_to_local = not is_to_bucket

        dest_bucket = src_bucket = None
        src_blob_name = dest_blob_name = None
        if is_from_bucket:
            src_bucket = self.client.bucket(src_bucket_name)
            src_blob_name = get_blob_name_in_bucket_from_url(src)
        if is_to_bucket:
            dest_bucket = self.client.bucket(dest_bucket_name)
            dest_blob_name = get_blob_name_in_bucket_from_url(dest)

        def exists_in_dest_bucket(blob_name):
            return dest_bucket.blob(blob_name).exists()

        # If the dest is a folder and it exists, we copy the src (whether file or dir) INSIDE the dest
        if is_from_bucket:
            if is_to_local:
                if os.path.isdir(dest):
                    if not dest.endswith('/'):
                        raise Exception(f'dest "{dest}" is a folder, but wasn\'t suffixed with "/"')

                    dest = os.path.join(os.getcwd(), src_file_or_folder_name)
            else:
                if dest.endswith('/'):
                    if exists_in_dest_bucket(dest_blob_name) or not src.endswith('/'):
                        # Same comment as in the case from_bucket_to_local (see above)
                        dest_blob_name += src_file_or_folder_name
        else:
            if is_to_local:
                raise Exception('from_local to_local not allowed')

            if os.path.isdir(src):
                if not src.endswith('/'):
                    raise Exception(f'src "{src}" is a folder, but wasn\'t suffixed with "/"')
                if not dest.endswith('/'):
                    raise Exception(
                        f'Cannot copy local dir to a file (directories should be suffixed with "/"):'
                        ' src={src}, dest={dest}'
                    )

                if exists_in_dest_bucket(dest_blob_name):
                    # Same comment as in the case from_bucket_to_local (see above)
                    dest_blob_name += src_file_or_folder_name
            else:
                if not os.path.isfile(src):
                    raise Exception(f'src file "{src}" doesn\'t exist')

                if dest.endswith('/'):
                    if exists_in_dest_bucket(dest_blob_name):
                        # Same comment as in the case from_bucket_to_local (see above)
                        dest_blob_name += src_file_or_folder_name

        src_blob = dest_blob = None
        if is_from_bucket:
            src_blob = src_bucket.blob(src_blob_name)
            src_blob.cache_control = 'max-age=0'
        if is_to_bucket:
            dest_blob = dest_bucket.blob(dest_blob_name)
            dest_blob.cache_control = 'max-age=0'

        if is_from_bucket:
            if is_to_bucket:
                src_bucket.copy_blob(src_blob, dest_bucket, dest_blob_name)
            else:
                src_blob.download_to_filename(dest)
        else:
            dest_blob.upload_from_filename(src)

    def cp_wait(self, src, dest):
        try:
            self.cp_wait_throw(src, dest)
            return True
        except Exception as e:
            print(e)
            return False

    # Returns (result, error) tuple
    def read_yaml_file_wait(self, url: str):
        with tempfile.TemporaryDirectory() as dir_path:
            file_name = os.path.basename(url)
            file = f'{dir_path}/{file_name}'
            if not self.cp_wait(url, file):
                return None, f'Failed to CD or to download the file at "{url}"'

            try:
                with open(file, 'r') as stream:
                    obj = yaml.safe_load(stream)
            except Exception as e:
                return None, f'Failed to read the target file at "{url}": {e}'

            return obj, None
