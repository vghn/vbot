import base64
import logging
import json
import boto3
from botocore.vendored import requests
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import parse_qs

# serverless-python-requirements plugin to install requirements
try:
    import unzip_requirements # NOQA
except ImportError:
    pass

# Import requirements not present on AWS Lambda
from OpenSSL.crypto import verify, load_publickey, FILETYPE_PEM, X509
from OpenSSL.crypto import Error as SignatureError

# logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# AWS
s3 = boto3.client('s3')
ssm = boto3.client('ssm')


def get_secret(key):
    """
    Retrieve AWS SSM Parameter (decrypted if necessary)
    Ex: get_secret('/path/to/service/myParam')
    """
    response = ssm.get_parameter(Name=key, WithDecryption=True)
    return response['Parameter']['Value']


def respond(err, res=None):
    """
    Return an JSON formatted AWS API Gateway response
    """
    return {
        'statusCode': '400' if err else '200',
        'body': err.args[0] if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
        }
    }


def slack(event, context):
    """
    Slack Endpoint Processor
    """

    # Skip scheduled events (they are just warming up the fucntion)
    if 'detail-type' in event and event['detail-type'] == 'Scheduled Event':
        return

    return respond(None, process_slack(parse_qs(event['body'])))


def travis(event, context):
    """
    TravisCI Endpoint
    """

    # Skip scheduled events (they are just warming up the fucntion)
    if 'detail-type' in event and event['detail-type'] == 'Scheduled Event':
        return

    return process_travis(event)


def process_slack(params):
    """
    Slack Requests Processor
    """

    token = params['token'][0]

    if token != get_secret('/vbot/SlackVerificationToken'):
        logger.error("Request token (%s) does not match expected", token)
        return {'text': 'Invalid request token :cry:'}

    user = params['user_id'][0]
    command = params['command'][0]
    channel = params['channel_name'][0]
    response_url = params['response_url'][0] # NOQA

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
            return {'text': 'You are not on the allowed user list :cry:'}
        else:
            logger.info('Authorized user <@%s> invoked command "%s" on channel #%s with the following text "%s"', user, command, channel, command_text)

    if command == '/vbot':
        if command_text == 'deploy r10k':
            # Only allow Vlad (U0474LR06)
            verify_allowed('U0474LR06')

            return {'text': 'No longer implemented :thumbsdown:'}
        elif command_text == 'help':
            return {
                'text': '*USAGE*',
                'attachments': [
                    {
                        'title': 'help',
                        'text': 'Shows this'
                    },
                    {
                        'title': 'deploy r10k',
                        'text': 'Deploys Puppet Master changes via SSH (No longer implemented)'
                    }
                ]
            }
        else:
            logger.warn('Unknown action')
            return {'text': 'Unknown action "%s" :cry:; try "/vbot help"' % (command_text)}
    else:
        logger.warn('Unknown command')
        return {'text': 'Unknown command "%s" :cry:' % (command)}

    return {'text': 'Event ignored :cry:'}


def process_travis(request):
    """
    Process TravisCI Requests
    Thanks to https://gist.github.com/andrewgross/8ba32af80ecccb894b82774782e7dcd4
    """
    signature = get_travis_signature(request)
    json_payload = parse_qs(request['body'])['payload'][0]
    json_data = json.loads(json_payload)

    build_number = json_data['number']
    build_url = json_data['build_url']
    state = json_data['state']
    branch = json_data['branch']
    repo_name = json_data['repository']['name']
    owner_name = json_data['repository']['owner_name']

    try:
        public_key = get_travis_public_key(build_url)
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

    logger.info('Authorized request received from TravisCI build #%s for the %s branch of repository %s/%s', build_number, branch, owner_name, repo_name)

    if owner_name == 'vghn' and repo_name == 'puppet' and state == 'passed':
        logger.warn('No longer implemented')
    else:
        logger.warn('Event ignored')

    return respond(None, {'status': 'OK'})


def post_to_slack(message):
    """
    Ex: post_to_slack({'text': 'Unknown command :cry:'})
    """
    hook_url = get_secret('SlackAlertsHookURL')
    request = Request(hook_url, json.dumps(message).encode('utf-8'))
    try:
        response = urlopen(request)
        response.read()
        logger.info('Response posted to Slack channel')
    except HTTPError as e:
        logger.error("Request failed: %d %s", e.code, e.reason)
    except URLError as e:
        logger.error("Server connection failed: %s", e.reason)


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


def get_travis_public_key(build_url):
    """
    Returns the PEM encoded public key from the Travis CI /config endpoint
    """

    # Make sure you use the correct config URL, the .org and .com
    # have different keys!
    if build_url.startswith('https://travis-ci.com'):
        travis_config_url = 'https://api.travis-ci.com/config'
    elif build_url.startswith('https://travis-ci.org'):
        travis_config_url = 'https://api.travis-ci.org/config'
    else:
        logger.warn('The build url is unknown')

    response = requests.get(travis_config_url, timeout=5)
    response.raise_for_status()
    return response.json()['config']['notifications']['webhook']['public_key']
