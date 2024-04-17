import schedule
import time
from requests import get
import subprocess
import logging
import json

logger = logging.getLogger(__name__)
ip = '127.0.0.1'
hostname = ''
user = ''

def update_public_ip():
  global ip

  current_ip = get('https://api.ipify.org').content.decode('utf8')

  if ip != current_ip:
    ip = current_ip
    cmd = ['/usr/bin/curl', '-s', '--user', user, f'https://dyndns.loopia.se?hostname={hostname}&myip={ip}']
    process = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE)
    process.wait()
    stdout = process.stdout.read().decode('utf8')
    logger.info(f'updating public ip to {ip}, response {stdout}')

if __name__ == '__main__':
  logging.basicConfig(filename='loopiadns.log', level=logging.INFO, format='%(asctime)s: %(levelname)s [%(name)s] %(message)s')

  with open('loopiadns.config', 'r') as f:
    config = json.load(f)
  hostname = config['hostname']
  user = config['user']

  schedule.every(5).minutes.do(update_public_ip)

  logger.info('START')

  update_public_ip()

  while True:
    schedule.run_pending()
    time.sleep(1)
