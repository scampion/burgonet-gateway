#!/usr/bin/env python3
"""
Generic syslog server for receiving logs from nginx

The goal of this script is to receive logs from nginx and dispatch them to a Redis server.
The logs are expected to be in the syslog format and sent via UDP to the server.

"""
import json
import logging
import os
import re
import socket
import socketserver
import sys
import traceback
from datetime import datetime
from typing import NamedTuple, Optional

import redis

from frontend.app.config import REDIS_HOST, REDIS_PORT, SYSLOG_HOST, SYSLOG_PORT, RESPONSES_LOGFILE
from frontend.app.models import DeepSeek, OpenAI, Anthropic, Azure, Ollama
from functools import lru_cache

rd = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
out = open(RESPONSES_LOGFILE, 'a')
CONFIG = None

parsers = {
    'deepseek': DeepSeek.parse_response,
    'openai': OpenAI.parse_response,
    'anthropic': Anthropic.parse_response,
    'azure': Azure.parse_response,
    'ollama': Ollama.parse_response,
}

# set logging level at INFO
logging.basicConfig(
    level=os.environ.get('LOGLEVEL', 'INFO').upper()
)

class SyslogMessage(NamedTuple):
    facility: int
    severity: int
    timestamp: datetime
    hostname: str
    program: str
    pid: Optional[int]
    message: str


class SyslogParser:
    # Mapping for facility codes
    FACILITIES = {
        0: "kern",  # kernel messages
        1: "user",  # user-level messages
        2: "mail",  # mail system
        3: "daemon",  # system daemons
        4: "auth",  # security/authorization messages
        5: "syslog",  # messages generated internally by syslogd
        6: "lpr",  # line printer subsystem
        7: "news",  # network news subsystem
        8: "uucp",  # UUCP subsystem
        9: "cron",  # clock daemon
        10: "authpriv",  # security/authorization messages
        11: "ftp",  # FTP daemon
        12: "ntp",  # NTP subsystem
        13: "security",  # log audit
        14: "console",  # log alert
        15: "cron2",  # clock daemon
        16: "local0",
        17: "local1",
        18: "local2",
        19: "local3",
        20: "local4",
        21: "local5",
        22: "local6",
        23: "local7"
    }

    # Mapping for severity codes
    SEVERITIES = {
        0: "emerg",
        1: "alert",
        2: "crit",
        3: "err",
        4: "warning",
        5: "notice",
        6: "info",
        7: "debug"
    }

    @staticmethod
    def parse(message: str) -> Optional[SyslogMessage]:
        """Parse a syslog message according to RFC 3164."""
        try:
            # Basic pattern for RFC 3164 syslog messages
            pattern = r'<(\d+)>(\w+\s+\d+\s+\d+:\d+:\d+)\s+(\S+)\s+([^:\[\s]+)(?:\[(\d+)\])?:\s*(.*)'
            match = re.match(pattern, message)

            if not match:
                return None

            pri, timestamp_str, hostname, program, pid, content = match.groups()

            # Parse priority field
            pri = int(pri)
            facility = pri >> 3
            severity = pri & 0x07

            # Parse timestamp
            try:
                current_year = datetime.now().year
                timestamp = datetime.strptime(f"{current_year} {timestamp_str}", "%Y %b %d %H:%M:%S")
            except ValueError:
                timestamp = datetime.now()

            # Convert pid to int if present
            pid = int(pid) if pid else None

            return SyslogMessage(
                facility=facility,
                severity=severity,
                timestamp=timestamp,
                hostname=hostname,
                program=program,
                pid=pid,
                message=content
            )
        except Exception as e:
            print(f"Error parsing message: {e}")
            return None


@lru_cache(maxsize=128)
def get_quotas_config(uri):
    for model in CONFIG['models']:
        if model['location'] == uri:
            return model.get('quotas', {})


