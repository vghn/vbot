'use strict';

// Include the serverless-slack bot framework
const slack = require('serverless-slack');

// The function that AWS Lambda will call
exports.handler = slack.handler.bind(slack);

// Slash Command handler (https://api.slack.com/slash-commands)
slack.on('/vbot', (msg, bot) => {
  let message = {
    text: "Hello " + msg.user_name + "! How would you like to greet the channel?",
    attachments: [{
      fallback: 'actions',
      callback_id: "greetings_click",
      actions: [
        { type: "button", name: "Wave", text: ":wave:", value: ":wave:" },
        { type: "button", name: "Hello", text: "Hello", value: "Hello" },
        { type: "button", name: "Howdy", text: "Howdy", value: "Howdy" },
        { type: "button", name: "Hiya", text: "Hiya", value: "Hiya" }
      ]
    }]
  };

  switch (msg.text) {
    case 'hi':
      bot.replyPrivate(message);
      break;
    default:
      bot.replyPrivate({
        text: 'Unknown command!',
        attachments: [{
          title: "Hi",
          text: "Choose how to say hi to the channel"
        }]
      });
  }
});

// Interactive Message handler
slack.on('greetings_click', (msg, bot) => {
  let message = {
    // selected button value
    text: msg.actions[0].value
  };

  // public reply
  bot.reply(message);
});

// Reaction Added event handler
slack.on('reaction_added', (msg, bot) => {
  bot.reply({
    text: ':wave:'
  });
});
