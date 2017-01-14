'use strict';

// Include the serverless-slack bot framework
const slack = require('serverless-slack');
// Include AWS SDK
const AWS = require('aws-sdk');
const s3 = new AWS.S3();

// VARs
// const s3Bucket = this.serverless.variables.service.custom.s3Bucket;
// const sshKey = this.serverless.variables.service.custom.sshKey;
const s3Bucket = 'vladgh';
const sshKey = 'secure/production/keys/deploy';

// The function that AWS Lambda will call
exports.slackListener = slack.handler.bind(slack);

// Slash Command handler (https://api.slack.com/slash-commands)
slack.on('/vbot', (msg, bot) => {
  let usage = {
    "attachments": [{
      "title": "USAGE:",
      "title_link": "https://github.com/vghn/vbot/blob/master/README.md",
      "color": "#36a64f",
      "fields": [{
        "title": "/vbot hi",
        "value": "Choose how to say hi to the channel",
        "short": false
      }]
    }]
  }

  let message = {
    "text": "Hello " + msg.user_name + "! How would you like to greet the channel?",
    "attachments": [{
      "fallback": "actions",
      "callback_id": "greetings_click",
      "actions": [
        { "type": "button", "name": "Wave", "text": ":wave:", "value": ":wave:" },
        { "type": "button", "name": "Hello", "text": "Hello", "value": "Hello" },
        { "type": "button", "name": "Howdy", "text": "Howdy", "value": "Howdy" },
        { "type": "button", "name": "Hiya", "text": "Hiya", "value": "Hiya" }
      ]
    }]
  };

  switch (msg.text) {
    case 'hi':
      bot.replyPrivate(message);
      break;
    case 'ssh':
      bot.replyPrivate(getSSHKey);
      break;
    default:
      bot.replyPrivate(usage);
  }
});

// Interactive Message handler
slack.on('greetings_click', (msg, bot) => {
  bot.reply({
    text: msg.actions[0].value
  });
});

// Reaction Added event handler
slack.on('reaction_added', (msg, bot) => {
  bot.reply({
    text: ':wave:'
  });
});


function getSSHKey(){
  let params = {
    Bucket: s3Bucket,
    Key: sshKey
  };
  let key = s3.getObject(params, function(err, data) {
    if (err) console.log(err, err.stack); // an error occurred
    else     console.log(data);           // successful response
  });
  return key.Body
};
