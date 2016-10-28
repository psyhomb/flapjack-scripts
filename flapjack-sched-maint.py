#!/usr/bin/env python
# Author: Milos Buncic
# Date: 2016/10/24
# Description: Create or delete Flapjack scheduled maintenance periods

import sys
import os
import datetime
import argparse
import json
import requests


def get_checks_data(url):
  """ Return all checks data for enabled checks (output: list) """
  try:
    checks_data = requests.get('%s/checks' % url).json()['checks']
  except requests.exceptions.ConnectionError as e:
    print 'Connection Error: %s' % e
    sys.exit(1)

  return [  check_data  for check_data in checks_data  if check_data['enabled']  ]


def get_checks_ids(checks_data, checks=[], entities=[]):
  """ Return list of checks ids (output: list) """
  checks_ids = []
  for check_data in checks_data:
    if checks and entities:
      for entity in entities:
        for check in checks:
          alt_check = '%s_%s' % (check, entity.replace('.', '-'))
          if (check.lower() == check_data['name'].lower() or alt_check.lower() == check_data['name'].lower()) and entity.lower() == check_data['entity_name'].lower():
            checks_ids.append(check_data['id'])
    elif checks and not entities:
      for check in checks:
        alt_check = '%s_%s' % (check, check_data['entity_name'].replace('.', '-'))
        if check.lower() == check_data['name'].lower() or alt_check.lower() == check_data['name'].lower():
          checks_ids.append(check_data['id'])
    elif entities and not checks:
        for entity in entities:
          if entity.lower() == check_data['entity_name'].lower():
            checks_ids.append(check_data['id'])

  return sorted(checks_ids)


def get_grouped_checks_ids(checks_ids, max_length):
  """ Return list of grouped checks ids (output: list) """
  length = len(checks_ids)
  grouped_checks_ids = []
  l = []

  for check_id in checks_ids:
    length -= 1
    l.append(check_id)
    s = ','.join(l)

    if len(s) >= max_length or length == 0:
      grouped_checks_ids.append(s)
      l = []

  return grouped_checks_ids


def create_sched_maint(url, check_id, start_time, duration, summary):
  """ Create schedule maintenance (output: tuple) """
  http_codes = {
    '204': 'The submitted scheduled maintenance periods were created successfully',
    '400': 'Bad request, try with smaller path length',
    '403': 'Error The required \'start_time\' parameter was not sent',
    '404': 'Error No matching checks were found',
    '405': 'Error The submitted parameters were not sent with the JSONAPI MIME type application/json',
    '500': 'Internal Server Error'
  }

  data = {
    "scheduled_maintenances": [
      {
        "start_time": start_time,
        "duration": duration,
        "summary": summary
      }
    ]
  }

  response = requests.post('%s/scheduled_maintenances/checks/%s' % (url, check_id), json=data)
  status_code = str(response.status_code)

  return status_code, http_codes[status_code]


def delete_sched_maint(url, check_id, start_time):
  """ Delete schedule maintenance (output: tuple) """
  http_codes = {
    '204': 'Matching scheduled maintenance periods were deleted',
    '400': 'Bad request, try with smaller path length',
    '403': 'Error The required \'start_time\' parameter was not sent',
    '404': 'Error No matching checks were found',
    '500': 'Internal Server Error'
  }

  response = requests.delete('%s/scheduled_maintenances/checks/%s?start_time=%s' % (url, check_id, start_time))
  status_code = str(response.status_code)

  return status_code, http_codes[status_code]


def write_to_file(filename, data):
  """ Write data to file """
  try:
    with open(filename, 'w') as f:
      f.write(json.dumps(data, indent=4, ensure_ascii=False, sort_keys=True).encode('utf-8'))
  except IOError as e:
    print 'Error while writing to file: %s' % e
    sys.exit(1)


def read_from_file(filename):
  """ Read data from file (output: dict) """
  try:
    with open(filename, 'r') as f:
      return json.load(f)
  except IOError as e:
    print 'Error while reading from file: %s' % e
    sys.exit(1)


def stale_cache(filename, retention_time):
  """ Check cache status (output: boolean) """
  now = int(datetime.datetime.strftime(datetime.datetime.now(), '%s'))
  mtime = int(os.path.getmtime(filename))

  if (now - mtime) > retention_time:
    return True
  else:
    return False


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('-H', '--hostname', help='Flapjack API hostname', default='localhost', dest='host', action='store')
  parser.add_argument('-p', '--port', help='Flapjack API port', type=int, default=3081, dest='port', action='store')
  parser.add_argument('-c', '--checks', help='List of case insensitive check names (e.g. c1,c2,cX)', default='', dest='checks', action='store')
  parser.add_argument('-e', '--entities', help='List of case insensitive entity names (e.g. e1,e2,eX)', default='', dest='entities', action='store')
  parser.add_argument('-t', '--start-time', help='A date & time in ISO 8601 format YYYY-MM-DDThh:mm:ss (e.g. 2016-10-22T17:55:00)', default='', dest='start_time', action='store')
  parser.add_argument('-d', '--duration', help='A length of time (in seconds) that the created scheduled maintenance periods should last, will be ignored if -D is used', type=int, default=3600, dest='duration', action='store')
  parser.add_argument('-S', '--summary', help='A summary of the reason for the maintenance period, will be ignored if -D is used', default='Test', dest='summary', action='store')
  parser.add_argument('-l', '--length', help='URL max path length (RFC 2616, section 3.2.1)', type=int, default=1000, dest='length', action='store')
  parser.add_argument('-D', '--delete', help='Delete schedule maintenance (requires creation start time specified with -t)', dest='delete', action='store_true')
  parser.add_argument('--no-cache', help='Don\'t use cached information', dest='no_cache', action='store_true')
  parser.add_argument('--cache-retention-time', help='Cache will expire after specified time (in seconds) period', type=int, default=604800, dest='cache_retention_time', action='store')
  parser.add_argument('--cache-file', help='Cache file path', default='/tmp/%s-cache.json' % os.path.splitext(os.path.basename(__file__))[0], dest='cache_file', action='store')

  args = parser.parse_args()

  flapjack_api = 'http://%s:%d' % (args.host, args.port)
  checks = args.checks.split(',') if args.checks else []
  entities = args.entities.split(',') if args.entities else []
  start_time = args.start_time
  duration = args.duration
  summary = args.summary
  length = args.length
  delete = args.delete
  no_cache = args.no_cache
  cache_retention_time = args.cache_retention_time
  cache_file = args.cache_file

  if (not checks and not entities) or (delete and not start_time):
    parser.print_help()
    sys.exit(2)

  if not delete and not start_time:
    start_time = datetime.date.strftime(datetime.datetime.now(), '%Y-%m-%dT%H:%M:%S')

  if no_cache or not os.path.isfile(cache_file) or stale_cache(cache_file, cache_retention_time):
    checks_data = get_checks_data(flapjack_api)
    if checks_data:
      write_to_file(cache_file, checks_data)
  else:
    checks_data = read_from_file(cache_file)

  checks_ids = get_checks_ids(checks_data, checks, entities)
  if checks_ids:
    if not delete:
      for check_id in get_grouped_checks_ids(checks_ids, length):
        response = create_sched_maint(flapjack_api, check_id, start_time, duration, summary)
        print 'HTTP status code: %s, %s' % response
    else:
      for check_id in get_grouped_checks_ids(checks_ids, length):
        response = delete_sched_maint(flapjack_api, check_id, start_time)
        print 'HTTP status code: %s, %s' % response
  else:
    print 'Can\'t find any results for given \'check\' and \'entity\' values'


if __name__ == '__main__':
  main()
