# Discord Fashion Bot

This is the codebase for a Discord bot that is meant to respond to user's requests to display runways dependent on designer and collections. The bot parses Vogue 
runway collections in order to grab and post the images.

# Motivation

I made this bot without the intention of using it as a serious or commercial bot, so it's entirely for personal use - I wanted to learn the ropes to BeautifulSoup/requests APIs, as well as AWS backend support and then transfer this knowledge to other similar projects and create other interactive bots that communities on Discord could use, but Vogue was definitely a website that I was looking at to start because of its easily structured website and my interest in fashion.

# Future Work

In the future I intend to expand upon this bot by adding more interactive features and foolproofing. 

- Foolproofing the reactions to ensure that if a user is adding specific reactions to non-bot messages that the bot interacts with that the bot won't attempt to parse a message that isn't theirs (Doesn't break the bot but does cause console to log an error message while looking for data from one of its own messages.)
- Determine if it's possible to send an embed with hidden metadata that allows for the embeds themselves to not carry every single piece of information on the card to parse later on
