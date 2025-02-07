def create_client(client_data):
    from client_details import ClientDetail
    client = ClientDetail(client_data["ip"], client_data["port"])
    client.set_client_score(client_data["client_score"])
    client.set_has_guessed_word(client_data["has_guessed_word"])
    client.set_last_played_word(client_data["last_played_word"])
    client.set_last_word_interpretation(client_data["last_word_interpretation"])
    client.set_can_play_round(client_data["can_play_the_round"])
    return client


class GameStateManager:
    def __init__(self):
        self.current_game_word = None
        self.game_round = 0
        self.game_ended = False
        self.connected_clients = []

    def set_game_details(self, game_round, game_ended, current_game_word, connected_clients):
        self.game_round = game_round
        self.game_ended = game_ended
        self.current_game_word = current_game_word
        self.connected_clients.clear()
        for client_data in connected_clients:
            self.connected_clients.append(create_client(client_data))
