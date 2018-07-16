Makes the first 2 users to join a voice channel\* the channel's "owners" that can limit its user count, if the room was limited in the first place.
When an owner leaves, the person who joined after them replaces them as owner.
When all users leave the room, it will automatically be unlocked.

Commands:

## !lock
#### Limits the channel to the number of users currently in the channel (or 2 if the user is alone).

## !lock 5
#### Limits the channel to 5 users (or the original limit if it's under 5).

## !unlock
#### Resets the channel to its original user limit.

## !checkowner
#### Check who the owners of the channel are.

# Bot Owner Only
## !close | !shutdown | !kill
#### Closes the bot gracefully, unlocking any channels that may be locked by users.

\* If the bot is started with users already in voice channels, the first 2 users listed will become the owners.