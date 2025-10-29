#!/usr/bin/python3
# -*- coding: utf-8 -*-

# source: https://support.loopia.se/wp-content/uploads/2019/04/dyndns_loopia.txt
#     https://support.loopia.se/wiki/uppdatera-dynamisk-ip-adress-med-loopiaapi/

"""
If you don't have an API user yet you can create one in the Customer Zone.
For reasons of security you shouldn't add more permissions than necessary.

The user requires the following permissions for this script to function:
* getZoneRecords  - To find out which record to update
* updateZoneRecord  - To actually update the zone record

The following permissions are optional but recommended:
* removeZoneRecord  - If the zone has several A-records, this is necessary to remove all excess records.
* addZoneRecord   - Necessary if the zone doesn't have any A-record at all.
"""

import json
import logging
import time
import urllib.request
import xmlrpc.client


def api_error():
  """Print a warning message because an error has occured"""

  logging.error('Error! Not sure why, sorry! Please check your internet connection and http://www.driftbloggen.se. Contact support@loopia.se if the problem persists.')
  quit(1)

def del_excess(Config, zone_records):
  """Remove all A records except the first one"""

  num = 0
  for record in zone_records:
    client.removeZoneRecord(
        Config["username"],
        Config["password"],
        Config["domain"],
        Config["subdomain"],
        record['record_id'])
    num = num + 1

  logging.info('Deleted {} unnecessary record(s)'.format(str(num)))

def get_ip():
  """Get public IP adress"""
  ip = urllib.request.urlopen('https://api.ipify.org').read().decode('utf-8')
  return ip

def get_records(Config):
  """Get current zone records"""
  try:
    zone_records = client.getZoneRecords(
      Config["username"],
      Config["password"],
      Config["domain"],
      Config["subdomain"])
    # Remove irrelevant records and return
    return [d for d in zone_records if d['type'] == 'A']
  except:
    # Quit if unable to authorize
    if 'AUTH_ERROR' in zone_records:
      logging.error('Your user information seems to be incorrect. Please edit this file and check your username and password.')
      quit(2)

    # Quit if API returns unknown error
    if 'UNKNOWN_ERROR' in zone_records:
      logging.error('API returned "UNKNOWN ERROR". This could mean that the requested (sub)domain does not exist in this account.')
      quit(3)

    # Can't connect to the API for other reasons
    api_error()


def add_record(Config, ip):
  """Add a new A record if we don't have any"""

  new_record = {
    'priority': '',
    'rdata': ip,
    'type': 'A',
    'ttl': Config["ttl"]
  }

  status = client.addZoneRecord(
      Config["username"],
      Config["password"],
      Config["domain"],
      Config["subdomain"],
      new_record)

  if Config["subdomain"] == '@':
    logging.info('{domain}: {status}. Added new record.'.format(
      domain=Config["domain"],
      status=status))
  else:
    logging.info('{subdomain}.{domain}: {status}. Added new record.'.format(
      subdomain=Config["subdomain"],
      domain=Config["domain"],
      status=status))

def update_record(Config, new_ip, record):
  """Update current A record"""

  # Does the record need updating?
  if record['rdata'] != new_ip:
    logging.info('IP address has changed from {old} to {new}'.format(
      old=record['rdata'],
      new=new_ip))
    # Yes it does. Update it!
    new_record = {
      'priority': record['priority'],
      'record_id': record['record_id'],
      'rdata': new_ip,
      'type': record['type'],
      'ttl': record['ttl']
    }

    try:
      status = client.updateZoneRecord(
          Config["username"],
          Config["password"],
          Config["domain"],
          Config["subdomain"],
          new_record)

      if Config["subdomain"] == '@':
        logging.info('{domain}: {status}'.format(
          domain=Config["domain"],
          status=status))
      else:
        logging.info('{subdomain}.{domain}: {status}'.format(
          subdomain=Config["subdomain"],
          domain=Config["domain"],
          status=status))

    except:
      api_error()

############
### Main ###
############

def main(Config):
  # Get current A records and public IP address
  a_records = get_records(Config)
  new_ip = get_ip()

  # Do we currently have an A record? If not, create one!
  if len(a_records) == 0:
    add_record(Config, new_ip)

  else:
    # Remove all excess A records
    if len(a_records) > 1:
      del_excess(Config, a_records[1:])

    # Now let's update the record!
    update_record(Config, new_ip, a_records[0])

if __name__ == '__main__':
  logging.basicConfig(filename='loopiadns.log', level=logging.INFO, format='%(asctime)s: %(levelname)s [%(name)s] %(message)s')

  with open('loopiadns.json', 'r') as f:
    config = json.load(f)

  # Build XML RPC client
  client = xmlrpc.client.ServerProxy(
    uri = 'https://api.loopia.se/RPCSERV',
    encoding = 'utf-8')

  logging.info('START')

  while True:
    for c in config:
      main(c)
    time.sleep(60*5)
