"""pytest 全局配置：在任何 app 模块导入之前隔离数据库与上传目录。

注意：必须使用 setdefault，且在导入 app 之前执行——app.config.database 里的
load_dotenv() 不会覆盖已存在的环境变量，因此这里的隔离配置始终生效。
"""
import os
import tempfile

_tmpdir = tempfile.mkdtemp(prefix='cc-pytest-')
os.environ.setdefault('DB_PATH', f'{_tmpdir}/test.db'.replace('\\', '/'))
os.environ.setdefault('UPLOAD_DIR', _tmpdir)
