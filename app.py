
from flask import Flask, render_template, jsonify, request
import docker
import threading
import time

app = Flask(__name__)
client = docker.from_env()

# 全局容器状态缓存
container_cache = {}
cache_lock = threading.Lock()

def update_container_cache():
    global container_cache
    while True:
        containers = client.containers.list(all=True)
        with cache_lock:
            container_cache = {
                c.id: {
                    'name': c.name,
                    'status': c.status,
                    'ports': c.ports,
                    'image': c.image.tags[0] if c.image.tags else '',
                    'id': c.short_id
                } for c in containers
            }
        time.sleep(5)

# 启动后台线程更新容器状态
thread = threading.Thread(target=update_container_cache)
thread.daemon = True
thread.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/containers')
def get_containers():
    with cache_lock:
        return jsonify(list(container_cache.values()))

@app.route('/api/container/<container_id>/<action>', methods=['POST'])
def control_container(container_id, action):
    try:
        container = client.containers.get(container_id)
        if action == 'start':
            container.start()
        elif action == 'stop':
            container.stop()
        elif action == 'restart':
            container.restart()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
