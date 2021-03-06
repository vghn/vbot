# VBot

  [![Build Status](https://travis-ci.org/vghn/vbot.svg?branch=master)](https://travis-ci.org/vghn/vbot)

## Development status

This project is still in a prototype development stage.

## Overview

VBot Slack App

Initially a NodeJS app based on <https://github.com/johnagan/serverless-slack-app>

Refactored later in Python on AWS Lambda with AWS API Gateway based on <https://medium.com/devoops-and-universe/serverless-slack-bot-on-aws-vs-azure-getting-notified-instantly-ab0916393e1d> for some of the Slack code and <https://gist.github.com/andrewgross/8ba32af80ecccb894b82774782e7dcd4> for the Travis webhook

## Requirements

- AWS credentials present in `.aws` (for a user with "AdministratorAccess" policy)
- SSM Parameters:
  - `/vbot/SlackVerificationToken` (secure string), used to verify slack requests
  - `/vbot/SlackAlertsHookURL` (secure string), used for slack posting in #alerts

## Commands

- `bin/vbot help` - Shows help
- `bin/vbot deploy` - Deploys new version
- `bin/vbot deploy function_name` - Deploys new version of a single function

The GET URL is used in <https://api.slack.com/apps> - VBot - Interactive messages, Slash Commands and OAuth & Permissions.
The App needs to be installed by going to OAuth & Permissions - Install app to team

## Contribute

See [CONTRIBUTING.md](CONTRIBUTING.md) file.

## License

Licensed under the Apache License, Version 2.0.
See [LICENSE](LICENSE) file.