def quota(data):
    quotas = get_quotas_config(data['uri'])
    logging.debug(f"quotas: {quotas}")
    # Manage quotas for tokens
    for period, value in quotas.get('max_tokens', {}).items():
        user = rd.get(f"token:{data['token']}")
        logging.debug(f"checking quota for {user} {period} {value}")
        if period == "hour":
            current_hour = datetime.now().strftime("%Y-%m-%d-%H")
            # add total tokens used in the hour to redis quota:<user>:<hour>
            total_tokens = data['tokens_input'] + data['tokens_output']
            rd.incr(f"quota:{user}:{current_hour}", total_tokens)
            rd.expire(f"quota:{user}:{current_hour}", 3600)

            # check if the total tokens used in the hour is greater than the max tokens allowed
            if int(rd.get(f"quota:{user}:{current_hour}") or 0) > value:
                # set the quota exceeded flag to quota:<user>:exceeded and expire it after 1 hour
                timeout = 3600 - (datetime.now().minute * 60 + datetime.now().second)
                rd.setex(f"quota:{user}:exceeded", timeout, f'hour {current_hour}')
                logging.info(f"📊 quota exceeded for {user} {period} {value}")

        if period == "day":
            current_day = datetime.now().strftime("%Y-%m-%d")
            # add total tokens used in the day to redis quota:<user>:<day>
            total_tokens = data['tokens_input'] + data['tokens_output']
            rd.incr(f"quota:{user}:{current_day}", total_tokens)
            rd.expire(f"quota:{user}:{current_day}", 86400)

            # check if the total tokens used in the day is greater than the max tokens allowed
            if int(rd.get(f"quota:{user}:{current_day}") or 0) > value:
                # set the quota exceeded flag to quota:<user>:exceeded and expire it after 1 day
                timeout = 86400 - (datetime.now().hour * 3600 + datetime.now().minute * 60 + datetime.now().second)
                rd.setex(f"quota:{user}:exceeded", timeout, f"day {current_day}")
                logging.info(f"📊 quota exceeded for {user} {period} {value}")

        if period == "week":
            current_week = datetime.now().strftime("%Y-%W")
            # add total tokens used in the week to redis quota:<user>:<week>
            total_tokens = data['tokens_input'] + data['tokens_output']
            rd.incr(f"quota:{user}:{current_week}", total_tokens)
            rd.expire(f"quota:{user}:{current_week}", 604800)
            # check if the total tokens used in the week is greater than the max tokens allowed
            if int(rd.get(f"quota:{user}:{current_week}") or 0) > value:
                # set the quota exceeded flag to quota:<user>:exceeded and expire it after 1 week
                timeout = 604800 - (datetime.now().weekday() * 86400 + datetime.now().hour * 3600 +
                                    datetime.now().minute * 60 + datetime.now().second)
                rd.setex(f"quota:{user}:exceeded", timeout, f'week {current_week}')
                logging.info(f"📊 quota exceeded for {user} {period} {value}")


def dispatch(line):
    rd.publish('responses', line)  # duplicate the stream for future purposes
    data = json.loads(line)
    if data['status'] == '200':
        # Clean up the data and prepare it
        token = data['authorization'][7:]
        data['token'] = token
        keys_to_keep = ['time', 'uri', 'request_body', 'response_body', 'provider', 'model_name', 'model_version']
        data = {k: v for k, v in data.items() if k in keys_to_keep}
        request_body = json.loads(data['request_body'])
        response_body = json.loads(data['response_body'])
        data['request_body'] = request_body
        data['response_body'] = response_body

        # Apply provider parser
        provider_name = data['provider']
        parsed_response = parsers[provider_name](data)
        parsed_response['provider'] = provider_name
        parsed_response['time'] = data['time']
        parsed_response['uri'] = data['uri']
        parsed_response['token'] = token

        # Check for quota
        quota(parsed_response)
        out.write(json.dumps(parsed_response) + '\n')
        logging.info(f"🚀 response parsed: {parsed_response}")
    else:
        raise Exception(f"Error HTTP Status: {data['status']} {data}")


class SyslogUDPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = bytes.decode(self.request[0].strip())
        parsed = SyslogParser.parse(data)
        if parsed:
            try:
                dispatch(parsed.message)
                logging.debug(f"syslog message parsed: {self.client_address[0]}: {parsed.message}")
            except Exception as e:
                traceback.print_exc()
                logging.error(f"🚨️ Error:{e.__class__.__name__}  {str(e)} {data}")
        else:
            logging.error(f"syslog message unparsed : {self.client_address[0]} (UNPARSED): {data}")


def run_server(host='0.0.0.0', port=514):
    try:
        server = socketserver.UDPServer((host, port), SyslogUDPHandler)
        logging.info(f"Starting syslog server on {host}:{port}")
        logging.info("Waiting for messages... (Press Ctrl+C to stop)")
        server.serve_forever()

    except PermissionError:
        logging.error("Error: Port 514 requires root privileges. Try running with sudo or use a port > 1024")
    except KeyboardInterrupt:
        logging.info("\nShutting down syslog server")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Error: {e}")


if __name__ == "__main__":
    CONFIG = json.load(open(sys.argv[1]))
    if socket.gethostname() != SYSLOG_HOST and SYSLOG_HOST != socket.gethostname().split(".")[0]:
        raise Exception(
            f"SYSLOG_HOST ({SYSLOG_HOST}) does not match the host running the script ({socket.gethostname()})")
    run_server(port=SYSLOG_PORT)
