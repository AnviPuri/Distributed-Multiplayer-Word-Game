class ServerDetail:

    def __init__(self, ip, port, server_id, is_primary, is_responding=True):
        self.ip = ip
        self.port = port
        self.id = server_id
        self.is_primary = is_primary
        self.is_responding = is_responding

    def set_is_primary(self, is_primary):
        self.is_primary = is_primary

