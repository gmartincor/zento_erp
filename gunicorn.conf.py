# =============================================================================
# gunicorn.conf.py - Configuración de Gunicorn para Render
# =============================================================================

import os
import multiprocessing

# Configuración del servidor
bind = f"0.0.0.0:{os.environ.get('PORT', 8000)}"
workers = min(4, multiprocessing.cpu_count() * 2 + 1)
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
preload_app = True
timeout = 120
keepalive = 5

# Configuración de logging
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("LOG_LEVEL", "info").lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Configuración de proceso
user = None
group = None
tmp_upload_dir = "/tmp"
secure_scheme_headers = {
    'X-FORWARDED-PROTO': 'https',
}

# Configuración de memoria
max_requests_jitter = 100
worker_tmp_dir = "/dev/shm"

# Hooks para mejor rendimiento
def on_starting(server):
    server.log.info("Iniciando Gunicorn para zentoerp.com")

def on_reload(server):
    server.log.info("Recargando Gunicorn")

def worker_int(worker):
    worker.log.info("Worker recibió INT o QUIT signal")

def pre_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_worker_init(worker):
    worker.log.info("Worker initialized (pid: %s)", worker.pid)

def worker_abort(worker):
    worker.log.info("Worker aborted (pid: %s)", worker.pid)
