import os
import datetime
import base64
import logging
import json
import boto3
from botocore.vendored import requests
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import parse_qs

# Requirements
try:
    import unzip_requirements
except ImportError:
    pass

import paramiko
from OpenSSL.crypto import verify, load_publickey, FILETYPE_PEM, X509
from OpenSSL.crypto import Error as SignatureError

# logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# AWS
s3 = boto3.client('s3')
ssm = boto3.client('ssm')

# Make sure you use the correct config URL, the .org and .com
# have different keys!
# https://api.travis-ci.org/config
# https://api.travis-ci.com/config
TRAVIS_CONFIG_URL = 'https://api.travis-ci.org/config'


def get_secret(key):
    resp = ssm.get_parameter(Name=key, WithDecryption=True)
    return resp['Parameter']['Value']


def respond(err, res=None):
    return {
        'statusCode': '400' if err else '200',
        'body': err.args[0] if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
        }
    }


def run(event, context):
    current_time = datetime.datetime.now().time()
    name = context.function_name
    logger.info('Your function %s ran at %s', name, str(current_time))


def api(event, context):
    current_time = datetime.datetime.now().time()
    name = context.function_name
    logger.info('Your function %s ran at %s', name, str(current_time))

    return respond(None, {'status': 'OK'})


def slack(event, context):
    """
    Slack Slash Commands
    """

    current_time = datetime.datetime.now().time()
    name = context.function_name
    logger.info('Your function %s ran at %s', name, str(current_time))

    params = parse_qs(event['body'])
    token = params['token'][0]

    if token != get_secret('/vbot/SlackVerificationToken'):
        logger.error("Request token (%s) does not match expected", token)
        return respond(None, {'text': 'Invalid request token :cry:'})

    user = params['user_id'][0]
    command = params['command'][0]
    channel = params['channel_name'][0]
    response_url = params['response_url'][0]

    if 'text' in params:
        command_text = params['text'][0]
    else:
        command_text = ''

    def verify_allowed(users):
        """
        Allowed users list (comma separated; white space ignored)
        """
        if user not in [allowed.strip() for allowed in users.split(',')]:
            logger.warn('Unauthorized user <@%s> tried to run command "%s" on channel #%s with the following text "%s"', user, command, channel, command_text)
            return respond(None, {'text': 'You are not on the allowed user list :cry:'})
        else:
            logger.info('Authorized user <@%s> invoked command "%s" on channel #%s with the following text "%s"', user, command, channel, command_text)

    if command == '/vbot':
        if command_text == 'deploy r10k':
            # Only allow Vlad (U0474LR06)
            verify_allowed('U0474LR06')
            deploy_r10k()
            return respond(None, {'text': 'R10K deploying in the background :thumbsup:'})
        else:
            logger.warn('Unknown Subcommand')
            return respond(None, {'text': 'Unknown Subcommand "%s" :cry:' % (command_text)})
    else:
        logger.warn('Unknown command')
        return respond(None, {'text': 'Unknown command "%s" :cry:' % (command)})

    return respond(None, {'text': 'Event ignored :cry:'})


def post_to_slack(hook_url, slack_message):
    """
    Ex: post_to_slack(response_url, {'text': 'Unknown command :cry:'})
    """
    req = Request(hook_url, json.dumps(slack_message).encode('utf-8'))
    try:
        response = urlopen(req)
        response.read()
        logger.info('Response posted')
    except HTTPError as e:
        logger.error("Request failed: %d %s", e.code, e.reason)
    except URLError as e:
        logger.error("Server connection failed: %s", e.reason)


def travis(event, context):
    """
    TravisCI Requests
    Thanks to https://gist.github.com/andrewgross/8ba32af80ecccb894b82774782e7dcd4
    """
    signature = get_travis_signature(event)
    json_payload = parse_qs(event['body'])['payload'][0]

    try:
        public_key = get_travis_public_key()
    except requests.Timeout:
        logger.error({'message': 'Timed out when attempting to retrieve Travis CI public key'})
        return respond(Exception('Timed out when attempting to retrieve Travis CI public key'))
    except requests.RequestException as e:
        logger.error({'message': 'Failed to retrieve Travis CI public key', 'error': e.message})
        return respond(Exception('Failed to retrieve Travis CI public key'))
    try:
        check_travis_authorized(signature, public_key, json_payload)
    except SignatureError:
        return respond(Exception('Unauthorized'))

    json_data = json.loads(json_payload)
    build_number = json_data['number']
    branch = json_data['branch']
    repo_name = json_data['repository']['name']
    owner_name = json_data['repository']['owner_name']

    logger.info('Authorized request received from TravisCI build #%s for the %s branch of repository %s/%s', build_number, branch, owner_name, repo_name)

    if owner_name == 'vghn' and repo_name == 'puppet':
        deploy_r10k()
    else:
        logger.warn('Event ignored')


def check_travis_authorized(signature, public_key, payload):
    """
    Convert the PEM encoded public key to a format palatable for pyOpenSSL,
    then verify the signature
    """
    pkey_public_key = load_publickey(FILETYPE_PEM, public_key)
    certificate = X509()
    certificate.set_pubkey(pkey_public_key)
    verify(certificate, signature, payload, str('sha1'))


def get_travis_signature(request):
    """
    Extract the raw bytes of the request signature provided by travis
    """
    signature = request['headers']['Signature']
    return base64.b64decode(signature)


def get_travis_public_key():
    """
    Returns the PEM encoded public key from the Travis CI /config endpoint
    """
    response = requests.get(TRAVIS_CONFIG_URL, timeout=5)
    response.raise_for_status()
    return response.json()['config']['notifications']['webhook']['public_key']


def deploy_r10k():
    """
    Run remote r10k deploy command
    """
    host = 'rhea.ghn.me'
    user = 'ubuntu'

    # Download private key file from secure S3 bucket
    s3.download_file(
        os.environ['SECRETS_BUCKET'],
        'deploy.rsa',
        '/tmp/deploy.rsa'
        )

    # Establish SSH connection
    key = paramiko.RSAKey.from_private_key_file('/tmp/deploy.rsa')
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    logger.info('Connect to ' + host)
    ssh.connect(host, username=user, pkey=key)

    # Run SSH commands
    ssh_commands = [
        'docker exec $(docker ps --quiet --latest --filter "label=r10k") r10k deploy environment --puppetfile'
        ]
    for ssh_command in ssh_commands:
        logger.info("Execute '{}' in the background".format(ssh_command + ' >/dev/null 2>&1 &'))
        stdin, stdout, stderr = ssh.exec_command(ssh_command)
    ssh.close()