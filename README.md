# Distributed-Multiplayer-Word-Game

* start the game as soon as we have more than 1 client
* the game will have 5 rounds. In case the word is guessed before those 5 rounds, the game ends and winner is declared
* in every round fifo ordering is done
* the clients are asked one by one to guess the word and their result is calculated amd sent back to the client
* at any point if the correct word is guessed , the game ends and the result is shared with all clients
* each client also has can_play_this_round value which tells if it will be a part of this round
* for every correct letter and placement - +1

* once the game ends, a new game is started after a minute