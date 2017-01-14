'use strict';

// Include the serverless-slack bot framework
const slack = require('serverless-slack');

// The function that AWS Lambda will call
exports.slackListener = slack.handler.bind(slack);

var usage = {
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
};

var greetMessage = {
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

// Slash Command handler (https://api.slack.com/slash-commands)
slack.on('/vbot', (msg, bot) => {
  switch (msg.text) {
    case 'hi':
      bot.replyPrivate(greetMessage);
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
