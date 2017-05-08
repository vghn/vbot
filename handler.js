'use strict';

// Include the serverless-slack bot framework
const slack = require('serverless-slack');

// The function that AWS Lambda will call
exports.slackListener = slack.handler.bind(slack);

// Slash Command handler (https://api.slack.com/slash-commands)
slack.on('/vbot', (msg, bot) => {
  let userName = msg.user_name
  let messageText = msg.text

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
  };

  switch (messageText) {
    case 'hi':
      bot.replyPrivate({
        "text": `Hello ${userName}! How would you like to greet the channel?`,
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
      });
      break;
    default:
      bot.replyPrivate(usage);
  }
});

// Interactive Message handler
slack.on('greetings_click', (msg, bot) => {
  bot.reply({
    "text": msg.actions[0].value
  });
});

// Reaction Added event handler
slack.on('reaction_added', (msg, bot) => {
  bot.reply({
    "text": ":wave:"
  });
});
